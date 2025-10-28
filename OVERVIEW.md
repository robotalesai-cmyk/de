# Project Overview

## Automated Viral Video Bot for TikTok & YouTube

A comprehensive, production-ready Python application that automatically generates, creates, and posts viral short-form videos to social media platforms.

## Architecture

### High-Level Flow
```
User Configuration (.env)
         ↓
    Main Entry (main.py)
         ↓
    ┌────────────────────────────────┐
    │   Content Generator (AI)       │
    │   - GPT-4 script generation    │
    │   - Hook extraction            │
    │   - Title & hashtag creation   │
    └────────────┬───────────────────┘
                 ↓
    ┌────────────────────────────────┐
    │   Video Creator (MoviePy)      │
    │   - Text-to-speech audio       │
    │   - Video composition          │
    │   - Text overlays              │
    │   - Background generation      │
    └────────────┬───────────────────┘
                 ↓
    ┌────────────────────────────────┐
    │   Uploader (APIs)              │
    │   - YouTube OAuth2 upload      │
    │   - TikTok (manual/automated)  │
    │   - Metadata optimization      │
    └────────────┬───────────────────┘
                 ↓
            Published Video
```

### Component Architecture

#### 1. Content Generator (`src/content_generator.py`)
- **Purpose:** Generate viral video scripts using AI
- **Key Methods:**
  - `generate_content(niche)` - Main generation method
  - `_generate_script()` - Creates viral script with OpenAI
  - `_extract_hook()` - Identifies attention-grabbing opening
  - `_generate_title()` - Creates clickbait-style titles
  - `_generate_hashtags()` - Produces relevant hashtags
- **Dependencies:** OpenAI API
- **Output:** Content dictionary with script, title, hashtags, etc.

#### 2. Video Creator (`src/video_creator.py`)
- **Purpose:** Convert scripts into polished videos
- **Key Methods:**
  - `create_video(content)` - Main video creation pipeline
  - `_generate_audio()` - Text-to-speech conversion
  - `_create_background()` - Generate gradient backgrounds
  - `_add_text_overlays()` - Add animated text
- **Dependencies:** MoviePy, Google TTS, FFmpeg
- **Output:** MP4 video file (1080x1920)

#### 3. Uploader (`src/uploader.py`)
- **Purpose:** Post videos to social platforms
- **Key Methods:**
  - `upload_to_all_platforms()` - Upload to all configured platforms
  - `upload_to_youtube()` - YouTube Shorts upload via API
  - `upload_to_tiktok()` - TikTok upload (requires setup)
  - `_init_youtube_api()` - OAuth2 authentication
- **Dependencies:** Google API Client, OAuth2
- **Output:** Upload results with URLs

#### 4. Scheduler (`src/scheduler.py`)
- **Purpose:** Automate video posting throughout the day
- **Key Methods:**
  - `start()` - Begin scheduled operation
  - `create_and_post_video()` - Complete pipeline execution
- **Dependencies:** schedule library
- **Output:** Continuous operation with scheduled posts

#### 5. Configuration (`src/config.py`)
- **Purpose:** Centralized settings management
- **Key Attributes:**
  - API keys and credentials
  - Video settings (dimensions, FPS, duration)
  - Content preferences
  - Scheduling configuration
- **Dependencies:** python-dotenv
- **Output:** Validated configuration

### Data Flow

1. **Input:** User configuration (`.env` file)
2. **Content Generation:**
   - AI generates script based on niche
   - Extract hook (first 3 seconds)
   - Create title and hashtags
3. **Video Creation:**
   - Convert script to speech (MP3)
   - Create video background
   - Add animated text overlays
   - Combine audio and video
4. **Upload:**
   - Authenticate with platforms
   - Upload video with metadata
   - Return video URLs
5. **Output:** Published videos on social media

## Technology Stack

### Core Technologies
- **Python 3.8+:** Main programming language
- **OpenAI GPT-4:** AI content generation
- **MoviePy:** Video editing and composition
- **FFmpeg:** Video processing backend
- **Google TTS:** Text-to-speech conversion
- **YouTube Data API v3:** Automated uploads
- **Schedule:** Task scheduling

### Key Libraries
```
openai>=1.0.0              # AI content generation
moviepy>=1.0.3             # Video editing
Pillow>=10.0.0             # Image processing
opencv-python>=4.8.0       # Computer vision
google-api-python-client   # YouTube API
gtts>=2.4.0               # Text-to-speech
schedule>=1.2.0           # Task scheduling
python-dotenv>=1.0.0      # Configuration
```

## File Structure

```
de/
├── main.py                    # Application entry point
├── demo.py                    # Demo without API calls
├── setup.sh                   # Setup automation script
├── requirements.txt           # Python dependencies
├── .env.example              # Configuration template
├── .gitignore                # Git ignore rules
├── LICENSE                   # MIT License
│
├── Documentation/
│   ├── README.md             # Complete documentation
│   ├── QUICKSTART.md         # 5-minute setup guide
│   ├── EXAMPLES.md           # Code examples
│   └── TROUBLESHOOTING.md    # Problem solutions
│
├── src/                      # Source code
│   ├── __init__.py
│   ├── content_generator.py  # AI content generation
│   ├── video_creator.py      # Video creation
│   ├── uploader.py          # Platform uploads
│   ├── scheduler.py         # Automation
│   └── config.py            # Configuration
│
└── tests/                    # Test suite
    ├── __init__.py
    └── test_bot.py          # Unit tests
```

## Configuration

### Environment Variables
```bash
# Required
OPENAI_API_KEY=sk-...         # OpenAI API access

# Optional
VIDEO_DURATION=30             # Video length (seconds)
CONTENT_NICHE=motivational    # Content type
OUTPUT_FOLDER=./output        # Save location
AUTO_POST_ENABLED=false       # Enable scheduler
POST_SCHEDULE=09:00,15:00     # Post times
```

### Content Niches
- **motivational:** Success quotes and inspiration
- **facts:** Interesting viral facts
- **story:** Short engaging narratives
- **tips:** Life hacks and tutorials
- **comedy:** Jokes and humor

## Workflow Modes

### 1. Single Video Mode (Default)
```bash
python main.py
```
- Generates one video immediately
- Saves to output directory
- Attempts platform upload
- Exits when complete

### 2. Scheduled Mode
```bash
# Set in .env:
# AUTO_POST_ENABLED=true
# POST_SCHEDULE=09:00,15:00,21:00

python main.py
```
- Runs continuously
- Posts at scheduled times
- Automatically generates new content
- Logs all activities

## API Usage & Costs

### OpenAI API
- **Cost per video:** ~$0.03-0.06
- **Usage:** Script + title generation
- **Rate limits:** 3 requests/minute (tier 1)

### YouTube API
- **Cost:** Free
- **Quota:** 10,000 units/day
- **Upload cost:** ~1,600 units
- **Capacity:** ~6 videos/day (free tier)

### Google TTS
- **Cost:** Free (via gtts library)
- **Usage:** Unlimited
- **Quality:** Good for short-form content

### Estimated Daily Costs
- 3 videos/day: ~$0.15-0.20
- 10 videos/day: ~$0.50-0.60
- 30 videos/month: ~$1.50-2.00

## Security Considerations

1. **API Key Protection:**
   - Store in `.env` file (not committed)
   - Never hardcode credentials
   - Use environment variables

2. **OAuth2 Tokens:**
   - Stored in `token.json` (gitignored)
   - Auto-refresh on expiration
   - Secure storage required

3. **Input Validation:**
   - Sanitize user inputs
   - Validate configuration
   - Handle API errors gracefully

4. **Rate Limiting:**
   - Respect API quotas
   - Implement backoff strategies
   - Monitor usage

## Performance Optimization

### Video Creation (~2-4 minutes per video)
- Script generation: 5-10 seconds
- Audio synthesis: 5-10 seconds
- Video rendering: 1-3 minutes
- Upload: 30-60 seconds

### Bottlenecks
1. **MoviePy rendering:** CPU-intensive
2. **OpenAI API:** Network latency
3. **YouTube upload:** Large file transfer

### Optimization Tips
- Use GPT-3.5-turbo for faster generation
- Lower video FPS (24 instead of 30)
- Parallel video processing
- GPU acceleration for rendering

## Scalability

### Current Limitations
- Single-threaded video creation
- Sequential API calls
- Local file storage

### Scaling Strategies
1. **Horizontal:** Multiple instances with different accounts
2. **Batch Processing:** Queue system for videos
3. **Cloud Deployment:** AWS/GCP for rendering
4. **CDN Storage:** S3/GCS for video files
5. **Database:** Track published content

## Monitoring & Analytics

### Metrics to Track
- Videos created per day
- Upload success rate
- API costs
- Processing time per video
- Views and engagement (manual)

### Logging
- Application logs in console
- Error tracking
- API usage logs
- Performance metrics

## Future Enhancements

### Potential Features
- [ ] TikTok automated upload
- [ ] Instagram Reels support
- [ ] Multiple video styles/templates
- [ ] Voice cloning for custom voices
- [ ] A/B testing for content
- [ ] Analytics dashboard
- [ ] Web UI for management
- [ ] Database for content tracking
- [ ] Custom background videos
- [ ] Music/sound effects

### Technical Improvements
- [ ] Async video processing
- [ ] Queue-based architecture
- [ ] Redis for caching
- [ ] Docker containerization
- [ ] CI/CD pipeline
- [ ] Comprehensive test coverage
- [ ] Performance profiling
- [ ] Cloud deployment guide

## Maintenance

### Regular Tasks
- Monitor API usage and costs
- Update dependencies
- Review generated content quality
- Analyze video performance
- Backup configurations
- Rotate API keys periodically

### Troubleshooting
- Check logs for errors
- Verify API quotas
- Test individual components
- Run demo script
- Review troubleshooting guide

## Support & Community

### Getting Help
1. Check documentation (README, QUICKSTART, TROUBLESHOOTING)
2. Run demo script for validation
3. Review examples for guidance
4. Open GitHub issue with details
5. Join community discussions

### Contributing
- Report bugs
- Suggest features
- Submit pull requests
- Improve documentation
- Share success stories

## License

MIT License - Free for commercial and personal use

---

**Built with ❤️ for content creators who want to automate viral video production**
