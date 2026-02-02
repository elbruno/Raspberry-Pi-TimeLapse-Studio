"""
storage.py - File and Session Storage Management

This file handles:
- Creating session folders for each time-lapse
- Naming files properly
- Saving session metadata (the JSON log file)
- Cleaning up old sessions
- Checking disk space

Think of this as the "filing cabinet" of the application.
"""

import os
import json
import shutil
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from .models import Session
from .utils import (
    generate_session_id,
    get_timestamp_string,
    get_folder_size_mb,
    ensure_folder_exists,
)

# Set up logging
logger = logging.getLogger(__name__)


class StorageManager:
    """
    Manages file storage for time-lapse sessions.
    
    Each session gets its own folder with:
    - Captured images
    - A session.json file with metadata (settings, counts, etc.)
    
    Example folder structure:
        data/
        ├── session_20240115_140000/
        │   ├── session.json
        │   ├── img_0001_20240115_140000.jpg
        │   ├── img_0002_20240115_140010.jpg
        │   └── ...
        └── session_20240115_150000/
            └── ...
    """
    
    def __init__(self, base_dir: str = "./data"):
        """
        Initialize the storage manager.
        
        Args:
            base_dir: The root folder where all sessions are stored
        """
        self.base_dir = Path(base_dir)
        
        # Make sure the base directory exists
        ensure_folder_exists(str(self.base_dir))
        
        logger.info(f"StorageManager initialized with base_dir: {self.base_dir}")
    
    def create_session_folder(self, session_id: Optional[str] = None) -> str:
        """
        Create a new folder for a time-lapse session.
        
        Args:
            session_id: Optional custom session ID. If not provided, one is generated.
            
        Returns:
            The full path to the created session folder
        """
        if session_id is None:
            session_id = generate_session_id()
        
        session_folder = self.base_dir / session_id
        
        # Create the folder
        ensure_folder_exists(str(session_folder))
        
        logger.info(f"Created session folder: {session_folder}")
        return str(session_folder)
    
    def save_session_metadata(self, session: Session) -> bool:
        """
        Save session information to a JSON file.
        
        This is saved after each capture so we don't lose data if the app crashes.
        
        Args:
            session: The Session object to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        if not session.output_folder:
            logger.error("Cannot save metadata: session has no output folder")
            return False
        
        metadata_path = Path(session.output_folder) / "session.json"
        
        try:
            session_dict = session.to_dict()
            
            with open(metadata_path, "w") as f:
                json.dump(session_dict, f, indent=2)
            
            logger.debug(f"Session metadata saved to {metadata_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save session metadata: {e}")
            return False
    
    def load_session_metadata(self, session_folder: str) -> Optional[Session]:
        """
        Load session information from a JSON file.
        
        Args:
            session_folder: Path to the session folder
            
        Returns:
            A Session object, or None if loading failed
        """
        metadata_path = Path(session_folder) / "session.json"
        
        if not metadata_path.exists():
            logger.warning(f"No metadata file found at {metadata_path}")
            return None
        
        try:
            with open(metadata_path, "r") as f:
                data = json.load(f)
            
            return Session.from_dict(data)
            
        except Exception as e:
            logger.error(f"Failed to load session metadata: {e}")
            return None
    
    def list_sessions(self) -> List[Session]:
        """
        Get a list of all sessions in the data folder.
        
        Returns:
            List of Session objects, sorted by start time (newest first)
        """
        sessions = []
        
        if not self.base_dir.exists():
            return sessions
        
        # Look for folders that start with "session_"
        for folder in self.base_dir.iterdir():
            if folder.is_dir() and folder.name.startswith("session_"):
                session = self.load_session_metadata(str(folder))
                if session:
                    sessions.append(session)
        
        # Sort by start time (newest first)
        sessions.sort(key=lambda s: s.start_time, reverse=True)
        
        return sessions
    
    def get_session_images(self, session_folder: str) -> List[str]:
        """
        Get a list of all image files in a session folder.
        
        Args:
            session_folder: Path to the session folder
            
        Returns:
            List of image file paths, sorted by name
        """
        images = []
        folder = Path(session_folder)
        
        if not folder.exists():
            return images
        
        # Find all image files
        image_extensions = {".jpg", ".jpeg", ".png"}
        
        for file in folder.iterdir():
            if file.is_file() and file.suffix.lower() in image_extensions:
                images.append(str(file))
        
        # Sort by filename (which includes the sequence number)
        images.sort()
        
        return images
    
    def get_latest_images(
        self, session_folder: str, count: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get information about the most recent images in a session.
        
        Args:
            session_folder: Path to the session folder
            count: Maximum number of images to return
            
        Returns:
            List of dictionaries with image info (path, name, size, etc.)
        """
        all_images = self.get_session_images(session_folder)
        
        # Get the most recent images
        recent_images = all_images[-count:] if len(all_images) > count else all_images
        
        result = []
        for image_path in reversed(recent_images):  # Newest first
            path = Path(image_path)
            try:
                stat = path.stat()
                result.append({
                    "path": str(path),
                    "name": path.name,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })
            except Exception as e:
                logger.warning(f"Could not get info for {image_path}: {e}")
        
        return result
    
    def get_storage_usage_mb(self) -> float:
        """
        Calculate total storage used by all sessions.
        
        Returns:
            Total size in megabytes
        """
        return get_folder_size_mb(str(self.base_dir))
    
    def cleanup_old_sessions(self, retention_days: int) -> int:
        """
        Delete sessions older than a certain number of days.
        
        Args:
            retention_days: Delete sessions older than this
            
        Returns:
            Number of sessions deleted
        """
        if retention_days <= 0:
            return 0
        
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        deleted_count = 0
        
        for session in self.list_sessions():
            if session.end_time and session.end_time < cutoff_date:
                # Delete this session folder
                folder = Path(session.output_folder)
                if folder.exists():
                    try:
                        shutil.rmtree(folder)
                        logger.info(f"Deleted old session: {session.id}")
                        deleted_count += 1
                    except Exception as e:
                        logger.error(f"Failed to delete {session.id}: {e}")
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old session(s)")
        
        return deleted_count
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a specific session.
        
        Args:
            session_id: The ID of the session to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        session_folder = self.base_dir / session_id
        
        if not session_folder.exists():
            logger.warning(f"Session folder not found: {session_id}")
            return False
        
        try:
            shutil.rmtree(session_folder)
            logger.info(f"Deleted session: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False
    
    def create_session_zip(self, session_id: str, session_folder: Optional[str] = None) -> Optional[str]:
        """
        Create a ZIP file of a session for download.
        
        Args:
            session_id: The ID of the session to zip
            session_folder: Optional explicit path to session folder (for handling output_dir changes)
            
        Returns:
            Path to the ZIP file, or None if creation failed
        """
        if session_folder:
            folder = Path(session_folder)
        else:
            folder = self.base_dir / session_id
        
        if not folder.exists():
            logger.error(f"Session folder not found: {session_id} at {folder}")
            return None
        
        zip_path = self.base_dir / f"{session_id}.zip"
        
        try:
            # Create the ZIP file
            shutil.make_archive(
                str(self.base_dir / session_id),  # Base name (without .zip)
                "zip",
                folder,  # Folder to archive
            )
            
            logger.info(f"Created ZIP archive: {zip_path}")
            return str(zip_path)
            
        except Exception as e:
            logger.error(f"Failed to create ZIP for {session_id}: {e}")
            return None
