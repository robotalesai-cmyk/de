# Troubleshooting Guide

Common issues and solutions for the Automated Viral Video Bot.

## Installation Issues

### Python Version Error
**Error:** `SyntaxError` or features not available

**Solution:**
```bash
# Check Python version (need 3.8+)
python3 --version

# Install Python 3.8+ if needed
# Ubuntu/Debian:
sudo apt-get install python3.10

# macOS:
brew install python@3.10
```

### FFmpeg Not Found
**Error:** `FileNotFoundError: [Errno 2] No such file or directory: 'ffmpeg'`

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Verify installation
ffmpeg -version
```

### Pip Install Fails
**Error:** Various package installation errors

**Solution:**
```bash
# Upgrade pip first
pip install --upgrade pip

# Try installing with verbose output
pip install -r requirements.txt -v

# If specific package fails, install separately
pip install moviepy
pip install openai
```

## Configuration Issues

### OpenAI API Key Not Found
**Error:** `ValueError: OPENAI_API_KEY not found in environment variables`

**Solution:**
1. Check `.env` file exists: `ls -la .env`
2. Open `.env` and verify key is set:
   ```
   OPENAI_API_KEY=sk-proj-xxxxx
   ```
3. No spaces around `=`
4. No quotes needed around the key
5. Key must start with `sk-`

### Invalid API Key
**Error:** `AuthenticationError` or `401 Unauthorized`

**Solution:**
1. Verify key at https://platform.openai.com/api-keys
2. Check if key has been revoked
3. Ensure account has credits
4. Generate new key if needed

### Environment Variables Not Loading
**Error:** Variables from `.env` not being read

**Solution:**
```bash
# Check file name (must be exactly .env)
ls -la | grep env

# Verify file content
cat .env

# Try loading manually
export OPENAI_API_KEY=your_key
python main.py
```

## Video Creation Issues

### MoviePy Import Error
**Error:** `ImportError: cannot import name 'AudioFileClip'`

**Solution:**
```bash
# Reinstall moviepy with dependencies
pip uninstall moviepy
pip install moviepy==1.0.3

# Also ensure imageio-ffmpeg is installed
pip install imageio-ffmpeg
```

### Text Rendering Error
**Error:** `OSError: cannot open resource` or font not found

**Solution:**
```bash
# Install fonts
# Ubuntu/Debian:
sudo apt-get install fonts-liberation

# macOS: (usually has Arial)
# Or use system fonts

# In video_creator.py, change font to one that exists:
font='Arial'  # or 'DejaVu-Sans' on Linux
```

### Audio Generation Fails
**Error:** gTTS errors or audio file not created

**Solution:**
```bash
# Check internet connection (gTTS needs internet)
ping google.com

# Try reinstalling gTTS
pip uninstall gtts
pip install gtts

# Alternative: Use offline TTS
# Install pyttsx3: pip install pyttsx3
```

### Video Rendering Too Slow
**Issue:** Video creation takes very long

**Solution:**
1. Reduce video quality/resolution temporarily
2. Use fewer text overlays
3. Shorter videos (15-20 seconds)
4. Close other applications
5. Consider cloud rendering

## Upload Issues

### YouTube Authentication Fails
**Error:** `FileNotFoundError: client_secret.json not found`

**Solution:**
1. Download OAuth credentials from Google Cloud Console
2. Rename to exactly `client_secret.json`
3. Place in project root directory
4. Verify file exists: `ls -la client_secret.json`

### YouTube API Quota Exceeded
**Error:** `HttpError 403: quotaExceeded`

**Solution:**
1. Check quota usage: https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas
2. Free tier: 10,000 units/day
3. One upload ≈ 1,600 units
4. Can upload ~6 videos/day free
5. Request quota increase if needed

### YouTube Upload Fails
**Error:** Various upload errors

**Solution:**
```bash
# Delete old token and re-authenticate
rm token.json
python main.py

# Check video file isn't corrupted
ffmpeg -v error -i output/video.mp4 -f null -

# Verify video meets YouTube requirements:
# - Size: < 256 GB
# - Duration: < 12 hours
# - Format: MP4
```

### TikTok Upload Not Working
**Issue:** TikTok upload returns error

**Solution:**
- TikTok doesn't have official upload API
- Options:
  1. Manual upload using generated caption
  2. Browser automation (Selenium/Playwright)
  3. Third-party services (e.g., Pigeon)
- Bot generates video ready for manual upload

## Runtime Issues

### Script Generation Fails
**Error:** OpenAI API errors or timeout

**Solution:**
```bash
# Check API status
curl https://status.openai.com

# Verify account credits
# https://platform.openai.com/account/billing

# Try with longer timeout
# In content_generator.py, add:
# timeout=60

# Try GPT-3.5 instead (cheaper, faster)
# Change model="gpt-3.5-turbo"
```

### Memory Error During Video Creation
**Error:** `MemoryError` or system runs out of RAM

**Solution:**
1. Reduce video resolution
2. Process fewer text chunks at once
3. Close other applications
4. Increase system swap space
5. Use cloud VM with more RAM

### Scheduler Stops Running
**Issue:** Scheduled jobs don't execute

**Solution:**
```bash
# Check schedule format in .env
POST_SCHEDULE=09:00,15:00,21:00

# Verify system time
date

# Ensure bot keeps running
# Use screen or tmux for persistent sessions:
screen -S videobot
python main.py
# Ctrl+A, D to detach

# Or use systemd service (Linux)
```

## Performance Issues

### Slow Content Generation
**Issue:** GPT-4 responses take too long

**Solution:**
1. Use GPT-3.5-turbo instead (faster, cheaper)
2. Reduce max_tokens parameter
3. Lower temperature for faster responses
4. Cache common script templates

### Video Processing Slow
**Issue:** Video creation takes >5 minutes

**Solution:**
1. Use lower FPS (24 instead of 30)
2. Reduce text chunk size
3. Use simpler backgrounds
4. Optimize MoviePy settings
5. Consider GPU acceleration

## Debugging

### Enable Verbose Logging
```python
# Add to main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Test Individual Components
```bash
# Test content generation
python -c "
from src.content_generator import ContentGenerator
import os
os.environ['OPENAI_API_KEY']='your_key'
gen = ContentGenerator()
print(gen._generate_hashtags('motivational'))
"

# Test video creator
python -c "
from src.video_creator import VideoCreator
from pathlib import Path
vc = VideoCreator(Path('./output'))
print(vc._get_random_gradient_color())
"

# Or use the demo script for comprehensive testing
python demo.py
```

### Check Dependencies
```bash
# List installed packages
pip list

# Verify critical packages
python -c "import openai; import moviepy; import gtts; print('All imports OK')"
```

## Getting Help

If you're still stuck:

1. **Check logs:** Look for error messages in console output
2. **Verify environment:** Run demo: `python demo.py`
3. **Test components:** Run unit tests: `python -m pytest tests/ -v`
4. **Search issues:** Check GitHub issues for similar problems
5. **Ask for help:** Open new issue with:
   - Error message
   - Python version
   - OS and version
   - Steps to reproduce

## Prevention Tips

1. **Keep dependencies updated:** `pip install --upgrade -r requirements.txt`
2. **Monitor API usage:** Check OpenAI and YouTube quotas regularly
3. **Backup configuration:** Keep `.env` file backed up (securely)
4. **Test before scheduling:** Always test with single video first
5. **Version control:** Use git to track changes to code

## Common Gotchas

- `.env` file must be in project root, not in `src/`
- FFmpeg must be in system PATH
- YouTube requires OAuth, not just API key
- TikTok has no official upload API
- OpenAI API keys start with `sk-`
- Video files can be large (10-50 MB each)
- API rate limits apply (don't spam requests)

## Still Having Issues?

Open an issue on GitHub with:
- Exact error message
- Your setup (OS, Python version)
- Steps you've tried
- Relevant log output

We're here to help! 🚀
