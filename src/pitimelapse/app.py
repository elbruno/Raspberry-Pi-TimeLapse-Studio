"""
app.py - Flask Web Application for PiTimeLapse Lab

This file creates the web interface where you can:
- See the current status (running/stopped)
- Start and stop time-lapses
- View and edit settings
- Browse captured images

Flask is a simple web framework that makes it easy to build
web applications in Python.
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    send_file,
    redirect,
    url_for,
    flash,
)

from .config import AppConfig, load_config, save_config
from .storage import StorageManager
from .capture import CaptureScheduler
from .models import Status

# Set up logging
logger = logging.getLogger(__name__)

# Create Flask app
# __name__ tells Flask where to look for templates and static files
app = Flask(
    __name__,
    template_folder="../../templates",  # Path to HTML templates
    static_folder="../../static",        # Path to CSS/JS files
)

# Secret key for session management (used for flash messages)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "pitimelapse-secret-key-change-me")

# Global objects (initialized when app starts)
config: Optional[AppConfig] = None
storage: Optional[StorageManager] = None
scheduler: Optional[CaptureScheduler] = None


def init_app(app_config: AppConfig) -> None:
    """
    Initialize the application with configuration.
    
    This function is called when the app starts to set up:
    - Storage manager
    - Capture scheduler
    
    Args:
        app_config: The loaded configuration
    """
    global config, storage, scheduler
    
    config = app_config
    storage = StorageManager(config.output_dir)
    scheduler = CaptureScheduler(config, storage)
    
    logger.info("Application initialized")


# =============================================================================
# WEB ROUTES - These serve HTML pages
# =============================================================================

@app.route("/")
def index():
    """
    Home page - shows current status and control buttons.
    
    This is the main dashboard where you can see if a time-lapse
    is running and start/stop it.
    """
    status = scheduler.get_status() if scheduler else Status()
    session = scheduler.get_current_session() if scheduler else None
    
    return render_template(
        "index.html",
        status=status,
        session=session,
        config=config,
    )


@app.route("/gallery")
def gallery():
    """
    Gallery page - shows captured images.
    
    Displays thumbnails of recent images from the current or
    most recent session.
    """
    if not storage:
        return render_template("gallery.html", images=[], sessions=[])
    
    sessions = storage.list_sessions()
    
    # Get session_id from query string, or use most recent
    session_id = request.args.get("session")
    
    if not session_id and sessions:
        session_id = sessions[0].id
    
    images = []
    current_session = None
    
    if session_id:
        # Find the selected session
        for s in sessions:
            if s.id == session_id:
                current_session = s
                break
        
        if current_session:
            session_folder = current_session.output_folder
            images = storage.get_latest_images(session_folder, count=50)
    
    return render_template(
        "gallery.html",
        images=images,
        sessions=sessions,
        current_session=current_session,
        selected_session_id=session_id,
    )


@app.route("/settings")
def settings():
    """
    Settings page - view and edit configuration.
    
    Shows all the current settings and allows you to change them.
    """
    return render_template(
        "settings.html",
        config=config,
        is_running=scheduler.get_status().is_running if scheduler else False,
    )


@app.route("/settings/save", methods=["POST"])
def save_settings():
    """
    Handle settings form submission.
    
    Validates the new settings and saves them to config.yaml.
    """
    global config, storage, scheduler
    
    if scheduler and scheduler.get_status().is_running:
        flash("Cannot change settings while time-lapse is running. Stop it first.", "error")
        return redirect(url_for("settings"))
    
    try:
        # Create new config from form data
        new_config = AppConfig(
            camera_mode=request.form.get("camera_mode", "opencv"),
            camera_index=int(request.form.get("camera_index", 0)),
            resolution_width=int(request.form.get("resolution_width", 1280)),
            resolution_height=int(request.form.get("resolution_height", 720)),
            interval_seconds=int(request.form.get("interval_seconds", 10)),
            start_delay_seconds=int(request.form.get("start_delay_seconds", 0)),
            duration_limit_seconds=int(request.form.get("duration_limit_seconds", 0)),
            output_dir=request.form.get("output_dir", "./data"),
            image_format=request.form.get("image_format", "jpg"),
            overlay_timestamp="overlay_timestamp" in request.form,
            web_host=request.form.get("web_host", "0.0.0.0"),
            web_port=int(request.form.get("web_port", 8000)),
            retention_days=int(request.form.get("retention_days", 0)),
            max_storage_mb=int(request.form.get("max_storage_mb", 0)),
            log_level=request.form.get("log_level", "INFO"),
        )
        
        # Validate the new config
        errors = new_config.validate()
        if errors:
            for error in errors:
                flash(f"Validation error: {error}", "error")
            return redirect(url_for("settings"))
        
        # Save to file
        if save_config(new_config):
            config = new_config
            
            # Re-initialize storage if output_dir changed
            storage = StorageManager(config.output_dir)
            scheduler = CaptureScheduler(config, storage)
            
            flash("Settings saved successfully!", "success")
        else:
            flash("Failed to save settings. Check the logs.", "error")
            
    except ValueError as e:
        flash(f"Invalid value: {e}", "error")
    except Exception as e:
        flash(f"Error saving settings: {e}", "error")
        logger.exception("Error saving settings")
    
    return redirect(url_for("settings"))


@app.route("/image/<session_id>/<filename>")
def serve_image(session_id: str, filename: str):
    """
    Serve an image file.
    
    This route allows the gallery to display images.
    Resolves session folder from metadata to handle output_dir changes.
    """
    if not config or not storage:
        return "Not configured", 500
    
    # First try to find session in storage metadata (handles output_dir changes)
    sessions = storage.list_sessions()
    session_folder = None
    for s in sessions:
        if s.id == session_id:
            session_folder = s.output_folder
            break
    
    # Fallback to current config output_dir if session not found in metadata
    if not session_folder:
        session_folder = str(Path(config.output_dir) / session_id)
    
    image_path = Path(session_folder) / filename
    
    # Validate path is within session folder (prevent directory traversal)
    try:
        image_path = image_path.resolve()
        session_path = Path(session_folder).resolve()
        if not str(image_path).startswith(str(session_path)):
            logger.warning(f"Directory traversal attempt: {filename}")
            return "Invalid path", 400
    except Exception as e:
        logger.error(f"Path resolution error: {e}")
        return "Invalid path", 400
    
    if not image_path.exists():
        logger.warning(f"Image not found: {image_path}")
        return "Image not found", 404
    
    return send_file(str(image_path))


@app.route("/download/<session_id>")
def download_session(session_id: str):
    """
    Download a session as a ZIP file.
    
    Creates a ZIP archive of all images in the session.
    Resolves session folder from metadata to handle output_dir changes.
    """
    if not storage:
        return "Storage not available", 500
    
    # Find session folder from metadata
    sessions = storage.list_sessions()
    session_folder = None
    for s in sessions:
        if s.id == session_id:
            session_folder = s.output_folder
            break
    
    if not session_folder or not Path(session_folder).exists():
        flash("Session folder not found", "error")
        return redirect(url_for("gallery"))
    
    zip_path = storage.create_session_zip(session_id, session_folder)
    
    if not zip_path:
        flash("Failed to create ZIP file", "error")
        return redirect(url_for("gallery"))
    
    return send_file(
        zip_path,
        as_attachment=True,
        download_name=f"{session_id}.zip",
    )


@app.route("/delete/<session_id>", methods=["POST"])
def delete_session_route(session_id: str):
    """
    Delete a session and all its images.
    
    Requires POST request to prevent accidental deletion.
    """
    if not storage:
        return jsonify({"success": False, "message": "Storage not available"}), 500
    
    # Check if this session is currently active
    if scheduler and scheduler.get_status().is_running:
        current_session = scheduler.get_current_session()
        if current_session and current_session.id == session_id:
            return jsonify({"success": False, "message": "Cannot delete active session. Stop the time-lapse first."}), 400
    
    # Delete the session
    success = storage.delete_session(session_id)
    
    if success:
        return jsonify({"success": True, "message": f"Session {session_id} deleted successfully"})
    else:
        return jsonify({"success": False, "message": "Failed to delete session"}), 500


# =============================================================================
# API ROUTES - These return JSON data
# =============================================================================

@app.route("/api/status")
def api_status():
    """
    GET /api/status
    
    Returns the current application status as JSON.
    
    Response:
        {
            "is_running": true/false,
            "current_session_id": "session_xxx" or null,
            "last_capture_time": "2024-01-15T14:30:22" or null,
            "next_capture_time": "2024-01-15T14:30:32" or null,
            "total_photos": 42,
            "total_errors": 0,
            "last_error": null,
            "camera_mode": "opencv",
            "camera_available": true
        }
    """
    status = scheduler.get_status() if scheduler else Status()
    return jsonify(status.to_dict())


@app.route("/api/start", methods=["POST"])
def api_start():
    """
    POST /api/start
    
    Start a new time-lapse session.
    
    Response:
        {
            "success": true/false,
            "message": "Time-lapse started! Session ID: session_xxx"
        }
    """
    if not scheduler:
        return jsonify({"success": False, "message": "Scheduler not initialized"})
    
    success, message = scheduler.start()
    return jsonify({"success": success, "message": message})


@app.route("/api/stop", methods=["POST"])
def api_stop():
    """
    POST /api/stop
    
    Stop the current time-lapse session.
    
    Response:
        {
            "success": true/false,
            "message": "Time-lapse stopped. Captured 42 photos."
        }
    """
    if not scheduler:
        return jsonify({"success": False, "message": "Scheduler not initialized"})
    
    success, message = scheduler.stop()
    return jsonify({"success": success, "message": message})


@app.route("/api/sessions")
def api_sessions():
    """
    GET /api/sessions
    
    List all sessions.
    
    Response:
        {
            "sessions": [
                {
                    "id": "session_20240115_143022",
                    "start_time": "2024-01-15T14:30:22",
                    ...
                },
                ...
            ]
        }
    """
    if not storage:
        return jsonify({"sessions": []})
    
    sessions = storage.list_sessions()
    return jsonify({"sessions": [s.to_dict() for s in sessions]})


@app.route("/api/sessions/<session_id>")
def api_session_detail(session_id: str):
    """
    GET /api/sessions/<session_id>
    
    Get details of a specific session.
    
    Response:
        {
            "session": { ... } or null
        }
    """
    if not storage or not config:
        return jsonify({"session": None})
    
    session_folder = Path(config.output_dir) / session_id
    session = storage.load_session_metadata(str(session_folder))
    
    if session:
        return jsonify({"session": session.to_dict()})
    else:
        return jsonify({"session": None}), 404


@app.route("/api/sessions/<session_id>/latest-images")
def api_latest_images(session_id: str):
    """
    GET /api/sessions/<session_id>/latest-images
    
    Get the most recent images from a session.
    
    Query params:
        count: Number of images to return (default: 10)
    
    Response:
        {
            "images": [
                {"path": "...", "name": "...", "size": 12345},
                ...
            ]
        }
    """
    if not storage or not config:
        return jsonify({"images": []})
    
    count = request.args.get("count", 10, type=int)
    session_folder = Path(config.output_dir) / session_id
    
    images = storage.get_latest_images(str(session_folder), count=count)
    
    # Modify paths to use the serve_image route
    for img in images:
        img["url"] = url_for("serve_image", session_id=session_id, filename=img["name"])
    
    return jsonify({"images": images})


@app.route("/api/config")
def api_config():
    """
    GET /api/config
    
    Get the current configuration.
    
    Response:
        { config object }
    """
    if not config:
        return jsonify({})
    return jsonify(config.to_dict())


@app.route("/api/storage")
def api_storage():
    """
    GET /api/storage
    
    Get storage usage information.
    
    Response:
        {
            "used_mb": 150.5,
            "max_mb": 1000,
            "session_count": 5
        }
    """
    if not storage:
        return jsonify({"used_mb": 0, "max_mb": 0, "session_count": 0})
    
    used_mb = storage.get_storage_usage_mb()
    sessions = storage.list_sessions()
    
    return jsonify({
        "used_mb": round(used_mb, 2),
        "max_mb": config.max_storage_mb if config else 0,
        "session_count": len(sessions),
    })


@app.route("/api/latest-frame")
def api_latest_frame():
    """
    GET /api/latest-frame
    
    Returns the latest captured frame as JPEG image.
    Used for live preview on the dashboard.
    
    Response:
        - JPEG image bytes with Content-Type: image/jpeg
        - 404 if no frame captured yet
    """
    if not scheduler:
        return "Scheduler not initialized", 500
    
    frame_bytes = scheduler.get_latest_frame()
    if not frame_bytes:
        return "No frame captured yet", 404
    
    from flask import Response
    return Response(frame_bytes, mimetype='image/jpeg')


@app.route("/api/test-camera")
def api_test_camera():
    """
    GET /api/test-camera
    
    Captures a single test frame from the camera.
    Used for camera preview on the settings page.
    
    Response:
        - JPEG image bytes with Content-Type: image/jpeg
        - 500 with error message if camera unavailable
    """
    if not config:
        return jsonify({"error": "Not configured"}), 500
    
    # Check if time-lapse is running - don't interfere with active capture
    if scheduler and scheduler.get_status().is_running:
        # Return latest frame from active session if available
        frame_bytes = scheduler.get_latest_frame()
        if frame_bytes:
            from flask import Response
            return Response(frame_bytes, mimetype='image/jpeg')
        return jsonify({"error": "Camera in use by active time-lapse"}), 409
    
    try:
        # Open camera temporarily
        if config.camera_mode == "picamera2":
            from .camera_picamera2 import PiCamera2Camera
            camera = PiCamera2Camera()
        else:
            from .camera_opencv import OpenCVCamera
            camera = OpenCVCamera(camera_index=config.camera_index)
        
        if not camera.is_available():
            return jsonify({"error": f"Camera library not available for mode: {config.camera_mode}"}), 500
        
        if not camera.open(config.resolution_width, config.resolution_height):
            return jsonify({"error": "Could not open camera"}), 500
        
        try:
            # Capture a frame
            frame = camera.capture()
            if frame is None:
                return jsonify({"error": "Failed to capture frame"}), 500
            
            # Encode as JPEG
            try:
                import cv2
                _, jpeg_bytes = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                from flask import Response
                return Response(jpeg_bytes.tobytes(), mimetype='image/jpeg')
            except ImportError:
                return jsonify({"error": "OpenCV not available for encoding"}), 500
        finally:
            camera.close()
            
    except Exception as e:
        logger.exception("Error testing camera")
        return jsonify({"error": str(e)}), 500


# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    if request.path.startswith("/api/"):
        return jsonify({"error": "Not found"}), 404
    return render_template("error.html", error="Page not found"), 404


@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors."""
    logger.exception("Server error")
    if request.path.startswith("/api/"):
        return jsonify({"error": "Server error"}), 500
    return render_template("error.html", error="Server error"), 500


def run_server(host: str = "0.0.0.0", port: int = 8000, debug: bool = False) -> None:
    """
    Start the Flask development server.
    
    Args:
        host: IP address to listen on
        port: Port number
        debug: Enable debug mode (auto-reload on code changes)
    """
    # Use threaded mode to handle multiple requests
    app.run(host=host, port=port, debug=debug, threaded=True)
