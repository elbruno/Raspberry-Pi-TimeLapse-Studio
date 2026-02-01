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
    Validate the configuration file.
    
    Checks if all settings are valid and shows any errors.
    """
    print("Validating configuration...")
    
    try:
        config = load_config()
        errors = config.validate()
        
        if errors:
            print("\n❌ Configuration errors found:\n")
            for error in errors:
                print(f"  - {error}")
            return 1
        else:
            print("\n✅ Configuration is valid!\n")
            print("Current settings:")
            print(f"  Camera mode: {config.camera_mode}")
            print(f"  Resolution: {config.resolution_width}x{config.resolution_height}")
            print(f"  Interval: {config.interval_seconds} seconds")
            print(f"  Output: {config.output_dir}")
            print(f"  Web server: {config.web_host}:{config.web_port}")
            return 0
            
    except Exception as e:
        print(f"\n❌ Error loading configuration: {e}")
        return 1


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
    subparsers.add_parser("validate", help="Validate configuration file")
    
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
