# Quick Start Guide

Get your automated video bot running in 5 minutes!

## Prerequisites Check

Before starting, ensure you have:
- [ ] Python 3.8+ installed (`python3 --version`)
- [ ] FFmpeg installed (`ffmpeg -version`)
- [ ] OpenAI API account and credits
- [ ] (Optional) Google Cloud project for YouTube

## Step-by-Step Setup

### 1. Install Dependencies

```bash
# Clone the repository
git clone https://github.com/robotalesai-cmyk/de.git
cd de

# Run setup script (Linux/Mac)
chmod +x setup.sh
./setup.sh

# Or manually:
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your OpenAI API key
nano .env  # or use your favorite editor
```

**Minimum required:**
```
OPENAI_API_KEY=sk-your-key-here
```

### 3. Test the Bot

Create your first video:

```bash
python main.py
```

This will:
1. Generate a viral script using AI
2. Create a 30-second video with voiceover
3. Save it to `output/` directory
4. Attempt to upload to YouTube (if configured)

### 4. Check Your Video

```bash
ls -lh output/
# You should see video_*.mp4 and audio_*.mp3 files
```

Open the video file to review it!

## Next Steps

### Set Up YouTube Upload

1. **Create Google Cloud Project:**
   - Go to https://console.cloud.google.com/
   - Click "Select a project" → "New Project"
   - Enter project name (e.g., "viral-video-bot")
   - Click "Create"

2. **Enable YouTube Data API v3:**
   - In your project, go to "APIs & Services" → "Library"
   - Search for "YouTube Data API v3"
   - Click on it and press "Enable"

3. **Configure OAuth Consent Screen:**
   - Go to "APIs & Services" → "OAuth consent screen"
   - Choose "External" user type
   - Fill in required fields:
     - App name: "Viral Video Bot"
     - User support email: your email
     - Developer contact: your email
   - Click "Save and Continue"
   - Skip scopes for now, click "Save and Continue"
   - Add your email as test user
   - Click "Save and Continue"

4. **Create OAuth Credentials:**
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - Choose application type: "Desktop app"
   - Name it: "Video Bot Desktop"
   - Click "Create"
   - Download the JSON file
   - Rename it to `client_secret.json`
   - Place in project root directory

5. **First Upload:**
   ```bash
   python main.py
   ```
   - Browser will open for authentication
   - Sign in with your Google account
   - Allow access to your YouTube channel
   - Token saved for future uploads

### Enable Scheduling

Edit `.env`:
```bash
AUTO_POST_ENABLED=true
POST_SCHEDULE=09:00,15:00,21:00
```

Run scheduler:
```bash
python main.py
# Bot will create and post videos at scheduled times
# Press Ctrl+C to stop
```

### Customize Content

Edit `.env` to change content type:
```bash
CONTENT_NICHE=facts        # or: motivational, story, tips, comedy
VIDEO_DURATION=30          # seconds (15-60 recommended)
```

## Troubleshooting

### "No module named 'openai'"
```bash
pip install -r requirements.txt
```

### "FFmpeg not found"
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg
```

### "OPENAI_API_KEY not found"
Make sure `.env` file exists and contains:
```
OPENAI_API_KEY=your-actual-key
```

### Video creation fails
- Check FFmpeg is installed: `ffmpeg -version`
- Check output directory is writable: `mkdir -p output`
- Check Python has necessary permissions

### YouTube upload fails
- Verify `client_secret.json` exists
- Delete `token.json` and re-authenticate
- Check YouTube API quota (10,000 units/day free)

## Cost Estimation

Per video:
- OpenAI GPT-4: ~$0.03-0.06
- Google TTS: Free
- YouTube upload: Free (quota limited)

**Daily cost for 3 videos: ~$0.15-0.20**

## Production Tips

1. **Start Small:** Create 1-2 videos manually first
2. **Review Generated Content:** Check scripts before posting
3. **Monitor Performance:** Track which niches get views
4. **Engage:** Respond to comments on your videos
5. **Optimize:** Adjust posting times based on analytics

## Getting Help

- Check `EXAMPLES.md` for more use cases
- Review `README.md` for full documentation
- Open an issue on GitHub if you need help

Happy video creating! 🎬✨
