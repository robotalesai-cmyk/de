"""Content generation module using AI."""

import os
import random
from openai import OpenAI

class ContentGenerator:
    """Generates viral video scripts and metadata using AI."""
    
    def __init__(self):
        """Initialize the content generator."""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = OpenAI(api_key=api_key)
        self.niches = {
            'motivational': 'motivational quotes and success stories',
            'facts': 'interesting and viral facts',
            'story': 'engaging short stories',
            'tips': 'life hacks and useful tips',
            'comedy': 'funny jokes and observations'
        }
    
    def generate_content(self, niche=None):
        """
        Generate video content including script, hook, and metadata.
        
        Args:
            niche: Content niche (motivational, facts, story, tips, comedy)
            
        Returns:
            dict: Content dictionary with script, hook, title, hashtags, etc.
        """
        if niche is None:
            niche = os.getenv('CONTENT_NICHE', 'motivational')
        
        niche_description = self.niches.get(niche, self.niches['motivational'])
        
        # Generate script
        script = self._generate_script(niche_description)
        
        # Generate hook (first 3 seconds)
        hook = self._extract_hook(script)
        
        # Generate metadata
        title = self._generate_title(script, niche)
        description = self._generate_description(script, niche)
        hashtags = self._generate_hashtags(niche)
        
        return {
            'script': script,
            'hook': hook,
            'title': title,
            'description': description,
            'hashtags': hashtags,
            'niche': niche
        }
    
    def _generate_script(self, niche_description):
        """Generate a viral video script."""
        duration = int(os.getenv('VIDEO_DURATION', 30))
        
        prompt = f"""Create a {duration}-second viral video script for TikTok/YouTube Shorts about {niche_description}.

Requirements:
- Hook viewers in the first 3 seconds
- Keep it engaging and concise
- Use simple, conversational language
- Include emotional appeal
- End with a call-to-action or cliffhanger
- Length: approximately {duration * 2.5} words (for natural speech)

Write ONLY the script, no additional commentary."""

        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a viral content creator specialized in short-form video content."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.9,
            max_tokens=500
        )
        
        return response.choices[0].message.content.strip()
    
    def _extract_hook(self, script):
        """Extract the hook (first sentence or first 10 words)."""
        sentences = script.split('.')
        hook = sentences[0].strip()
        
        # Ensure hook is not too long
        words = hook.split()
        if len(words) > 12:
            hook = ' '.join(words[:12]) + '...'
        
        return hook
    
    def _generate_title(self, script, niche):
        """Generate an engaging title."""
        prompt = f"""Based on this video script, create a catchy, clickbait-style title (max 60 characters):

Script: {script[:200]}...

Write ONLY the title, nothing else."""

        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a social media expert creating viral titles."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=50
        )
        
        title = response.choices[0].message.content.strip().strip('"\'')
        return title[:100]  # Limit title length
    
    def _generate_description(self, script, niche):
        """Generate a video description."""
        base_description = script[:150] + "..."
        cta = "\n\n👉 Follow for more viral content!\n💬 Comment your thoughts below\n❤️ Like and share if you enjoyed!"
        
        return base_description + cta
    
    def _generate_hashtags(self, niche):
        """Generate relevant hashtags."""
        base_hashtags = ['#fyp', '#viral', '#foryou', '#trending']
        
        niche_hashtags = {
            'motivational': ['#motivation', '#success', '#mindset', '#goals', '#inspiration'],
            'facts': ['#facts', '#didyouknow', '#interesting', '#learn', '#knowledge'],
            'story': ['#story', '#storytime', '#storytelling', '#narrative'],
            'tips': ['#tips', '#lifehacks', '#howto', '#tutorial', '#useful'],
            'comedy': ['#funny', '#comedy', '#humor', '#laugh', '#meme']
        }
        
        specific_hashtags = niche_hashtags.get(niche, niche_hashtags['motivational'])
        
        # Combine and return
        all_hashtags = base_hashtags + specific_hashtags[:3]
        return ' '.join(all_hashtags)
