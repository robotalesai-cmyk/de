"""Upload module for posting videos to TikTok and YouTube."""

import os
import json
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

class VideoUploader:
    """Handles uploading videos to social media platforms."""
    
    def __init__(self):
        """Initialize the uploader."""
        self.youtube_credentials = None
        self.youtube_service = None
    
    def upload_to_all_platforms(self, video_path, content):
        """
        Upload video to all configured platforms.
        
        Args:
            video_path: Path to video file
            content: Content dictionary with metadata
            
        Returns:
            dict: Results for each platform
        """
        results = {}
        
        # YouTube upload
        try:
            youtube_result = self.upload_to_youtube(video_path, content)
            results['YouTube'] = youtube_result
        except Exception as e:
            results['YouTube'] = {'success': False, 'error': str(e)}
        
        # TikTok upload (requires manual authentication or browser automation)
        try:
            tiktok_result = self.upload_to_tiktok(video_path, content)
            results['TikTok'] = tiktok_result
        except Exception as e:
            results['TikTok'] = {'success': False, 'error': str(e)}
        
        return results
    
    def upload_to_youtube(self, video_path, content):
        """
        Upload video to YouTube Shorts.
        
        Args:
            video_path: Path to video file
            content: Content dictionary
            
        Returns:
            dict: Upload result
        """
        # Initialize YouTube API
        if not self.youtube_service:
            self._init_youtube_api()
        
        # Prepare video metadata
        title = content['title']
        description = f"{content['description']}\n\n{content['hashtags']}\n\n#Shorts"
        
        # Create request body
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': self._extract_tags(content['hashtags']),
                'categoryId': '22'  # People & Blogs
            },
            'status': {
                'privacyStatus': 'public',
                'selfDeclaredMadeForKids': False
            }
        }
        
        # Upload video
        media = MediaFileUpload(
            video_path,
            mimetype='video/mp4',
            resumable=True,
            chunksize=1024*1024
        )
        
        request = self.youtube_service.videos().insert(
            part='snippet,status',
            body=body,
            media_body=media
        )
        
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"Uploaded {int(status.progress() * 100)}%")
        
        video_id = response['id']
        video_url = f"https://www.youtube.com/shorts/{video_id}"
        
        return {
            'success': True,
            'url': video_url,
            'video_id': video_id
        }
    
    def upload_to_tiktok(self, video_path, content):
        """
        Upload video to TikTok.
        
        Note: TikTok doesn't have a stable public API for uploads.
        This requires browser automation or unofficial APIs.
        
        Args:
            video_path: Path to video file
            content: Content dictionary
            
        Returns:
            dict: Upload result
        """
        # Check if TikTok session is configured
        session_id = os.getenv('TIKTOK_SESSION_ID')
        
        if not session_id:
            return {
                'success': False,
                'error': 'TikTok session ID not configured. Manual upload required.'
            }
        
        # For production, you would use:
        # 1. Unofficial TikTok API (TikTokApi package)
        # 2. Browser automation (Selenium/Playwright)
        # 3. Third-party services
        
        # Placeholder for TikTok upload
        caption = f"{content['title']}\n\n{content['hashtags']}"
        
        return {
            'success': False,
            'error': 'TikTok upload requires manual authentication. Use browser automation or upload manually.',
            'caption': caption,
            'video_path': video_path
        }
    
    def _init_youtube_api(self):
        """Initialize YouTube API with OAuth2."""
        SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
        
        creds = None
        token_path = Path('token.json')
        
        # Load existing credentials
        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        
        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # Need client_secret.json for OAuth flow
                client_secret = Path('client_secret.json')
                if not client_secret.exists():
                    raise FileNotFoundError(
                        "client_secret.json not found. Download from Google Cloud Console."
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(client_secret), SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Save credentials
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
        
        self.youtube_credentials = creds
        self.youtube_service = build('youtube', 'v3', credentials=creds)
    
    def _extract_tags(self, hashtags):
        """Extract tags from hashtag string."""
        tags = []
        for tag in hashtags.split():
            if tag.startswith('#'):
                tags.append(tag[1:])  # Remove # symbol
        return tags[:15]  # YouTube allows max 15 tags
