# Examples and Use Cases

## Example 1: Single Motivational Video

Create a single motivational video and post it:

```bash
# Set environment
export OPENAI_API_KEY="your_key"
export CONTENT_NICHE="motivational"
export VIDEO_DURATION=30
export AUTO_POST_ENABLED=false

# Run
python main.py
```

Output:
- Generated script with hook
- Video created in `output/` directory
- Uploaded to YouTube Shorts (if configured)

## Example 2: Facts Video Series

Create a series of fact videos throughout the day:

```bash
# Configure .env
CONTENT_NICHE=facts
AUTO_POST_ENABLED=true
POST_SCHEDULE=08:00,14:00,20:00

# Run scheduler
python main.py
```

The bot will automatically create and post videos at 8 AM, 2 PM, and 8 PM daily.

## Example 3: Custom Script Testing

Test video creation without posting:

```python
from src.content_generator import ContentGenerator
from src.video_creator import VideoCreator
from pathlib import Path

# Generate content
gen = ContentGenerator()
content = gen.generate_content('comedy')

print(f"Script: {content['script']}")
print(f"Title: {content['title']}")

# Create video
creator = VideoCreator(Path('./output'))
video_path = creator.create_video(content)

print(f"Video created: {video_path}")
```

## Example 4: Batch Video Creation

Create multiple videos at once:

```python
from src.content_generator import ContentGenerator
from src.video_creator import VideoCreator
from pathlib import Path

gen = ContentGenerator()
creator = VideoCreator(Path('./output'))

niches = ['motivational', 'facts', 'tips']

for niche in niches:
    print(f"Creating {niche} video...")
    content = gen.generate_content(niche)
    video_path = creator.create_video(content)
    print(f"Created: {video_path}")
```

## Example 5: YouTube-Only Upload

Upload only to YouTube:

```python
from src.uploader import VideoUploader

uploader = VideoUploader()

content = {
    'title': 'Amazing Fact You Didnt Know!',
    'description': 'This fact will blow your mind...',
    'hashtags': '#facts #viral #interesting'
}

result = uploader.upload_to_youtube('output/video.mp4', content)
print(f"Uploaded: {result['url']}")
```

## Content Niche Examples

### Motivational
```
Script: "You know what separates winners from losers? It's not talent. 
It's not luck. It's consistency. Every successful person you admire 
failed more times than you've even tried..."

Hook: "You know what separates winners from losers?"
```

### Facts
```
Script: "Did you know your brain can't actually feel pain? That's right - 
the organ that processes all your pain signals has no pain receptors of 
its own. Surgeons can operate on it while you're awake..."

Hook: "Did you know your brain can't actually feel pain?"
```

### Tips
```
Script: "Want to wake up easier? Put your alarm across the room. 
Seriously, this one trick changed my mornings. When you have to get up 
to turn it off, you're already up..."

Hook: "Want to wake up easier? Put your alarm across the room."
```

## Advanced Configuration

### Custom Video Dimensions

Edit `src/config.py`:
```python
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920  # Vertical
```

### Custom Text Styling

Edit `src/video_creator.py`:
```python
txt_clip = TextClip(
    chunk,
    fontsize=80,        # Larger text
    color='yellow',      # Different color
    font='Impact',       # Different font
    stroke_color='black',
    stroke_width=3
)
```

### Multiple Daily Niches

Schedule different niches at different times:

```python
# In src/scheduler.py
niches = ['motivational', 'facts', 'tips']
current_niche = niches[len(videos_posted) % len(niches)]
content = self.content_gen.generate_content(current_niche)
```

## Performance Tips

1. **GPU Acceleration**: Install moviepy with GPU support for faster rendering
2. **Parallel Processing**: Create multiple videos concurrently
3. **Caching**: Cache TTS audio for repeated phrases
4. **Batch API Calls**: Generate multiple scripts in one API call

## Monitoring

Track your bot's performance:

```bash
# Check output folder
ls -lh output/

# Monitor logs
tail -f bot.log

# Check API usage
# OpenAI: https://platform.openai.com/usage
# YouTube: https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas
```
