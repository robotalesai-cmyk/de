"""
Simple tests for the video bot components.
Run with: python -m pytest tests/ -v
"""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Test imports
def test_imports():
    """Test that all modules can be imported."""
    from src.content_generator import ContentGenerator
    from src.video_creator import VideoCreator
    from src.uploader import VideoUploader
    from src.scheduler import VideoScheduler
    from src.config import Config
    assert True

# Test ContentGenerator
def test_content_generator_init():
    """Test ContentGenerator initialization."""
    with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
        from src.content_generator import ContentGenerator
        gen = ContentGenerator()
        assert gen.client is not None
        assert 'motivational' in gen.niches

def test_content_generator_extract_hook():
    """Test hook extraction."""
    with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
        from src.content_generator import ContentGenerator
        gen = ContentGenerator()
        script = "This is amazing. You won't believe what happens next. It's incredible."
        hook = gen._extract_hook(script)
        assert len(hook) > 0
        assert hook.startswith("This is amazing")

def test_content_generator_generate_hashtags():
    """Test hashtag generation."""
    with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
        from src.content_generator import ContentGenerator
        gen = ContentGenerator()
        hashtags = gen._generate_hashtags('motivational')
        assert '#fyp' in hashtags
        assert '#motivation' in hashtags

# Test VideoCreator
def test_video_creator_init():
    """Test VideoCreator initialization."""
    from src.video_creator import VideoCreator
    creator = VideoCreator(Path('/tmp/test_output'))
    assert creator.width == 1080
    assert creator.height == 1920
    assert creator.fps == 30

def test_video_creator_gradient_color():
    """Test random gradient color generation."""
    from src.video_creator import VideoCreator
    creator = VideoCreator(Path('/tmp/test_output'))
    color = creator._get_random_gradient_color()
    assert isinstance(color, tuple)
    assert len(color) == 3

# Test Uploader
def test_uploader_extract_tags():
    """Test tag extraction from hashtags."""
    from src.uploader import VideoUploader
    uploader = VideoUploader()
    hashtags = "#viral #fyp #trending #motivation"
    tags = uploader._extract_tags(hashtags)
    assert 'viral' in tags
    assert 'fyp' in tags
    assert len(tags) <= 15

# Test Config
def test_config_validation():
    """Test configuration validation."""
    from src.config import Config
    
    # Should raise error without API key
    with patch.dict(os.environ, {'OPENAI_API_KEY': ''}):
        with pytest.raises(ValueError):
            Config.validate()
    
    # Should pass with API key
    with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
        assert Config.validate() == True

def test_config_defaults():
    """Test default configuration values."""
    from src.config import Config
    assert Config.VIDEO_WIDTH == 1080
    assert Config.VIDEO_HEIGHT == 1920
    assert Config.VIDEO_FPS == 30

# Test Scheduler
def test_scheduler_init():
    """Test scheduler initialization."""
    from src.scheduler import VideoScheduler
    
    mock_gen = Mock()
    mock_creator = Mock()
    mock_uploader = Mock()
    
    with patch.dict(os.environ, {'POST_SCHEDULE': '09:00,15:00,21:00'}):
        scheduler = VideoScheduler(mock_gen, mock_creator, mock_uploader)
        assert len(scheduler.post_times) == 3
        assert '09:00' in scheduler.post_times

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
