"""
Validation module using agno agent for Reddit Bot
"""
from agno.agent import Agent
from agno.models.google.gemini import Gemini
from config import Config
import logging
import re

logger = logging.getLogger(__name__)

class RedditValidator:
    """Validator class using agno agent for Reddit content validation"""
    
    def __init__(self):
        """Initialize the validator with Gemini model and agno agent"""
        try:
            self.model = Gemini(
                id="gemini-2.0-flash-exp",
                api_key=Config.GEMINI_API_KEY
            )
            
            self.validation_agent = Agent(
                name="Reddit Content Validator",
                role="Content Validator",
                model=self.model,
                instructions="Validate Reddit content. Return 'VALID' if appropriate, 'INVALID: [reason]' if not. Check for spam, harassment, relevance, and Reddit policy violations."
            )
            
            self.comment_generator_agent = Agent(
                name="Reddit Comment Generator",
                role="Comment Generator",
                model=self.model,
                instructions="Generate thoughtful, relevant Reddit comments (50-200 words). Match subreddit tone, add value, avoid repetition, follow Reddit etiquette."
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize validator: {e}")
            raise
    
    def validate_comment(self, comment_text: str, post_context: str = "") -> tuple[bool, str]:
        """Validate a comment using the agno agent"""
        try:
            if len(comment_text.strip()) < Config.MIN_COMMENT_LENGTH:
                return False, f"Comment too short (minimum {Config.MIN_COMMENT_LENGTH} characters)"
            
            if len(comment_text) > Config.MAX_COMMENT_LENGTH:
                return False, f"Comment too long (maximum {Config.MAX_COMMENT_LENGTH} characters)"
            
            validation_prompt = f"Validate this Reddit comment:\nPOST CONTEXT: {post_context[:500] if post_context else 'No context'}\nCOMMENT: {comment_text}"
            
            response = self.validation_agent.run(validation_prompt)
            result = response.content.strip()
            
            if result.startswith("VALID"):
                return True, "Comment is valid"
            elif result.startswith("INVALID"):
                return False, result.replace("INVALID:", "").strip()
            else:
                return "valid" in result.lower(), "Content validation completed"
                    
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False, f"Validation error: {str(e)}"
    
    def generate_comment(self, post_title: str, post_content: str, subreddit: str, 
                        existing_comments: list = None) -> str:
        """Generate a relevant comment using the agno agent"""
        try:
            existing_text = ""
            if existing_comments:
                existing_text = "\n".join([f"- {comment[:100]}..." for comment in existing_comments[:3]])
            
            prompt = f"Generate a Reddit comment for:\nSUBREDDIT: r/{subreddit}\nTITLE: {post_title}\nCONTENT: {post_content[:500] if post_content else 'No content'}\nEXISTING COMMENTS:\n{existing_text}"
            
            response = self.comment_generator_agent.run(prompt)
            generated_comment = response.content.strip()
            
            # Clean up response
            lines = [line.strip() for line in generated_comment.split('\n') 
                    if line.strip() and not line.startswith(('Here', 'This comment', 'I generated'))]
            
            return '\n'.join(lines) if lines else generated_comment
            
        except Exception as e:
            logger.error(f"Comment generation error: {e}")
            return f"Error generating comment: {str(e)}"
    
    def validate_subreddit_name(self, subreddit: str) -> tuple[bool, str]:
        """Validate subreddit name format"""
        if not subreddit:
            return False, "Subreddit name cannot be empty"
        
        subreddit = subreddit.replace('r/', '').replace('R/', '')
        
        if not re.match(r'^[A-Za-z0-9_]{3,21}$', subreddit):
            return False, "Invalid subreddit name format"
        
        return True, subreddit
    
    def validate_post_data(self, post_data: dict) -> tuple[bool, str]:
        """Validate post data structure"""
        required_fields = ['title', 'id']
        
        for field in required_fields:
            if field not in post_data:
                return False, f"Missing required field: {field}"
        
        if not post_data['title'].strip():
            return False, "Post title cannot be empty"
        
        return True, "Post data is valid"