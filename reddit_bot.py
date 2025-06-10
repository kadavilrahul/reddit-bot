"""
Main Reddit Bot class with comprehensive functionality
"""
import logging
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from reddit_client import RedditClient
from validators import RedditValidator
import schedule

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('reddit_bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class RedditBot:
    """Main Reddit Bot class with automated posting and data retrieval capabilities"""
    
    def __init__(self):
        """Initialize the Reddit bot"""
        try:
            self.client = RedditClient()
            self.validator = RedditValidator()
            self.stats = {
                'comments_posted': 0,
                'posts_retrieved': 0,
                'errors': 0,
                'start_time': datetime.now()
            }
            logger.info("Reddit Bot initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Reddit Bot: {e}")
            raise
    
    def retrieve_subreddit_data(self, subreddit_name: str, sort_by: str = 'hot', 
                               limit: int = 10, include_comments: bool = False) -> Dict:
        """
        Retrieve comprehensive data from a subreddit
        
        Args:
            subreddit_name: Name of the subreddit
            sort_by: Sort method for posts
            limit: Number of posts to retrieve
            include_comments: Whether to include comments for each post
            
        Returns:
            Dictionary containing subreddit data
        """
        try:
            logger.info(f"Retrieving data from r/{subreddit_name}")
            
            # Get posts
            posts = self.client.get_subreddit_posts(
                subreddit_name=subreddit_name,
                sort_by=sort_by,
                limit=limit
            )
            
            # Get comments for each post if requested
            if include_comments:
                for post in posts:
                    try:
                        comments = self.client.get_post_comments(post['id'], limit=20)
                        post['comments'] = comments
                        time.sleep(1)  # Rate limiting
                    except Exception as e:
                        logger.warning(f"Failed to get comments for post {post['id']}: {e}")
                        post['comments'] = []
            
            subreddit_data = {
                'subreddit': subreddit_name,
                'retrieved_at': datetime.now().isoformat(),
                'sort_method': sort_by,
                'total_posts': len(posts),
                'posts': posts,
                'summary': self._generate_subreddit_summary(posts)
            }
            
            self.stats['posts_retrieved'] += len(posts)
            logger.info(f"Successfully retrieved {len(posts)} posts from r/{subreddit_name}")
            
            return subreddit_data
            
        except Exception as e:
            logger.error(f"Error retrieving subreddit data: {e}")
            self.stats['errors'] += 1
            raise
    
    def auto_comment_on_posts(self, subreddit_name: str, max_comments: int = 5, 
                             sort_by: str = 'new', min_score: int = 0) -> List[Dict]:
        """
        Automatically generate and post comments on recent posts
        
        Args:
            subreddit_name: Target subreddit
            max_comments: Maximum number of comments to post
            sort_by: How to sort posts ('new', 'hot', 'rising')
            min_score: Minimum post score to comment on
            
        Returns:
            List of comment posting results
        """
        try:
            logger.info(f"Starting auto-commenting on r/{subreddit_name}")
            
            # Get recent posts
            posts = self.client.get_subreddit_posts(
                subreddit_name=subreddit_name,
                sort_by=sort_by,
                limit=max_comments * 2  # Get more posts to filter from
            )
            
            # Filter posts based on criteria
            eligible_posts = []
            for post in posts:
                if (post['score'] >= min_score and 
                    not post['locked'] and 
                    not post['over_18'] and
                    post['num_comments'] < 100):  # Avoid heavily commented posts
                    eligible_posts.append(post)
            
            # Comment on eligible posts
            results = []
            comments_posted = 0
            
            for post in eligible_posts[:max_comments]:
                try:
                    logger.info(f"Generating comment for post: {post['title'][:50]}...")
                    
                    result = self.client.generate_and_post_comment(
                        post_id=post['id'],
                        subreddit_name=subreddit_name
                    )
                    
                    result['post_title'] = post['title']
                    result['post_id'] = post['id']
                    results.append(result)
                    
                    if result['success']:
                        comments_posted += 1
                        self.stats['comments_posted'] += 1
                        logger.info(f"Successfully commented on post {post['id']}")
                    else:
                        logger.warning(f"Failed to comment on post {post['id']}: {result['error']}")
                        self.stats['errors'] += 1
                    
                    # Rate limiting between comments
                    time.sleep(10)
                    
                except Exception as e:
                    logger.error(f"Error commenting on post {post['id']}: {e}")
                    self.stats['errors'] += 1
                    results.append({
                        'success': False,
                        'error': str(e),
                        'post_id': post['id'],
                        'post_title': post['title']
                    })
            
            logger.info(f"Auto-commenting completed. Posted {comments_posted} comments")
            return results
            
        except Exception as e:
            logger.error(f"Error in auto-commenting: {e}")
            self.stats['errors'] += 1
            raise
    
    def search_and_analyze(self, query: str, subreddit_name: str = None, 
                          limit: int = 50) -> Dict:
        """
        Search for posts and provide analysis
        
        Args:
            query: Search query
            subreddit_name: Optional subreddit to search within
            limit: Maximum number of results
            
        Returns:
            Dictionary with search results and analysis
        """
        try:
            logger.info(f"Searching for: {query}")
            
            posts = self.client.search_posts(
                query=query,
                subreddit_name=subreddit_name,
                limit=limit
            )
            
            # Generate analysis using AI
            analysis = self._analyze_posts_with_ai(posts, query)
            
            search_results = {
                'query': query,
                'subreddit': subreddit_name,
                'searched_at': datetime.now().isoformat(),
                'total_results': len(posts),
                'posts': posts,
                'analysis': analysis
            }
            
            return search_results
            
        except Exception as e:
            logger.error(f"Error in search and analysis: {e}")
            raise
    
    def monitor_subreddit(self, subreddit_name: str, keywords: List[str], 
                         action: str = 'comment', duration_hours: int = 24) -> Dict:
        """
        Monitor a subreddit for specific keywords and take action
        
        Args:
            subreddit_name: Subreddit to monitor
            keywords: List of keywords to watch for
            action: Action to take ('comment', 'log', 'both')
            duration_hours: How long to monitor
            
        Returns:
            Monitoring results
        """
        try:
            logger.info(f"Starting monitoring of r/{subreddit_name} for keywords: {keywords}")
            
            start_time = datetime.now()
            end_time = start_time + timedelta(hours=duration_hours)
            matches = []
            
            while datetime.now() < end_time:
                try:
                    # Get new posts
                    posts = self.client.get_subreddit_posts(
                        subreddit_name=subreddit_name,
                        sort_by='new',
                        limit=10
                    )
                    
                    # Check for keyword matches
                    for post in posts:
                        post_text = f"{post['title']} {post['selftext']}".lower()
                        
                        for keyword in keywords:
                            if keyword.lower() in post_text:
                                match_info = {
                                    'post_id': post['id'],
                                    'title': post['title'],
                                    'keyword': keyword,
                                    'matched_at': datetime.now().isoformat(),
                                    'permalink': post['permalink']
                                }
                                
                                matches.append(match_info)
                                logger.info(f"Keyword match found: {keyword} in post {post['id']}")
                                
                                # Take action based on configuration
                                if action in ['comment', 'both']:
                                    try:
                                        comment_result = self.client.generate_and_post_comment(
                                            post_id=post['id'],
                                            subreddit_name=subreddit_name
                                        )
                                        match_info['comment_result'] = comment_result
                                    except Exception as e:
                                        logger.error(f"Failed to comment on matched post: {e}")
                    
                    # Wait before next check
                    time.sleep(300)  # Check every 5 minutes
                    
                except Exception as e:
                    logger.error(f"Error during monitoring cycle: {e}")
                    time.sleep(60)  # Wait 1 minute before retrying
            
            monitoring_results = {
                'subreddit': subreddit_name,
                'keywords': keywords,
                'duration_hours': duration_hours,
                'total_matches': len(matches),
                'matches': matches,
                'completed_at': datetime.now().isoformat()
            }
            
            logger.info(f"Monitoring completed. Found {len(matches)} matches")
            return monitoring_results
            
        except Exception as e:
            logger.error(f"Error in subreddit monitoring: {e}")
            raise
    
    def get_bot_stats(self) -> Dict:
        """Get bot statistics and performance metrics"""
        runtime = datetime.now() - self.stats['start_time']
        
        return {
            'runtime_hours': runtime.total_seconds() / 3600,
            'comments_posted': self.stats['comments_posted'],
            'posts_retrieved': self.stats['posts_retrieved'],
            'errors': self.stats['errors'],
            'success_rate': (
                (self.stats['comments_posted'] / 
                 max(1, self.stats['comments_posted'] + self.stats['errors'])) * 100
            ),
            'start_time': self.stats['start_time'].isoformat(),
            'current_time': datetime.now().isoformat()
        }
    
    def save_data_to_file(self, data: Dict, filename: str = None) -> str:
        """Save data to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reddit_data_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Data saved to {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error saving data to file: {e}")
            raise
    
    def _generate_subreddit_summary(self, posts: List[Dict]) -> Dict:
        """Generate summary statistics for subreddit posts"""
        if not posts:
            return {}
        
        total_score = sum(post['score'] for post in posts)
        total_comments = sum(post['num_comments'] for post in posts)
        
        return {
            'total_posts': len(posts),
            'average_score': total_score / len(posts),
            'total_score': total_score,
            'total_comments': total_comments,
            'average_comments': total_comments / len(posts),
            'top_post': max(posts, key=lambda x: x['score'])['title'],
            'most_discussed': max(posts, key=lambda x: x['num_comments'])['title']
        }
    
    def _analyze_posts_with_ai(self, posts: List[Dict], query: str) -> str:
        """Use AI to analyze search results"""
        try:
            if not posts:
                return "No posts found for analysis"
            
            # Prepare data for analysis
            posts_summary = []
            for post in posts[:10]:  # Analyze top 10 posts
                posts_summary.append({
                    'title': post['title'],
                    'score': post['score'],
                    'comments': post['num_comments'],
                    'subreddit': post['subreddit']
                })
            
            analysis_prompt = f"""
            Analyze these Reddit search results for query: "{query}"
            
            Posts data: {json.dumps(posts_summary, indent=2)}
            
            Provide insights about:
            1. Common themes and topics
            2. Engagement patterns (scores, comments)
            3. Popular subreddits for this topic
            4. Trends and observations
            5. Key takeaways
            
            Keep the analysis concise but informative.
            """
            
            response = self.validator.validation_agent.run(analysis_prompt)
            return response.content
            
        except Exception as e:
            logger.error(f"Error in AI analysis: {e}")
            return f"Analysis error: {str(e)}"
    
    def schedule_auto_commenting(self, subreddit_name: str, interval_hours: int = 6, 
                                max_comments: int = 3):
        """Schedule automatic commenting at regular intervals"""
        def job():
            try:
                logger.info(f"Running scheduled auto-commenting on r/{subreddit_name}")
                self.auto_comment_on_posts(
                    subreddit_name=subreddit_name,
                    max_comments=max_comments,
                    sort_by='new'
                )
            except Exception as e:
                logger.error(f"Scheduled job error: {e}")
        
        schedule.every(interval_hours).hours.do(job)
        logger.info(f"Scheduled auto-commenting every {interval_hours} hours for r/{subreddit_name}")
    
    def run_scheduler(self):
        """Run the scheduled tasks"""
        logger.info("Starting scheduler...")
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute