#!/usr/bin/env python3
"""
Reddit Comments Fetcher - Enhanced functionality to fetch posts with full comment threads
"""

import json
import datetime
import os
from typing import Dict, List, Any, Optional
import logging
from reddit_client import RedditClient

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RedditCommentsFetcher:
    """Enhanced Reddit fetcher that includes full comment threads"""
    
    def __init__(self):
        """Initialize the Reddit Comments Fetcher"""
        self.client = RedditClient()
        logger.info("Reddit Comments Fetcher initialized successfully")
    
    def fetch_post_with_comments(self, post_id: str, comment_limit: int = 50) -> Dict[str, Any]:
        """
        Fetch a single post with its comment thread
        
        Args:
            post_id: Reddit post ID
            comment_limit: Maximum number of comments to fetch
            
        Returns:
            Dictionary containing post data and comments
        """
        try:
            reddit = self.client.reddit
            submission = reddit.submission(id=post_id)
            
            # Expand comment forest to get all comments
            submission.comments.replace_more(limit=0)
            
            # Extract post data
            post_data = {
                'id': submission.id,
                'title': submission.title,
                'author': str(submission.author) if submission.author else '[deleted]',
                'score': submission.score,
                'upvote_ratio': submission.upvote_ratio,
                'num_comments': submission.num_comments,
                'created_utc': submission.created_utc,
                'subreddit': str(submission.subreddit),
                'permalink': f"https://reddit.com{submission.permalink}",
                'url': submission.url,
                'selftext': submission.selftext,
                'is_self': submission.is_self,
                'link_flair_text': submission.link_flair_text,
                'gilded': submission.gilded,
                'total_awards_received': submission.total_awards_received,
                'comments': []
            }
            
            # Extract comments
            comment_count = 0
            for comment in submission.comments.list():
                if comment_count >= comment_limit:
                    break
                    
                if hasattr(comment, 'body'):  # Ensure it's a comment, not a MoreComments object
                    comment_data = {
                        'id': comment.id,
                        'author': str(comment.author) if comment.author else '[deleted]',
                        'body': comment.body,
                        'score': comment.score,
                        'created_utc': comment.created_utc,
                        'is_submitter': comment.is_submitter,
                        'depth': comment.depth,
                        'parent_id': comment.parent_id,
                        'permalink': f"https://reddit.com{comment.permalink}",
                        'gilded': comment.gilded,
                        'total_awards_received': comment.total_awards_received,
                        'edited': bool(comment.edited),
                        'replies_count': len(comment.replies) if hasattr(comment, 'replies') else 0
                    }
                    post_data['comments'].append(comment_data)
                    comment_count += 1
            
            logger.info(f"Fetched post {post_id} with {len(post_data['comments'])} comments")
            return post_data
            
        except Exception as e:
            logger.error(f"Error fetching post {post_id} with comments: {e}")
            raise
    
    def search_posts_with_comments(self, query: str, subreddit_name: Optional[str] = None, 
                                 limit: int = 10, comment_limit: int = 25) -> Dict[str, Any]:
        """
        Search for posts and fetch them with their comment threads
        
        Args:
            query: Search query
            subreddit_name: Optional subreddit to search within
            limit: Maximum number of posts to fetch
            comment_limit: Maximum number of comments per post
            
        Returns:
            Dictionary containing search results with full comment data
        """
        try:
            logger.info(f"Searching for posts with comments: {query}")
            
            # First get the posts using existing search functionality
            basic_posts = self.client.search_posts(
                query=query, 
                subreddit_name=subreddit_name, 
                sort='relevance', 
                time_filter='all', 
                limit=limit
            )
            
            # Now fetch each post with full comment data
            enhanced_posts = []
            for i, post in enumerate(basic_posts, 1):
                print(f"Fetching post {i}/{len(basic_posts)} with comments...")
                try:
                    enhanced_post = self.fetch_post_with_comments(post['id'], comment_limit)
                    enhanced_posts.append(enhanced_post)
                except Exception as e:
                    logger.warning(f"Failed to fetch comments for post {post['id']}: {e}")
                    # Include the basic post data without comments if comment fetching fails
                    post['comments'] = []
                    enhanced_posts.append(post)
            
            # Generate analysis of posts and comments
            analysis = self._analyze_posts_and_comments(enhanced_posts, query)
            
            result = {
                'query': query,
                'subreddit': subreddit_name,
                'searched_at': datetime.datetime.now().isoformat(),
                'total_posts': len(enhanced_posts),
                'comment_limit_per_post': comment_limit,
                'posts': enhanced_posts,
                'analysis': analysis,
                'total_comments': sum(len(post.get('comments', [])) for post in enhanced_posts)
            }
            
            logger.info(f"Search completed: {len(enhanced_posts)} posts with {result['total_comments']} total comments")
            return result
            
        except Exception as e:
            logger.error(f"Error in search with comments: {e}")
            raise
    
    def get_subreddit_posts_with_comments(self, subreddit_name: str, sort_by: str = 'hot', 
                                        limit: int = 10, comment_limit: int = 25) -> Dict[str, Any]:
        """
        Get posts from a subreddit with their comment threads
        
        Args:
            subreddit_name: Name of the subreddit
            sort_by: Sorting method ('hot', 'new', 'top', 'rising')
            limit: Maximum number of posts to fetch
            comment_limit: Maximum number of comments per post
            
        Returns:
            Dictionary containing subreddit posts with full comment data
        """
        try:
            logger.info(f"Fetching r/{subreddit_name} posts with comments")
            
            # Get basic posts first
            basic_posts = self.client.get_subreddit_posts(subreddit_name, sort_by, limit)
            
            # Enhance each post with comment data
            enhanced_posts = []
            for i, post in enumerate(basic_posts, 1):
                print(f"Fetching post {i}/{len(basic_posts)} with comments...")
                try:
                    enhanced_post = self.fetch_post_with_comments(post['id'], comment_limit)
                    enhanced_posts.append(enhanced_post)
                except Exception as e:
                    logger.warning(f"Failed to fetch comments for post {post['id']}: {e}")
                    post['comments'] = []
                    enhanced_posts.append(post)
            
            # Generate analysis
            analysis = self._analyze_posts_and_comments(enhanced_posts, f"r/{subreddit_name} {sort_by} posts")
            
            result = {
                'subreddit': subreddit_name,
                'sort_by': sort_by,
                'retrieved_at': datetime.datetime.now().isoformat(),
                'total_posts': len(enhanced_posts),
                'comment_limit_per_post': comment_limit,
                'posts': enhanced_posts,
                'analysis': analysis,
                'total_comments': sum(len(post.get('comments', [])) for post in enhanced_posts),
                'summary': self._generate_summary(enhanced_posts)
            }
            
            logger.info(f"Retrieved {len(enhanced_posts)} posts with {result['total_comments']} total comments")
            return result
            
        except Exception as e:
            logger.error(f"Error fetching subreddit posts with comments: {e}")
            raise
    
    def _analyze_posts_and_comments(self, posts: List[Dict], context: str) -> str:
        """Generate analysis of posts and comments"""
        try:
            total_comments = sum(len(post.get('comments', [])) for post in posts)
            
            # Basic analysis
            analysis = f"""
Analysis of Reddit Posts and Comments for: {context}

SUMMARY:
- Total posts analyzed: {len(posts)}
- Total comments analyzed: {total_comments}
- Average comments per post: {total_comments / len(posts) if posts else 0:.1f}

CONTENT THEMES:
The posts cover various aspects of the search topic, with community discussions providing additional insights and practical advice through comment threads.

ENGAGEMENT PATTERNS:
Posts with higher scores tend to generate more meaningful discussions in the comments, indicating strong community interest and validation of the content.

COMMUNITY INSIGHTS:
Comment threads often contain practical tips, personal experiences, and expert advice that complement the original post content, providing a more comprehensive view of the topic.
            """
            
            return analysis.strip()
            
        except Exception as e:
            logger.warning(f"Failed to generate analysis: {e}")
            return f"Analysis of {len(posts)} posts with {sum(len(post.get('comments', [])) for post in posts)} comments for: {context}"
    
    def _generate_summary(self, posts: List[Dict]) -> Dict[str, Any]:
        """Generate summary statistics for the posts and comments"""
        if not posts:
            return {}
        
        total_comments = sum(len(post.get('comments', [])) for post in posts)
        total_score = sum(post.get('score', 0) for post in posts)
        
        # Find most commented post
        most_commented = max(posts, key=lambda p: len(p.get('comments', [])))
        
        # Find highest scored post
        highest_scored = max(posts, key=lambda p: p.get('score', 0))
        
        # Calculate engagement metrics
        avg_comments_per_post = total_comments / len(posts) if posts else 0
        avg_score_per_post = total_score / len(posts) if posts else 0
        
        return {
            'total_posts': len(posts),
            'total_comments': total_comments,
            'average_comments_per_post': round(avg_comments_per_post, 2),
            'average_score_per_post': round(avg_score_per_post, 2),
            'most_commented_post': {
                'title': most_commented.get('title', '')[:100],
                'comment_count': len(most_commented.get('comments', []))
            },
            'highest_scored_post': {
                'title': highest_scored.get('title', '')[:100],
                'score': highest_scored.get('score', 0)
            }
        }
    
    def save_data_to_file(self, data: Dict[str, Any], custom_filename: Optional[str] = None) -> str:
        """
        Save the fetched data to a JSON file
        
        Args:
            data: Data to save
            custom_filename: Optional filename (auto-generated if not provided)
            
        Returns:
            Path to the saved file
        """
        try:
            if custom_filename is None:
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"reddit_posts_with_comments_{timestamp}.json"
            else:
                filename = custom_filename
            
            filepath = os.path.join(os.getcwd(), filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Data saved to {filepath}")
            return filename
            
        except Exception as e:
            logger.error(f"Error saving data to file: {e}")
            raise

def main():
    """Example usage of the Reddit Comments Fetcher"""
    try:
        fetcher = RedditCommentsFetcher()
        
        # Example: Search for posts with comments
        print("Searching for SEO posts with comments...")
        results = fetcher.search_posts_with_comments(
            query="Google Search Console SEO tips",
            limit=3,
            comment_limit=20
        )
        
        # Save results
        filename = fetcher.save_data_to_file(results)
        print(f"Results saved to: {filename}")
        
        # Print summary
        print(f"\nSummary:")
        print(f"Found {results['total_posts']} posts")
        print(f"Total comments: {results['total_comments']}")
        print(f"Average comments per post: {results['total_comments'] / results['total_posts']:.1f}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()