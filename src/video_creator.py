"""Video creation module for generating short-form videos."""

import os
from pathlib import Path
from datetime import datetime
import random

from moviepy.editor import (
    TextClip, CompositeVideoClip, AudioFileClip,
    ColorClip, concatenate_videoclips
)
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

class VideoCreator:
    """Creates short-form videos with text, audio, and visuals."""
    
    def __init__(self, output_dir):
        """Initialize video creator."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Video settings
        self.width = 1080
        self.height = 1920  # Vertical format for TikTok/Shorts
        self.fps = 30
        self.duration = int(os.getenv('VIDEO_DURATION', 30))
    
    def create_video(self, content):
        """
        Create a complete video from content.
        
        Args:
            content: Content dictionary from ContentGenerator
            
        Returns:
            str: Path to created video file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_filename = f"video_{timestamp}.mp4"
        video_path = self.output_dir / video_filename
        
        # Generate audio from script
        audio_path = self._generate_audio(content['script'], timestamp)
        
        # Get actual audio duration
        audio = AudioFileClip(str(audio_path))
        video_duration = min(audio.duration, self.duration)
        
        # Create background
        background = self._create_background(video_duration)
        
        # Add text overlays
        video_with_text = self._add_text_overlays(background, content['script'], video_duration)
        
        # Add audio
        final_video = video_with_text.set_audio(audio)
        
        # Write video file
        final_video.write_videofile(
            str(video_path),
            fps=self.fps,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile=str(self.output_dir / 'temp_audio.m4a'),
            remove_temp=True,
            logger=None
        )
        
        # Cleanup
        audio.close()
        final_video.close()
        
        return str(video_path)
    
    def _generate_audio(self, script, timestamp):
        """Generate text-to-speech audio."""
        audio_path = self.output_dir / f"audio_{timestamp}.mp3"
        
        # Generate speech
        tts = gTTS(text=script, lang='en', slow=False)
        tts.save(str(audio_path))
        
        return audio_path
    
    def _create_background(self, duration):
        """Create an engaging background."""
        # Create a gradient background
        background = ColorClip(
            size=(self.width, self.height),
            color=self._get_random_gradient_color(),
            duration=duration
        )
        
        return background
    
    def _get_random_gradient_color(self):
        """Get a random color for background."""
        color_schemes = [
            (139, 69, 19),    # Brown/Warm
            (25, 25, 112),    # Midnight Blue
            (72, 61, 139),    # Dark Slate Blue
            (47, 79, 79),     # Dark Slate Gray
            (85, 107, 47),    # Dark Olive Green
        ]
        return random.choice(color_schemes)
    
    def _add_text_overlays(self, background, script, duration):
        """Add text overlays to video."""
        # Split script into chunks for better readability
        words = script.split()
        chunk_size = 5  # Words per chunk
        chunks = [' '.join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
        
        # Calculate timing for each chunk
        time_per_chunk = duration / len(chunks)
        
        text_clips = []
        
        for i, chunk in enumerate(chunks):
            start_time = i * time_per_chunk
            
            # Create text clip
            txt_clip = TextClip(
                chunk,
                fontsize=70,
                color='white',
                font='Arial-Bold',
                stroke_color='black',
                stroke_width=2,
                method='caption',
                size=(self.width - 100, None),
                align='center'
            )
            
            # Position and timing
            txt_clip = (txt_clip
                       .set_position('center')
                       .set_start(start_time)
                       .set_duration(time_per_chunk))
            
            text_clips.append(txt_clip)
        
        # Composite video
        video = CompositeVideoClip([background] + text_clips)
        
        return video
    
    def cleanup_temp_files(self):
        """Remove temporary audio files."""
        for file in self.output_dir.glob("audio_*.mp3"):
            try:
                file.unlink()
            except Exception:
                pass
