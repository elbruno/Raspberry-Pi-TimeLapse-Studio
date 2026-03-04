"""
storage_manager.py - Session & Photo Storage for Touch TimeLapse

Manages the on-disk layout:
    <base_path>/
    ├── session_20240120_153000/
    │   ├── session.json
    │   ├── photo_000001.jpg
    │   ├── photo_000002.jpg
    │   └── ...
    └── session_20240121_090000/
        └── ...

Each session folder contains its photos plus a ``session.json``
metadata file that is updated after every capture for crash-recovery.

Usage:
    storage = StorageManager("/media/pi/USB")
    session = storage.create_session()
    path    = storage.save_photo(session, frame, quality=90)
    storage.save_session_metadata(session)
"""

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import numpy as np

logger = logging.getLogger(__name__)

# Optional — OpenCV needed for saving JPEG files
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    cv2 = None
    logger.warning("OpenCV not available — photo saving will fail")


# ---------------------------------------------------------------------------
# Session dataclass
# ---------------------------------------------------------------------------

@dataclass
class Session:
    """Metadata for a single time-lapse recording session."""

    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_photos: int = 0
    photo_paths: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    status: str = "active"           # active | stopped | completed | interrupted
    output_folder: str = ""

    def is_active(self) -> bool:
        """True while the session has not been stopped."""
        return self.end_time is None

    def duration_seconds(self) -> float:
        """Elapsed seconds since the session started."""
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()

    # -- serialisation helpers ------------------------------------------------

    def to_dict(self) -> dict:
        """Convert to a JSON-friendly dictionary."""
        return {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_photos": self.total_photos,
            "photo_paths": self.photo_paths,
            "errors": self.errors,
            "status": self.status,
            "output_folder": self.output_folder,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        """Reconstruct a Session from a dictionary (e.g. loaded JSON)."""
        return cls(
            session_id=data.get("session_id", ""),
            start_time=(
                datetime.fromisoformat(data["start_time"])
                if data.get("start_time") else datetime.now()
            ),
            end_time=(
                datetime.fromisoformat(data["end_time"])
                if data.get("end_time") else None
            ),
            total_photos=data.get("total_photos", 0),
            photo_paths=data.get("photo_paths", []),
            errors=data.get("errors", []),
            status=data.get("status", "active"),
            output_folder=data.get("output_folder", ""),
        )


# ---------------------------------------------------------------------------
# StorageManager
# ---------------------------------------------------------------------------

class StorageManager:
    """
    Manages session folders, photo files, and metadata persistence.

    Args:
        base_path: Root directory for all sessions (typically a USB mount).
    """

    _session_counter: int = 0

    def __init__(self, base_path: str) -> None:
        self.base_path = Path(base_path)
        os.makedirs(self.base_path, exist_ok=True)
        logger.info("StorageManager initialised — base: %s", self.base_path)

    # -- session lifecycle ----------------------------------------------------

    def create_session(self) -> Session:
        """
        Create a new session with a timestamped folder.

        Returns:
            A fresh Session object ready for captures.
        """
        now = datetime.now()
        StorageManager._session_counter += 1
        session_id = now.strftime("session_%Y%m%d_%H%M%S") + f"_{StorageManager._session_counter:04d}"
        folder = self.base_path / session_id
        os.makedirs(folder, exist_ok=True)

        session = Session(
            session_id=session_id,
            start_time=now,
            output_folder=str(folder),
        )
        self.save_session_metadata(session)
        logger.info("Created session %s → %s", session_id, folder)
        return session

    def resume_session(self, session: Session) -> Session:
        """
        Resume an interrupted session, continuing photo numbering.

        Args:
            session: The interrupted Session loaded from disk.

        Returns:
            The same Session with status set to ``"running"``.
        """
        session.status = "active"
        # photo numbering continues from total_photos (handled by save_photo)
        self.save_session_metadata(session)
        logger.info(
            "Resumed session %s at photo #%d",
            session.session_id, session.total_photos
        )
        return session

    # -- photo persistence ----------------------------------------------------

    def save_photo(self, session: Session, frame: np.ndarray,
                   quality: int = 90) -> Optional[str]:
        """
        Encode *frame* as JPEG and write it to the session folder.

        Args:
            session: Active session.
            frame:   BGR image (numpy array).
            quality: JPEG quality 1-100.

        Returns:
            Absolute path to the saved file, or None on failure.
        """
        if not OPENCV_AVAILABLE:
            logger.error("Cannot save photo — OpenCV unavailable")
            return None

        if frame is None:
            logger.error("Cannot save None frame")
            return None

        session.total_photos += 1
        filename = f"photo_{session.total_photos:06d}.jpg"
        filepath = os.path.join(session.output_folder, filename)

        try:
            params = [cv2.IMWRITE_JPEG_QUALITY, quality]
            success = cv2.imwrite(filepath, frame, params)
            if success:
                session.photo_paths.append(filepath)
                logger.debug("Saved %s", filepath)
                return filepath
            else:
                logger.error("cv2.imwrite failed for %s", filepath)
                session.total_photos -= 1
                return None
        except Exception as e:
            logger.error("Error saving photo: %s", e)
            session.total_photos -= 1
            return None

    # -- metadata persistence -------------------------------------------------

    def save_session_metadata(self, session: Session) -> None:
        """Write ``session.json`` into the session folder."""
        if not session.output_folder:
            logger.error("Session has no output_folder — cannot save metadata")
            return

        path = os.path.join(session.output_folder, "session.json")
        try:
            with open(path, "w") as f:
                json.dump(session.to_dict(), f, indent=2)
            logger.debug("Metadata saved → %s", path)
        except Exception as e:
            logger.error("Failed to save session metadata: %s", e)

    def load_session_metadata(self, session_path: str) -> Optional[Session]:
        """
        Load a Session from the ``session.json`` inside *session_path*.

        Args:
            session_path: Path to a session folder.

        Returns:
            Session object, or None if the file is missing / corrupt.
        """
        meta_file = os.path.join(session_path, "session.json")
        if not os.path.exists(meta_file):
            logger.warning("No session.json in %s", session_path)
            return None

        try:
            with open(meta_file, "r") as f:
                data = json.load(f)
            return Session.from_dict(data)
        except Exception as e:
            logger.error("Failed to load session metadata from %s: %s",
                         session_path, e)
            return None

    # -- crash recovery -------------------------------------------------------

    def find_interrupted_session(self) -> Optional[Session]:
        """
        Scan for a session whose ``end_time`` is None (crash / power loss).

        Returns:
            The most recent interrupted Session, or None.
        """
        if not self.base_path.exists():
            return None

        candidates: list[Session] = []
        for folder in sorted(self.base_path.iterdir(), reverse=True):
            if folder.is_dir() and folder.name.startswith("session_"):
                session = self.load_session_metadata(str(folder))
                if session and session.end_time is None:
                    candidates.append(session)

        if candidates:
            chosen = candidates[0]  # most recent by folder name (reverse sort)
            logger.info("Found interrupted session: %s (%d photos so far)",
                        chosen.session_id, chosen.total_photos)
            return chosen

        return None
