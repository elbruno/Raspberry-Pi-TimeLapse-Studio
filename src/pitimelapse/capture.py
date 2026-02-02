"""
capture.py - Time-lapse Capture Scheduler

This file contains the CaptureScheduler class which:
- Runs in a background thread
- Takes photos at regular intervals
- Saves them to the session folder
- Tracks progress and errors
- Handles camera failures gracefully

The scheduler is the "heart" of the time-lapse system.
"""

import os
import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Optional, Callable
from pathlib import Path

from .models import Session, Status
from .config import AppConfig
from .storage import StorageManager
from .overlay import add_timestamp_overlay
from .utils import generate_session_id, generate_image_filename, get_folder_size_mb

# Try to import camera modules
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    cv2 = None

# Set up logging
logger = logging.getLogger(__name__)


class CaptureScheduler:
    """
    Manages the time-lapse capture loop in a background thread.
    
    This class:
    - Starts and stops capture sessions
    - Opens and closes the camera
    - Takes photos at the configured interval
    - Saves images and session metadata
    - Reports status for the web interface
    
    Usage:
        scheduler = CaptureScheduler(config, storage)
        scheduler.start()
        # ... later ...
        scheduler.stop()
    """
    
    def __init__(self, config: AppConfig, storage: StorageManager):
        """
        Initialize the capture scheduler.
        
        Args:
            config: Application configuration
            storage: Storage manager for saving files
        """
        self.config = config
        self.storage = storage
        
        # Current session and status
        self.current_session: Optional[Session] = None
        self.status = Status(
            camera_mode=config.camera_mode,
            camera_available=True,
        )
        
        # Camera object (will be initialized when starting)
        self.camera = None
        
        # Thread control
        self._capture_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        
        # Latest frame cache for live preview
        self._latest_frame: Optional[bytes] = None
        self._latest_frame_lock = threading.Lock()
        
        # Callback for status updates (used by web UI)
        self._status_callback: Optional[Callable[[Status], None]] = None
    
    def set_status_callback(self, callback: Callable[[Status], None]) -> None:
        """
        Set a callback function to be called when status changes.
        
        This is used by the web interface to get updates.
        
        Args:
            callback: Function that takes a Status object
        """
        self._status_callback = callback
    
    def _notify_status_change(self) -> None:
        """Call the status callback if one is registered."""
        if self._status_callback:
            self._status_callback(self.status)
    
    def start(self) -> tuple[bool, str]:
        """
        Start a new time-lapse capture session.
        
        This creates a new session, opens the camera, and starts
        the capture thread.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        with self._lock:
            # Check if already running
            if self.status.is_running:
                return False, "A time-lapse is already running. Stop it first."
            
            # Check storage limit
            if self.config.max_storage_mb > 0:
                current_usage = self.storage.get_storage_usage_mb()
                if current_usage >= self.config.max_storage_mb:
                    return False, (
                        f"Storage limit reached ({current_usage:.1f} MB used). "
                        f"Delete old sessions or increase max_storage_mb."
                    )
            
            # Create a new session
            session_id = generate_session_id()
            session_folder = self.storage.create_session_folder(session_id)
            
            self.current_session = Session(
                id=session_id,
                start_time=datetime.now(),
                interval_seconds=self.config.interval_seconds,
                output_folder=session_folder,
                settings_used=self.config.to_dict(),
            )
            
            # Open the camera
            if not self._open_camera():
                self.current_session = None
                return False, (
                    f"Could not open camera (mode: {self.config.camera_mode}). "
                    "Check the troubleshooting section in the README."
                )
            
            # Update status
            self.status.is_running = True
            self.status.current_session_id = session_id
            self.status.total_photos = 0
            self.status.total_errors = 0
            self.status.last_error = None
            self.status.camera_available = True
            
            # Calculate next capture time
            delay = self.config.start_delay_seconds
            self.status.next_capture_time = datetime.now() + timedelta(seconds=delay)
            
            # Clear stop event and start the capture thread
            self._stop_event.clear()
            self._capture_thread = threading.Thread(
                target=self._capture_loop,
                name="CaptureThread",
                daemon=True,
            )
            self._capture_thread.start()
            
            logger.info(f"Started time-lapse session: {session_id}")
            self._notify_status_change()
            
            return True, f"Time-lapse started! Session ID: {session_id}"
    
    def stop(self) -> tuple[bool, str]:
        """
        Stop the current time-lapse session.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        with self._lock:
            if not self.status.is_running:
                return False, "No time-lapse is currently running."
            
            # Signal the capture thread to stop
            self._stop_event.set()
            
            # Wait for thread to finish (with timeout)
            if self._capture_thread:
                self._capture_thread.join(timeout=5.0)
            
            # Close the camera
            self._close_camera()
            
            # Update session end time
            if self.current_session:
                self.current_session.end_time = datetime.now()
                self.storage.save_session_metadata(self.current_session)
                
                session_id = self.current_session.id
                total_photos = self.current_session.total_photos
                
                self.current_session = None
            else:
                session_id = "unknown"
                total_photos = 0
            
            # Update status
            self.status.is_running = False
            self.status.current_session_id = None
            self.status.next_capture_time = None
            
            logger.info(f"Stopped time-lapse session: {session_id} ({total_photos} photos)")
            self._notify_status_change()
            
            return True, f"Time-lapse stopped. Captured {total_photos} photos."
    
    def get_status(self) -> Status:
        """Get the current status of the scheduler."""
        return self.status
    
    def get_current_session(self) -> Optional[Session]:
        """Get the current session (if running)."""
        return self.current_session
    
    def get_latest_frame(self) -> Optional[bytes]:
        """
        Get the latest captured frame as JPEG bytes.
        
        Returns:
            JPEG bytes of the latest frame, or None if no frame captured yet.
        """
        with self._latest_frame_lock:
            return self._latest_frame
    
    def _open_camera(self) -> bool:
        """
        Open the camera based on config.camera_mode.
        
        Returns:
            True if camera opened successfully
        """
        try:
            if self.config.camera_mode == "picamera2":
                from .camera_picamera2 import PiCamera2Camera
                self.camera = PiCamera2Camera()
            else:
                from .camera_opencv import OpenCVCamera
                self.camera = OpenCVCamera(camera_index=self.config.camera_index)
            
            # Check if the camera library is available
            if not self.camera.is_available():
                logger.error(f"Camera library not available for mode: {self.config.camera_mode}")
                self.status.camera_available = False
                return False
            
            # Open the camera with configured resolution
            success = self.camera.open(
                width=self.config.resolution_width,
                height=self.config.resolution_height,
            )
            
            self.status.camera_available = success
            return success
            
        except Exception as e:
            logger.error(f"Error opening camera: {e}")
            self.status.camera_available = False
            return False
    
    def _close_camera(self) -> None:
        """Close the camera and release resources."""
        if self.camera:
            try:
                self.camera.close()
            except Exception as e:
                logger.warning(f"Error closing camera: {e}")
            self.camera = None
    
    def _capture_loop(self) -> None:
        """
        Main capture loop that runs in a background thread.
        
        This loop:
        1. Waits for the start delay
        2. Captures photos at the configured interval
        3. Saves images and updates session metadata
        4. Stops when signaled or when duration limit is reached
        """
        # Wait for start delay
        delay = self.config.start_delay_seconds
        if delay > 0:
            logger.info(f"Waiting {delay} seconds before first capture...")
            for _ in range(delay):
                if self._stop_event.is_set():
                    return
                time.sleep(1)
        
        # Track start time for duration limit
        loop_start = datetime.now()
        
        while not self._stop_event.is_set():
            # Check duration limit
            if self.config.duration_limit_seconds > 0:
                elapsed = (datetime.now() - loop_start).total_seconds()
                if elapsed >= self.config.duration_limit_seconds:
                    logger.info("Duration limit reached - stopping capture")
                    self._stop_event.set()
                    break
            
            # Check storage limit
            if self.config.max_storage_mb > 0:
                usage = self.storage.get_storage_usage_mb()
                if usage >= self.config.max_storage_mb:
                    error_msg = f"Storage limit reached ({usage:.1f} MB)"
                    logger.warning(error_msg)
                    self._add_error(error_msg)
                    self._stop_event.set()
                    break
            
            # Capture an image
            capture_start = datetime.now()
            self._capture_one_image()
            
            # Update next capture time
            interval = self.config.interval_seconds
            self.status.next_capture_time = capture_start + timedelta(seconds=interval)
            self._notify_status_change()
            
            # Sleep until next capture (checking for stop signal)
            sleep_until = self.status.next_capture_time
            while datetime.now() < sleep_until and not self._stop_event.is_set():
                time.sleep(0.5)  # Check every half second
        
        # Thread is stopping
        logger.info("Capture loop ended")
    
    def _capture_one_image(self) -> bool:
        """
        Capture and save a single image.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.current_session:
            return False
        
        # Try to capture (with retry on failure)
        image = None
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                image = self.camera.capture()
                if image is not None:
                    break
                else:
                    logger.warning(f"Capture attempt {attempt + 1} failed - retrying")
                    time.sleep(1)
            except Exception as e:
                logger.error(f"Capture error on attempt {attempt + 1}: {e}")
                time.sleep(1)
        
        if image is None:
            error_msg = f"Failed to capture image after {max_retries} attempts"
            logger.error(error_msg)
            self._add_error(error_msg)
            return False
        
        # Add timestamp overlay if enabled
        if self.config.overlay_timestamp:
            try:
                image = add_timestamp_overlay(image)
            except Exception as e:
                logger.warning(f"Could not add timestamp overlay: {e}")
        
        # Generate filename and save
        photo_number = self.current_session.total_photos + 1
        filename = generate_image_filename(
            self.current_session.id,
            photo_number,
            self.config.image_format,
        )
        filepath = os.path.join(self.current_session.output_folder, filename)
        
        try:
            if OPENCV_AVAILABLE:
                # Set JPEG quality
                params = [cv2.IMWRITE_JPEG_QUALITY, 95]
                success = cv2.imwrite(filepath, image, params)
            else:
                success = False
            
            if success:
                # Update session counts
                self.current_session.total_photos = photo_number
                self.status.total_photos = photo_number
                self.status.last_capture_time = datetime.now()
                
                # Cache the latest frame for live preview
                try:
                    _, jpeg_bytes = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    with self._latest_frame_lock:
                        self._latest_frame = jpeg_bytes.tobytes()
                except Exception as e:
                    logger.warning(f"Could not cache latest frame: {e}")
                
                # Save session metadata
                self.storage.save_session_metadata(self.current_session)
                
                logger.info(f"Captured image #{photo_number}: {filename}")
                return True
            else:
                error_msg = f"Failed to save image: {filepath}"
                logger.error(error_msg)
                self._add_error(error_msg)
                return False
                
        except Exception as e:
            error_msg = f"Error saving image: {e}"
            logger.error(error_msg)
            self._add_error(error_msg)
            return False
    
    def _add_error(self, error_msg: str) -> None:
        """Add an error to the session and status."""
        self.status.total_errors += 1
        self.status.last_error = error_msg
        
        if self.current_session:
            self.current_session.errors.append(
                f"{datetime.now().isoformat()}: {error_msg}"
            )
