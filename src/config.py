"""
Configuration module for managing settings and constants.
"""

import os
from pathlib import Path

class Config:
    """Application configuration."""
    
    # Paths
    BASE_DIR = Path(__file__).parent.parent
    OUTPUT_DIR = Path(os.getenv('OUTPUT_FOLDER', './output'))
    
    # OpenAI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = 'gpt-4'
    
    # Video Settings
    VIDEO_WIDTH = 1080
    VIDEO_HEIGHT = 1920  # Vertical format
    VIDEO_FPS = 30
    VIDEO_DURATION = int(os.getenv('VIDEO_DURATION', 30))
    
    # Content Settings
    CONTENT_NICHE = os.getenv('CONTENT_NICHE', 'motivational')
    
    # Scheduling
    AUTO_POST_ENABLED = os.getenv('AUTO_POST_ENABLED', 'false').lower() == 'true'
    POST_SCHEDULE = os.getenv('POST_SCHEDULE', '09:00,15:00,21:00')
    
    # Platform Settings
    YOUTUBE_CLIENT_ID = os.getenv('YOUTUBE_CLIENT_ID')
    YOUTUBE_CLIENT_SECRET = os.getenv('YOUTUBE_CLIENT_SECRET')
    YOUTUBE_CHANNEL_ID = os.getenv('YOUTUBE_CHANNEL_ID')
    
    TIKTOK_SESSION_ID = os.getenv('TIKTOK_SESSION_ID')
    TIKTOK_USERNAME = os.getenv('TIKTOK_USERNAME')
    
    @classmethod
    def validate(cls):
        """Validate required configuration."""
        errors = []
        
        if not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required")
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
        
        return True
