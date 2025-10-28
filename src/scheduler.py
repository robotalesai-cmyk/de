"""Scheduler module for automated video posting."""

import os
import time
import schedule
from datetime import datetime

class VideoScheduler:
    """Schedules automated video creation and posting."""
    
    def __init__(self, content_generator, video_creator, uploader):
        """
        Initialize scheduler.
        
        Args:
            content_generator: ContentGenerator instance
            video_creator: VideoCreator instance
            uploader: VideoUploader instance
        """
        self.content_gen = content_generator
        self.video_creator = video_creator
        self.uploader = uploader
        
        # Parse schedule from environment
        schedule_str = os.getenv('POST_SCHEDULE', '09:00,15:00,21:00')
        self.post_times = [t.strip() for t in schedule_str.split(',')]
    
    def start(self):
        """Start the scheduler."""
        print(f"📅 Scheduler starting with post times: {', '.join(self.post_times)}")
        
        # Schedule jobs
        for post_time in self.post_times:
            schedule.every().day.at(post_time).do(self.create_and_post_video)
            print(f"⏰ Scheduled post at {post_time}")
        
        # Run scheduler loop
        print("🔄 Scheduler running. Press Ctrl+C to stop.")
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def create_and_post_video(self):
        """Job function to create and post a video."""
        try:
            print(f"\n{'='*50}")
            print(f"🎬 Starting scheduled video creation at {datetime.now()}")
            print(f"{'='*50}\n")
            
            # Get niche
            niche = os.getenv('CONTENT_NICHE', 'motivational')
            
            # Generate content
            print("📝 Generating content...")
            content = self.content_gen.generate_content(niche)
            
            # Create video
            print("🎥 Creating video...")
            video_path = self.video_creator.create_video(content)
            
            # Upload
            print("📤 Uploading to platforms...")
            results = self.uploader.upload_to_all_platforms(video_path, content)
            
            # Report results
            print("\n📊 Upload Results:")
            for platform, result in results.items():
                if result['success']:
                    print(f"✅ {platform}: {result['url']}")
                else:
                    print(f"❌ {platform}: {result['error']}")
            
            print(f"\n✨ Job completed at {datetime.now()}")
            
        except Exception as e:
            print(f"❌ Error in scheduled job: {e}")
            import traceback
            traceback.print_exc()
