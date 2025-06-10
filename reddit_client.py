"""
Reddit API client module
"""
import praw
import prawcore
import time
import logging
from typing import List, Dict, Optional, Generator
from config import Config
from validators import RedditValidator

logger = logging.getLogger(__name__)

class RedditClient:
    """Reddit API client with validation and safety features"""
    
    def __init__(self):
        """Initialize Reddit client with credentials"""
        try:
            Config.validate_config()
            
            self.reddit = praw.Reddit(
                client_id=Config.REDDIT_CLIENT_ID,
                client_secret=Config.REDDIT_CLIENT_SECRET,
                username=Config.REDDIT_USERNAME,
                password=Config.REDDIT_PASSWORD,
                user_agent=Config.REDDIT_USER_AGENT
            )
            
            # Test authentication
            self.reddit.user.me()
            logger.info(f"Successfully authenticated as {Config.REDDIT_USERNAME}")
            
            # Initialize validator
            self.validator = RedditValidator()
            
        except Exception as e:
            logger.error(f"Failed to initialize Reddit client: {e}")
            raise
    
    def get_subreddit_posts(self, subreddit_name: str, sort_by: str = 'hot', 
                           limit: int = 10, time_filter: str = 'day') -> List[Dict]:
        """
        Retrieve posts from a subreddit
        
        Args:
            subreddit_name: Name of the subreddit
            sort_by: Sort method ('hot', 'new', 'top', 'rising')
            limit: Number of posts to retrieve
            time_filter: Time filter for 'top' sort ('hour', 'day', 'week', 'month', 'year', 'all')
            
        Returns:
            List of post dictionaries
        """
        try:
            # Validate subreddit name
            is_valid, result = self.validator.validate_subreddit_name(subreddit_name)
            if not is_valid:
                raise ValueError(result)
            
            subreddit_name = result
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Get posts based on sort method
            if sort_by == 'hot':
                posts = subreddit.hot(limit=limit)
            elif sort_by == 'new':
                posts = subreddit.new(limit=limit)
            elif sort_by == 'top':
                posts = subreddit.top(time_filter=time_filter, limit=limit)
            elif sort_by == 'rising':
                posts = subreddit.rising(limit=limit)
            else:
                raise ValueError(f"Invalid sort method: {sort_by}")
            
            post_data = []
            for post in posts:
                try:
                    post_info = {
                        'id': post.id,
                        'title': post.title,
                        'author': str(post.author) if post.author else '[deleted]',
                        'score': post.score,
                        'upvote_ratio': post.upvote_ratio,
                        'num_comments': post.num_comments,
                        'created_utc': post.created_utc,
                        'url': post.url,
                        'permalink': f"https://reddit.com{post.permalink}",
                        'selftext': post.selftext,
                        'subreddit': str(post.subreddit),
                        'is_self': post.is_self,
                        'over_18': post.over_18,
                        'spoiler': post.spoiler,
                        'stickied': post.stickied,
                        'locked': post.locked
                    }
                    
                    # Validate post data
                    is_valid, _ = self.validator.validate_post_data(post_info)
                    if is_valid:
                        post_data.append(post_info)
                    
                except Exception as e:
                    logger.warning(f"Error processing post {post.id}: {e}")
                    continue
            
            logger.info(f"Retrieved {len(post_data)} posts from r/{subreddit_name}")
            return post_data
            
        except prawcore.exceptions.Redirect:
            raise ValueError(f"Subreddit r/{subreddit_name} does not exist")
        except prawcore.exceptions.Forbidden:
            raise ValueError(f"Access forbidden to r/{subreddit_name}")
        except Exception as e:
            logger.error(f"Error retrieving posts: {e}")
            raise
    
    def get_post_comments(self, post_id: str, limit: int = 50) -> List[Dict]:
        """
        Get comments from a specific post
        
        Args:
            post_id: Reddit post ID
            limit: Maximum number of comments to retrieve
            
        Returns:
            List of comment dictionaries
        """
        try:
            submission = self.reddit.submission(id=post_id)
            submission.comments.replace_more(limit=0)  # Remove "more comments" objects
            
            comments_data = []
            for comment in submission.comments.list()[:limit]:
                try:
                    if hasattr(comment, 'body') and comment.body != '[deleted]':
                        comment_info = {
                            'id': comment.id,
                            'body': comment.body,
                            'author': str(comment.author) if comment.author else '[deleted]',
                            'score': comment.score,
                            'created_utc': comment.created_utc,
                            'permalink': f"https://reddit.com{comment.permalink}",
                            'parent_id': comment.parent_id,
                            'is_submitter': comment.is_submitter,
                            'stickied': comment.stickied,
                            'depth': comment.depth
                        }
                        comments_data.append(comment_info)
                        
                except Exception as e:
                    logger.warning(f"Error processing comment: {e}")
                    continue
            
            logger.info(f"Retrieved {len(comments_data)} comments from post {post_id}")
            return comments_data
            
        except Exception as e:
            logger.error(f"Error retrieving comments: {e}")
            raise
    
    def post_comment(self, post_id: str, comment_text: str, validate: bool = True) -> Dict:
        """
        Post a comment to a Reddit post
        
        Args:
            post_id: Reddit post ID
            comment_text: Comment text to post
            validate: Whether to validate comment before posting
            
        Returns:
            Dictionary with comment posting result
        """
        try:
            # Get post context for validation
            submission = self.reddit.submission(id=post_id)
            post_context = f"{submission.title}\n{submission.selftext}"
            
            # Validate comment if requested
            if validate:
                is_valid, reason = self.validator.validate_comment(comment_text, post_context)
                if not is_valid:
                    return {
                        'success': False,
                        'error': f"Comment validation failed: {reason}",
                        'comment_id': None
                    }
            
            # Check if post allows comments
            if submission.locked:
                return {
                    'success': False,
                    'error': "Post is locked and does not allow comments",
                    'comment_id': None
                }
            
            # Post the comment
            comment = submission.reply(comment_text)
            
            # Rate limiting
            time.sleep(Config.RATE_LIMIT_DELAY)
            
            logger.info(f"Successfully posted comment {comment.id} to post {post_id}")
            
            return {
                'success': True,
                'comment_id': comment.id,
                'permalink': f"https://reddit.com{comment.permalink}",
                'error': None
            }
            
        except prawcore.exceptions.Forbidden as e:
            error_msg = "Forbidden: You may be banned from this subreddit or lack permissions"
            logger.error(f"Comment posting forbidden: {e}")
            return {'success': False, 'error': error_msg, 'comment_id': None}
            
        except prawcore.exceptions.TooManyRequests as e:
            error_msg = "Rate limited: Too many requests. Please wait before posting again"
            logger.error(f"Rate limited: {e}")
            return {'success': False, 'error': error_msg, 'comment_id': None}
            
        except Exception as e:
            logger.error(f"Error posting comment: {e}")
            return {'success': False, 'error': str(e), 'comment_id': None}
    
    def generate_and_post_comment(self, post_id: str, subreddit_name: str = None) -> Dict:
        """
        Generate and post an AI comment to a Reddit post
        
        Args:
            post_id: Reddit post ID
            subreddit_name: Optional subreddit name for context
            
        Returns:
            Dictionary with posting result
        """
        try:
            # Get post details
            submission = self.reddit.submission(id=post_id)
            
            # Get existing comments for context
            existing_comments = []
            submission.comments.replace_more(limit=0)
            for comment in submission.comments.list()[:5]:  # Get top 5 comments
                if hasattr(comment, 'body') and comment.body != '[deleted]':
                    existing_comments.append(comment.body)
            
            # Generate comment using validator/AI
            generated_comment = self.validator.generate_comment(
                post_title=submission.title,
                post_content=submission.selftext,
                subreddit=subreddit_name or str(submission.subreddit),
                existing_comments=existing_comments
            )
            
            if generated_comment.startswith("Error"):
                return {
                    'success': False,
                    'error': generated_comment,
                    'comment_id': None
                }
            
            # Post the generated comment
            return self.post_comment(post_id, generated_comment, validate=True)
            
        except Exception as e:
            logger.error(f"Error generating and posting comment: {e}")
            return {'success': False, 'error': str(e), 'comment_id': None}
    
    def search_posts(self, query: str, subreddit_name: str = None, 
                    sort: str = 'relevance', time_filter: str = 'all', 
                    limit: int = 25) -> List[Dict]:
        """
        Search for posts on Reddit
        
        Args:
            query: Search query
            subreddit_name: Optional subreddit to search within
            sort: Sort method ('relevance', 'hot', 'top', 'new', 'comments')
            time_filter: Time filter ('all', 'day', 'week', 'month', 'year')
            limit: Maximum number of results
            
        Returns:
            List of post dictionaries
        """
        try:
            if subreddit_name:
                # Validate subreddit name
                is_valid, result = self.validator.validate_subreddit_name(subreddit_name)
                if not is_valid:
                    raise ValueError(result)
                subreddit_name = result
                subreddit = self.reddit.subreddit(subreddit_name)
                search_results = subreddit.search(query, sort=sort, time_filter=time_filter, limit=limit)
            else:
                search_results = self.reddit.subreddit('all').search(query, sort=sort, time_filter=time_filter, limit=limit)
            
            posts_data = []
            for post in search_results:
                try:
                    post_info = {
                        'id': post.id,
                        'title': post.title,
                        'author': str(post.author) if post.author else '[deleted]',
                        'score': post.score,
                        'num_comments': post.num_comments,
                        'created_utc': post.created_utc,
                        'permalink': f"https://reddit.com{post.permalink}",
                        'selftext': post.selftext,
                        'subreddit': str(post.subreddit),
                        'url': post.url
                    }
                    
                    is_valid, _ = self.validator.validate_post_data(post_info)
                    if is_valid:
                        posts_data.append(post_info)
                        
                except Exception as e:
                    logger.warning(f"Error processing search result: {e}")
                    continue
            
            logger.info(f"Found {len(posts_data)} posts for query: {query}")
            return posts_data
            
        except Exception as e:
            logger.error(f"Error searching posts: {e}")
            raise
    
    def get_user_info(self, username: str = None) -> Dict:
        """
        Get information about a Reddit user
        
        Args:
            username: Username to get info for (defaults to authenticated user)
            
        Returns:
            Dictionary with user information
        """
        try:
            if username:
                user = self.reddit.redditor(username)
            else:
                user = self.reddit.user.me()
            
            user_info = {
                'name': user.name,
                'id': user.id,
                'created_utc': user.created_utc,
                'comment_karma': user.comment_karma,
                'link_karma': user.link_karma,
                'total_karma': user.comment_karma + user.link_karma,
                'is_gold': user.is_gold,
                'is_mod': user.is_mod,
                'verified': user.verified,
                'has_verified_email': user.has_verified_email
            }
            
            return user_info
            
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            raise