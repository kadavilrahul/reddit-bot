"""
Configuration module for Reddit Bot
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for Reddit Bot"""
    
    # Reddit API Configuration
    REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
    REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
    REDDIT_USERNAME = os.getenv('REDDIT_USERNAME')
    REDDIT_PASSWORD = os.getenv('REDDIT_PASSWORD')
    REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT', 'ScraperBot')
    
    # Google Gemini Configuration
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    GEMINI_ENDPOINT = os.getenv('GEMINI_ENDPOINT', 'https://generativelanguage.googleapis.com/v1beta/models/')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash-exp')
    
    # Bot Configuration
    MAX_COMMENT_LENGTH = 10000
    MAX_POSTS_PER_REQUEST = 100
    RATE_LIMIT_DELAY = 2  # seconds between requests
    
    # Validation settings
    MIN_COMMENT_LENGTH = 10
    MAX_RETRIES = 3
    
    @classmethod
    def validate_config(cls):
        """Validate that all required configuration is present"""
        required_vars = [
            'REDDIT_CLIENT_ID',
            'REDDIT_CLIENT_SECRET', 
            'REDDIT_USERNAME',
            'REDDIT_PASSWORD',
            'GEMINI_API_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True