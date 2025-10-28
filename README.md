# Automated Viral Video Bot for TikTok & YouTube

🤖 A fully automated bot that generates, creates, and posts viral short-form videos to TikTok and YouTube Shorts using AI.

## Features

- 🎯 **AI-Powered Content Generation** - Uses OpenAI GPT-4 to create engaging viral scripts
- 🎬 **Automated Video Creation** - Generates professional videos with text overlays and voiceovers
- 📤 **Multi-Platform Upload** - Automatically posts to YouTube Shorts (TikTok requires manual setup)
- 📅 **Scheduling System** - Schedule automatic posts throughout the day
- 🎨 **Multiple Content Niches** - Supports motivational, facts, stories, tips, and comedy content
- ⚡ **Optimized for Virality** - Hooks, captions, and hashtags designed for maximum engagement

## Quick Start

### Prerequisites

- Python 3.8 or higher
- OpenAI API key
- Google Cloud project with YouTube Data API enabled
- FFmpeg installed on your system

### Installation

1. Clone the repository:
```bash
git clone https://github.com/robotalesai-cmyk/de.git
cd de
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install FFmpeg (if not already installed):
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and settings
```

### Configuration

#### OpenAI API Key
1. Get your API key from [OpenAI Platform](https://platform.openai.com/)
2. Add to `.env`: `OPENAI_API_KEY=your_key_here`

#### YouTube Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable YouTube Data API v3
4. Create OAuth 2.0 credentials (Desktop app)
5. Download `client_secret.json` to the project root
6. On first run, authenticate via browser

#### TikTok Setup (Manual)
TikTok doesn't have a stable public API. Options:
- Use browser automation (Selenium/Playwright)
- Upload manually using the provided caption and hashtags
- Use third-party services

### Usage

#### Single Video Mode
Create and post one video immediately:
```bash
python main.py
```

#### Scheduled Mode
Run the bot with automatic scheduling:
```bash
# Edit .env and set:
# AUTO_POST_ENABLED=true
# POST_SCHEDULE=09:00,15:00,21:00

python main.py
```

### Content Niches

Set `CONTENT_NICHE` in `.env` to one of:
- `motivational` - Motivational quotes and success stories
- `facts` - Interesting and viral facts
- `story` - Engaging short stories
- `tips` - Life hacks and useful tips
- `comedy` - Funny jokes and observations

### Environment Variables

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# YouTube API Configuration
YOUTUBE_CLIENT_ID=your_youtube_client_id
YOUTUBE_CLIENT_SECRET=your_youtube_client_secret
YOUTUBE_CHANNEL_ID=your_channel_id

# TikTok Configuration
TIKTOK_SESSION_ID=your_tiktok_session_id
TIKTOK_USERNAME=your_tiktok_username

# Content Settings
VIDEO_DURATION=30              # Video length in seconds
CONTENT_NICHE=motivational     # Content type
OUTPUT_FOLDER=./output         # Where to save videos

# Scheduling
AUTO_POST_ENABLED=false        # Enable automatic scheduling
POST_SCHEDULE=09:00,15:00,21:00  # Times to post (24-hour format)
```

## Project Structure

```
de/
├── main.py                  # Main entry point
├── src/
│   ├── content_generator.py # AI content generation
│   ├── video_creator.py     # Video creation and editing
│   ├── uploader.py         # Platform upload handlers
│   └── scheduler.py        # Scheduling system
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## How It Works

1. **Content Generation**: Uses GPT-4 to generate viral scripts with hooks, engaging content, and CTAs
2. **Script to Speech**: Converts text to natural speech using Google TTS
3. **Video Creation**: Creates vertical videos (1080x1920) with animated text overlays
4. **Optimization**: Adds viral elements (hooks, hashtags, captions)
5. **Upload**: Posts to YouTube Shorts automatically (TikTok requires manual steps)

## API Costs

- **OpenAI GPT-4**: ~$0.03-0.06 per video (script + title generation)
- **Google TTS**: Free (included in gtts library)
- **YouTube API**: Free (quota limits apply)

Estimated cost: **~$1-2 per day** for 30-50 videos/month

## Limitations

- TikTok upload requires manual authentication or browser automation
- YouTube API has daily quota limits
- Video quality depends on AI-generated scripts
- Requires active OpenAI API subscription

## Tips for Viral Success

1. **Post Consistently**: 2-3 times daily for best results
2. **Engage with Comments**: Respond to comments on your videos
3. **Analyze Performance**: Track which niches perform best
4. **Optimize Timing**: Post when your audience is most active
5. **Mix Content**: Vary between niches to find what works

## Troubleshooting

### Video creation fails
- Ensure FFmpeg is installed: `ffmpeg -version`
- Check that output directory exists and is writable

### YouTube upload fails
- Verify `client_secret.json` is present
- Check YouTube API quota limits
- Ensure OAuth token is valid (delete `token.json` and re-authenticate)

### AI generation fails
- Verify OpenAI API key is valid
- Check account has available credits
- Try reducing VIDEO_DURATION if hitting token limits

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - See LICENSE file for details

## Disclaimer

This bot is for educational purposes. Ensure you comply with:
- Platform terms of service
- Content guidelines
- Copyright laws
- API usage policies

Use responsibly and create original, valuable content.
