"""
Configuration Module
Application settings and configuration management.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class AppConfig:
    """Application configuration"""
    # Paths
    schemas_dir: str = "data/schemas"
    output_dir: str = "output"
    temp_dir: str = "temp"
    
    # Streamlit settings
    page_title: str = "EIT Tool - Dynamic XML Generator"
    page_icon: str = "📄"
    layout: str = "wide"
    
    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_title: str = "EIT Tool API"
    api_version: str = "1.0.0"
    
    # XML settings
    pretty_print: bool = True
    encoding: str = "utf-8"
    
    # Validation settings
    strict_validation: bool = True
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    
    # UI settings
    max_preview_length: int = 1000
    form_sections: bool = True
    
    def __post_init__(self):
        """Create directories if they don't exist"""
        for dir_path in [self.schemas_dir, self.output_dir, self.temp_dir]:
            os.makedirs(dir_path, exist_ok=True)


class ConfigManager:
    """Configuration manager"""
    
    def __init__(self):
        self.config = AppConfig()
        self._load_env_vars()
    
    def _load_env_vars(self):
        """Load configuration from environment variables"""
        # API settings
        self.config.api_host = os.getenv("EIT_API_HOST", self.config.api_host)
        self.config.api_port = int(os.getenv("EIT_API_PORT", self.config.api_port))
        
        # Paths
        self.config.schemas_dir = os.getenv("EIT_SCHEMAS_DIR", self.config.schemas_dir)
        self.config.output_dir = os.getenv("EIT_OUTPUT_DIR", self.config.output_dir)
        self.config.temp_dir = os.getenv("EIT_TEMP_DIR", self.config.temp_dir)
        
        # Validation settings
        self.config.strict_validation = os.getenv("EIT_STRICT_VALIDATION", "true").lower() == "true"
        self.config.max_file_size = int(os.getenv("EIT_MAX_FILE_SIZE", self.config.max_file_size))
        
        # Recreate directories with new paths
        self.config.__post_init__()
    
    def get_config(self) -> AppConfig:
        """Get current configuration"""
        return self.config
    
    def update_config(self, updates: Dict[str, Any]):
        """Update configuration"""
        for key, value in updates.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
    
    def get_xsd_files(self) -> list:
        """Get list of XSD files in schemas directory"""
        xsd_files = []
        if os.path.exists(self.config.schemas_dir):
            for file in os.listdir(self.config.schemas_dir):
                if file.endswith('.xsd'):
                    xsd_files.append(os.path.join(self.config.schemas_dir, file))
        return xsd_files
    
    def get_output_path(self, filename: str) -> str:
        """Get full output path for a file"""
        return os.path.join(self.config.output_dir, filename)
    
    def get_temp_path(self, filename: str) -> str:
        """Get full temp path for a file"""
        return os.path.join(self.config.temp_dir, filename)


# Global configuration instance
config_manager = ConfigManager()
config = config_manager.get_config()