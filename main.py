"""
Main entry point for the automated viral video bot.
Orchestrates content generation, video creation, and platform uploads.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from src.content_generator import ContentGenerator
from src.video_creator import VideoCreator
from src.uploader import VideoUploader
from src.scheduler import VideoScheduler

def setup_environment():
    """Load environment variables and create necessary directories."""
    load_dotenv()
    
    # Create output directory
    output_dir = Path(os.getenv('OUTPUT_FOLDER', './output'))
    output_dir.mkdir(exist_ok=True)
    
    return output_dir

def create_video(content_gen, video_creator, niche=None):
    """Generate and create a single video."""
    print("🎬 Generating video content...")
    
    # Generate script and metadata
    content = content_gen.generate_content(niche)
    
    print(f"📝 Script: {content['script'][:100]}...")
    print(f"🎯 Hook: {content['hook']}")
    
    # Create video
    print("🎥 Creating video...")
    video_path = video_creator.create_video(content)
    
    print(f"✅ Video created: {video_path}")
    return video_path, content

def upload_video(uploader, video_path, content):
    """Upload video to platforms."""
    print("📤 Uploading to platforms...")
    
    results = uploader.upload_to_all_platforms(video_path, content)
    
    for platform, result in results.items():
        if result['success']:
            print(f"✅ {platform}: {result['url']}")
        else:
            print(f"❌ {platform}: {result['error']}")
    
    return results

def main():
    """Main execution function."""
    print("🤖 Automated Viral Video Bot Starting...")
    
    # Setup
    output_dir = setup_environment()
    
    # Initialize components
    content_gen = ContentGenerator()
    video_creator = VideoCreator(output_dir)
    uploader = VideoUploader()
    
    # Check if scheduling is enabled
    auto_post = os.getenv('AUTO_POST_ENABLED', 'false').lower() == 'true'
    
    if auto_post:
        print("📅 Starting scheduler mode...")
        scheduler = VideoScheduler(content_gen, video_creator, uploader)
        scheduler.start()
    else:
        # Single video mode
        print("🎬 Creating single video...")
        niche = os.getenv('CONTENT_NICHE', 'motivational')
        
        video_path, content = create_video(content_gen, video_creator, niche)
        upload_video(uploader, video_path, content)
        
        print("✨ Done!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
