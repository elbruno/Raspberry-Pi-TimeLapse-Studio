"""
config.py - Configuration Management for PiTimeLapse Lab

This file handles loading, validating, and saving the application's settings.

Configuration can come from two sources:
1. config.yaml - The main configuration file (human-readable YAML format)
2. .env file - Optional overrides for sensitive or path settings

The .env file takes priority over config.yaml for the settings it defines.
This lets you keep the same config.yaml but change paths/ports per installation.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Any, Dict, List
from dataclasses import dataclass, field, asdict
import yaml

# Try to load dotenv - it's optional for .env file support
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

# Set up logging
logger = logging.getLogger(__name__)

# Default paths - these are relative to the project root
DEFAULT_CONFIG_PATH = "config.yaml"
DEFAULT_ENV_PATH = ".env"


@dataclass
class AppConfig:
    """
    All configuration settings for PiTimeLapse Lab.
    
    This dataclass defines every setting the app uses, with sensible defaults.
    Think of it as a form with all the settings filled in with default values.
    
    Attributes are grouped by category for easier understanding.
    """
    
    # Camera Settings
    # ---------------
    camera_mode: str = "opencv"  # "picamera2" or "opencv"
    resolution_width: int = 1280  # Image width in pixels
    resolution_height: int = 720  # Image height in pixels
    
    # Capture Settings
    # ----------------
    interval_seconds: int = 10  # Seconds between each photo
    start_delay_seconds: int = 0  # Wait this many seconds before first capture
    duration_limit_seconds: int = 0  # 0 = run until stopped manually
    
    # Output Settings
    # ---------------
    output_dir: str = "./data"  # Where to save session folders
    image_format: str = "jpg"  # File format: "jpg" or "png"
    overlay_timestamp: bool = True  # Add timestamp text to images?
    
    # Web Server Settings
    # -------------------
    web_host: str = "0.0.0.0"  # "0.0.0.0" means accept connections from any IP
    web_port: int = 8000  # The port number for the web interface
    
    # Advanced Settings
    # -----------------
    timezone: str = "local"  # Timezone for timestamps (or "local" for system timezone)
    retention_days: int = 0  # Auto-delete sessions older than this (0 = never delete)
    max_storage_mb: int = 0  # Stop capturing if storage exceeds this (0 = no limit)
    log_level: str = "INFO"  # Logging verbosity: DEBUG, INFO, WARNING, ERROR
    
    def validate(self) -> List[str]:
        """
        Check if all settings have valid values.
        
        Returns:
            A list of error messages. Empty list means everything is valid!
        """
        errors = []
        
        # Validate camera_mode
        valid_modes = ["picamera2", "opencv"]
        if self.camera_mode not in valid_modes:
            errors.append(
                f"camera_mode must be one of {valid_modes}, got '{self.camera_mode}'"
            )
        
        # Validate interval (must be positive)
        if self.interval_seconds < 1:
            errors.append(
                f"interval_seconds must be at least 1, got {self.interval_seconds}"
            )
        
        # Validate resolution (reasonable bounds)
        if self.resolution_width < 1 or self.resolution_width > 10000:
            errors.append(
                f"resolution_width must be between 1 and 10000, got {self.resolution_width}"
            )
        if self.resolution_height < 1 or self.resolution_height > 10000:
            errors.append(
                f"resolution_height must be between 1 and 10000, got {self.resolution_height}"
            )
        
        # Validate image format
        valid_formats = ["jpg", "jpeg", "png"]
        if self.image_format.lower() not in valid_formats:
            errors.append(
                f"image_format must be one of {valid_formats}, got '{self.image_format}'"
            )
        
        # Validate port number
        if self.web_port < 1 or self.web_port > 65535:
            errors.append(
                f"web_port must be between 1 and 65535, got {self.web_port}"
            )
        
        # Validate delays and durations (can't be negative)
        if self.start_delay_seconds < 0:
            errors.append(
                f"start_delay_seconds cannot be negative, got {self.start_delay_seconds}"
            )
        if self.duration_limit_seconds < 0:
            errors.append(
                f"duration_limit_seconds cannot be negative, got {self.duration_limit_seconds}"
            )
        
        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_log_levels:
            errors.append(
                f"log_level must be one of {valid_log_levels}, got '{self.log_level}'"
            )
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to a dictionary (for saving to YAML)."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppConfig":
        """
        Create an AppConfig from a dictionary.
        
        Only uses keys that match AppConfig fields; ignores unknown keys.
        """
        # Get the names of all fields in AppConfig
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        
        # Filter the dictionary to only include valid keys
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}
        
        return cls(**filtered_data)


def load_config(
    config_path: str = DEFAULT_CONFIG_PATH,
    env_path: str = DEFAULT_ENV_PATH
) -> AppConfig:
    """
    Load configuration from files.
    
    This function:
    1. Starts with default values
    2. Loads settings from config.yaml (if it exists)
    3. Applies overrides from .env file (if it exists and dotenv is installed)
    
    Args:
        config_path: Path to the YAML config file
        env_path: Path to the .env file
        
    Returns:
        An AppConfig object with all settings loaded
    """
    # Start with defaults
    config = AppConfig()
    
    # Step 1: Load from YAML file if it exists
    yaml_path = Path(config_path)
    if yaml_path.exists():
        try:
            with open(yaml_path, "r") as f:
                yaml_data = yaml.safe_load(f) or {}
            
            logger.info(f"Loaded config from {config_path}")
            config = AppConfig.from_dict(yaml_data)
            
        except yaml.YAMLError as e:
            logger.error(f"Error parsing {config_path}: {e}")
            logger.info("Using default configuration")
        except Exception as e:
            logger.error(f"Error reading {config_path}: {e}")
            logger.info("Using default configuration")
    else:
        logger.info(f"No config file found at {config_path}, using defaults")
    
    # Step 2: Load .env file if available
    env_file = Path(env_path)
    if DOTENV_AVAILABLE and env_file.exists():
        load_dotenv(env_path)
        logger.info(f"Loaded environment from {env_path}")
    
    # Step 3: Apply environment variable overrides
    # Environment variables take priority over config.yaml
    config = _apply_env_overrides(config)
    
    return config


def _apply_env_overrides(config: AppConfig) -> AppConfig:
    """
    Override config values with environment variables.
    
    Environment variables use the pattern: PITIMELAPSE_<SETTING_NAME>
    For example: PITIMELAPSE_OUTPUT_DIR, PITIMELAPSE_WEB_PORT
    
    Args:
        config: The current AppConfig
        
    Returns:
        AppConfig with environment overrides applied
    """
    # Map of environment variable names to config attributes
    # (env_var_name, config_attr_name, type_converter)
    overrides = [
        ("PITIMELAPSE_CAMERA_MODE", "camera_mode", str),
        ("PITIMELAPSE_OUTPUT_DIR", "output_dir", str),
        ("PITIMELAPSE_WEB_HOST", "web_host", str),
        ("PITIMELAPSE_WEB_PORT", "web_port", int),
        ("PITIMELAPSE_INTERVAL_SECONDS", "interval_seconds", int),
        ("PITIMELAPSE_LOG_LEVEL", "log_level", str),
    ]
    
    for env_var, attr_name, type_func in overrides:
        env_value = os.getenv(env_var)
        if env_value is not None:
            try:
                # Convert the string from environment to the right type
                converted_value = type_func(env_value)
                setattr(config, attr_name, converted_value)
                logger.debug(f"Override from environment: {attr_name} = {converted_value}")
            except ValueError as e:
                logger.warning(f"Invalid value for {env_var}: {e}")
    
    return config


def save_config(config: AppConfig, config_path: str = DEFAULT_CONFIG_PATH) -> bool:
    """
    Save configuration to a YAML file.
    
    This is called when settings are changed through the web interface.
    
    Args:
        config: The AppConfig to save
        config_path: Where to save it
        
    Returns:
        True if saved successfully, False otherwise
    """
    try:
        config_dict = config.to_dict()
        
        # Add a helpful comment at the top
        yaml_content = "# PiTimeLapse Lab Configuration\n"
        yaml_content += "# Edit this file to change default settings.\n"
        yaml_content += "# You can also use environment variables for some settings.\n\n"
        yaml_content += yaml.dump(config_dict, default_flow_style=False, sort_keys=False)
        
        with open(config_path, "w") as f:
            f.write(yaml_content)
        
        logger.info(f"Configuration saved to {config_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save configuration: {e}")
        return False


def create_default_config(config_path: str = DEFAULT_CONFIG_PATH) -> bool:
    """
    Create a config file with all default values.
    
    This is useful for first-time setup.
    
    Args:
        config_path: Where to create the config file
        
    Returns:
        True if created successfully, False otherwise
    """
    default_config = AppConfig()
    return save_config(default_config, config_path)
