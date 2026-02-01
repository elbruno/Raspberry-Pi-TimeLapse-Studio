#!/usr/bin/env python3
"""
main.py - Entry Point for PiTimeLapse Lab

This is the main file that runs the application. You can:
1. Start the web server
2. Validate your configuration
3. List all sessions
4. Clean up old sessions

Usage:
    python main.py              # Start the web server
    python main.py --validate   # Check your config file
    python main.py --sessions   # List all sessions
    python main.py --cleanup 7  # Delete sessions older than 7 days

This file shows how to use Python's argparse module to create
a command-line interface (CLI).
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# Add the src directory to the Python path
# This allows us to import from the pitimelapse package
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from pitimelapse.config import load_config, save_config, create_default_config, AppConfig
from pitimelapse.storage import StorageManager
from pitimelapse.utils import format_duration, format_file_size


def setup_logging(level: str = "INFO") -> None:
    """
    Configure the logging system.
    
    Logging is like keeping a diary of what the program does.
    It helps with debugging and understanding what's happening.
    
    Args:
        level: How much detail to log (DEBUG, INFO, WARNING, ERROR)
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Configure the root logger
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # Make some noisy loggers quieter
    logging.getLogger("werkzeug").setLevel(logging.WARNING)


def cmd_run(args: argparse.Namespace) -> int:
    """
    Start the web server.
    
    This is the main command that runs the application.
    """
    # Load configuration
    config = load_config()
    
    # Set up logging
    setup_logging(config.log_level)
    
    logger = logging.getLogger(__name__)
    
    # Validate configuration
    errors = config.validate()
    if errors:
        logger.error("Configuration errors found:")
        for error in errors:
            logger.error(f"  - {error}")
        return 1
    
    # Initialize the Flask app
    from pitimelapse.app import app, init_app, run_server
    
    init_app(config)
    
    # Print startup message
    print("\n" + "=" * 50)
    print("🎬 PiTimeLapse Lab")
    print("=" * 50)
    print(f"Camera mode: {config.camera_mode}")
    print(f"Capture interval: {config.interval_seconds} seconds")
    print(f"Output directory: {config.output_dir}")
    print(f"Web interface: http://{config.web_host}:{config.web_port}")
    print("=" * 50)
    print("Press Ctrl+C to stop the server")
    print()
    
    try:
        # Start the Flask server
        run_server(
            host=config.web_host,
            port=config.web_port,
            debug=args.debug if hasattr(args, 'debug') else False,
        )
    except KeyboardInterrupt:
        print("\n\nShutting down...")
    except Exception as e:
        logger.exception("Server error")
        return 1
    
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """
    Validate the configuration file and check system requirements.
    
    Checks if:
    - Configuration file is valid
    - Required packages are installed
    - Camera is accessible
    - Output directory is writable
    """
    print("Validating configuration and system requirements...\n")
    
    try:
        config = load_config()
        errors = config.validate()
        
        if errors:
            print("❌ Configuration errors found:\n")
            for error in errors:
                print(f"  - {error}")
            print()
        
        # Check required packages
        print("Checking required packages:")
        package_errors = _check_packages(config)
        if package_errors:
            errors.extend(package_errors)
            for error in package_errors:
                print(f"  ❌ {error}")
        else:
            print("  ✅ All required packages are installed")
        
        print()
        
        # Check camera availability
        print("Checking camera availability:")
        camera_errors = _check_camera(config)
        if camera_errors:
            errors.extend(camera_errors)
            for error in camera_errors:
                print(f"  ❌ {error}")
        else:
            print("  ✅ Camera is available and accessible")
        
        print()
        
        # Check output directory
        print("Checking output directory:")
        storage_errors = _check_storage(config)
        if storage_errors:
            errors.extend(storage_errors)
            for error in storage_errors:
                print(f"  ❌ {error}")
        else:
            print(f"  ✅ Output directory is valid: {config.output_dir}")
        
        print()
        
        # Summary
        if errors:
            print(f"❌ Found {len(errors)} issue(s). Please fix them before running.\n")
            return 1
        else:
            print("✅ All checks passed! Configuration is ready.\n")
            print("Current settings:")
            print(f"  Camera mode: {config.camera_mode}")
            print(f"  Resolution: {config.resolution_width}x{config.resolution_height}")
            print(f"  Interval: {config.interval_seconds} seconds")
            print(f"  Output: {config.output_dir}")
            print(f"  Web server: {config.web_host}:{config.web_port}")
            print()
            return 0
            
    except Exception as e:
        print(f"\n❌ Error loading configuration: {e}")
        return 1


def _check_packages(config: AppConfig) -> list:
    """
    Check if required Python packages are installed.
    
    Returns:
        List of error messages (empty if all packages OK)
    """
    errors = []
    
    # Check Flask (always required)
    try:
        import flask
    except ImportError:
        errors.append("Flask is not installed")
    
    # Check PyYAML (always required)
    try:
        import yaml
    except ImportError:
        errors.append("PyYAML is not installed")
    
    # Check Pillow (always required for overlays)
    try:
        import PIL
    except ImportError:
        errors.append("Pillow is not installed")
    
    # Check camera-specific packages
    if config.camera_mode == "opencv":
        try:
            import cv2
        except ImportError:
            errors.append("opencv-python-headless is not installed (required for camera_mode: opencv)")
    
    elif config.camera_mode == "picamera2":
        try:
            import picamera2
        except ImportError:
            errors.append(
                "picamera2 is not installed. Install with: sudo apt install python3-picamera2"
            )
    
    return errors


def _check_camera(config: AppConfig) -> list:
    """
    Check if camera is available and accessible.
    
    Returns:
        List of error messages (empty if camera OK)
    """
    errors = []
    
    try:
        if config.camera_mode == "opencv":
            from pitimelapse.camera_opencv import OpenCVCamera
            
            camera = OpenCVCamera()
            
            if not camera.is_available():
                return ["OpenCV (cv2) is not available"]
            
            # Try to open the camera
            if not camera.open(
                width=config.resolution_width,
                height=config.resolution_height,
            ):
                return ["Cannot open camera. Check that the camera is connected and not in use by another application."]
            
            # Try to capture a test frame
            frame = camera.capture()
            camera.close()
            
            if frame is None:
                return ["Camera opened but failed to capture a test frame."]
        
        elif config.camera_mode == "picamera2":
            try:
                from pitimelapse.camera_picamera2 import PiCamera2Camera
                
                camera = PiCamera2Camera()
                
                if not camera.is_available():
                    return ["picamera2 is not available. Check that it's installed with: sudo apt install python3-picamera2"]
                
                # Try to open the camera
                if not camera.open(
                    width=config.resolution_width,
                    height=config.resolution_height,
                ):
                    return ["Cannot open Pi Camera. Check that the camera ribbon is connected and enabled."]
                
                # Try to capture a test frame
                frame = camera.capture()
                camera.close()
                
                if frame is None:
                    return ["Pi Camera opened but failed to capture a test frame."]
            
            except Exception as e:
                return [f"Error testing Pi Camera: {e}"]
        
    except Exception as e:
        errors.append(f"Error checking camera: {e}")
    
    return errors


def _check_storage(config: AppConfig) -> list:
    """
    Check if output directory exists and is writable.
    
    Returns:
        List of error messages (empty if storage OK)
    """
    errors = []
    
    try:
        # Create storage manager
        storage = StorageManager(config.output_dir)
        
        # Check if we can create a directory
        import tempfile
        import shutil
        
        test_dir = os.path.join(config.output_dir, ".test_write")
        
        try:
            os.makedirs(test_dir, exist_ok=True)
            # Try to write a test file
            test_file = os.path.join(test_dir, "test.txt")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            shutil.rmtree(test_dir, ignore_errors=True)
        except PermissionError:
            errors.append(f"No write permission to output directory: {config.output_dir}")
        except Exception as e:
            errors.append(f"Cannot write to output directory: {e}")
    
    except Exception as e:
        errors.append(f"Error checking storage: {e}")
    
    return errors


def cmd_sessions(args: argparse.Namespace) -> int:
    """
    List all time-lapse sessions.
    """
    config = load_config()
    storage = StorageManager(config.output_dir)
    
    sessions = storage.list_sessions()
    
    if not sessions:
        print("No sessions found.")
        return 0
    
    print(f"\nFound {len(sessions)} session(s):\n")
    print("-" * 70)
    
    for session in sessions:
        status = "🟢 Active" if session.is_active() else "⏹️ Ended"
        duration = format_duration(session.duration_seconds())
        
        print(f"📁 {session.id}")
        print(f"   Status: {status}")
        print(f"   Started: {session.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        if session.end_time:
            print(f"   Ended: {session.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Duration: {duration}")
        print(f"   Photos: {session.total_photos}")
        if session.errors:
            print(f"   Errors: {len(session.errors)}")
        print("-" * 70)
    
    # Show storage usage
    usage_mb = storage.get_storage_usage_mb()
    print(f"\nTotal storage used: {usage_mb:.2f} MB")
    
    return 0


def cmd_cleanup(args: argparse.Namespace) -> int:
    """
    Delete old sessions.
    """
    config = load_config()
    storage = StorageManager(config.output_dir)
    
    days = args.days
    
    print(f"Looking for sessions older than {days} days...")
    
    deleted = storage.cleanup_old_sessions(days)
    
    if deleted > 0:
        print(f"✅ Deleted {deleted} old session(s)")
    else:
        print("No old sessions to delete")
    
    return 0


def cmd_init(args: argparse.Namespace) -> int:
    """
    Create a default configuration file.
    """
    config_path = "config.yaml"
    
    if os.path.exists(config_path) and not args.force:
        print(f"Configuration file already exists: {config_path}")
        print("Use --force to overwrite")
        return 1
    
    if create_default_config(config_path):
        print(f"✅ Created default configuration: {config_path}")
        print("\nEdit this file to customize your settings, then run:")
        print("  python main.py")
        return 0
    else:
        print("❌ Failed to create configuration file")
        return 1


def main() -> int:
    """
    Main entry point - parse arguments and run the appropriate command.
    """
    # Create the argument parser
    parser = argparse.ArgumentParser(
        prog="pitimelapse",
        description="🎬 PiTimeLapse Lab - Capture beautiful time-lapse photos!",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    Start the web server
  python main.py --debug            Start with debug mode (auto-reload)
  python main.py validate           Check your configuration
  python main.py sessions           List all sessions
  python main.py cleanup --days 7   Delete sessions older than 7 days
  python main.py init               Create a default config file
        """,
    )
    
    # Create subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # 'run' command (default)
    run_parser = subparsers.add_parser("run", help="Start the web server")
    run_parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="Enable debug mode (auto-reload on code changes)"
    )
    
    # 'validate' command
    subparsers.add_parser(
        "validate",
        help="Validate configuration and check system requirements (packages, camera, permissions)"
    )
    
    # 'sessions' command
    subparsers.add_parser("sessions", help="List all sessions")
    
    # 'cleanup' command
    cleanup_parser = subparsers.add_parser("cleanup", help="Delete old sessions")
    cleanup_parser.add_argument(
        "--days", "-d",
        type=int,
        required=True,
        help="Delete sessions older than this many days"
    )
    
    # 'init' command
    init_parser = subparsers.add_parser("init", help="Create default config file")
    init_parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Overwrite existing config file"
    )
    
    # Also add --debug to the main parser for convenience
    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="Enable debug mode"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Route to the appropriate command
    if args.command == "validate":
        return cmd_validate(args)
    elif args.command == "sessions":
        return cmd_sessions(args)
    elif args.command == "cleanup":
        return cmd_cleanup(args)
    elif args.command == "init":
        return cmd_init(args)
    else:
        # Default to 'run' command
        return cmd_run(args)


if __name__ == "__main__":
    sys.exit(main())
