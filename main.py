#!/usr/bin/env python3
"""
Reddit Bot Main Application
Interactive CLI for Reddit bot operations
"""
import sys
import json
import argparse
from datetime import datetime
from reddit_bot import RedditBot
import logging

logger = logging.getLogger(__name__)

def print_banner():
    """Print application banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                        REDDIT BOT                            ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def print_menu():
    """Print main menu options"""
    menu = """
    ┌─────────────────────────────────────────────────────────────┐
    │                        MAIN MENU                            │
    ├─────────────────────────────────────────────────────────────┤
    │  1. Retrieve Subreddit Data                                 │
    │  2. Auto-Comment on Posts                                   │
    │  3. Search and Analyze Posts                                │
    │  4. Monitor Subreddit for Keywords                          │
    │  5. Post Custom Comment                                     │
    │  6. Get Bot Statistics                                      │
    │  7. Schedule Auto-Commenting                                │
    │  8. Export Data to File                                     │
    │  9. Get User Information                                    │
    │  0. Exit                                                    │
    └─────────────────────────────────────────────────────────────┘
    """
    print(menu)

def get_user_input(prompt: str, input_type: type = str, default=None):
    """Get validated user input"""
    while True:
        try:
            user_input = input(f"{prompt}: ").strip()
            if not user_input and default is not None:
                return default
            if not user_input:
                print("Input cannot be empty. Please try again.")
                continue
            return input_type(user_input)
        except ValueError:
            print(f"Invalid input. Please enter a valid {input_type.__name__}.")
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
            return None

def retrieve_subreddit_data(bot: RedditBot):
    """Handle subreddit data retrieval"""
    print("\n" + "="*60)
    print("RETRIEVE SUBREDDIT DATA")
    print("="*60)
    
    subreddit = get_user_input("Enter subreddit name (without r/)")
    if not subreddit:
        return
    
    sort_options = ['hot', 'new', 'top', 'rising']
    print(f"Sort options: {', '.join(sort_options)}")
    sort_by = get_user_input("Sort by", default='hot')
    if sort_by not in sort_options:
        sort_by = 'hot'
    
    limit = get_user_input("Number of posts to retrieve", int, 10)
    include_comments = get_user_input("Include comments? (y/n)", default='n').lower() == 'y'
    
    try:
        print(f"\n🔄 Retrieving data from r/{subreddit}...")
        data = bot.retrieve_subreddit_data(
            subreddit_name=subreddit,
            sort_by=sort_by,
            limit=limit,
            include_comments=include_comments
        )
        
        print(f"\n✅ Successfully retrieved {data['total_posts']} posts!")
        print(f"📊 Summary:")
        summary = data['summary']
        if summary:
            print(f"   • Average Score: {summary.get('average_score', 0):.1f}")
            print(f"   • Total Comments: {summary.get('total_comments', 0)}")
            print(f"   • Top Post: {summary.get('top_post', 'N/A')[:50]}...")
        
        save = get_user_input("Save data to file? (y/n)", default='y').lower() == 'y'
        if save:
            filename = bot.save_data_to_file(data)
            print(f"💾 Data saved to: {filename}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def auto_comment_on_posts(bot: RedditBot):
    """Handle automatic commenting"""
    print("\n" + "="*60)
    print("AUTO-COMMENT ON POSTS")
    print("="*60)
    
    subreddit = get_user_input("Enter subreddit name (without r/)")
    if not subreddit:
        return
    
    max_comments = get_user_input("Maximum comments to post", int, 3)
    sort_options = ['new', 'hot', 'rising']
    print(f"Sort options: {', '.join(sort_options)}")
    sort_by = get_user_input("Sort posts by", default='new')
    if sort_by not in sort_options:
        sort_by = 'new'
    
    min_score = get_user_input("Minimum post score", int, 0)
    
    confirm = get_user_input(f"Confirm: Post up to {max_comments} AI comments on r/{subreddit}? (y/n)", default='n')
    if confirm.lower() != 'y':
        print("Operation cancelled.")
        return
    
    try:
        print(f"\n🤖 Starting auto-commenting on r/{subreddit}...")
        results = bot.auto_comment_on_posts(
            subreddit_name=subreddit,
            max_comments=max_comments,
            sort_by=sort_by,
            min_score=min_score
        )
        
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        
        print(f"\n📊 Auto-commenting Results:")
        print(f"   • Successful: {successful}")
        print(f"   • Failed: {failed}")
        
        if failed > 0:
            print("\n❌ Failed comments:")
            for result in results:
                if not result['success']:
                    print(f"   • {result['post_title'][:40]}... - {result['error']}")
                    
    except Exception as e:
        print(f"❌ Error: {e}")

def search_and_analyze(bot: RedditBot):
    """Handle search and analysis"""
    print("\n" + "="*60)
    print("SEARCH AND ANALYZE POSTS")
    print("="*60)
    
    query = get_user_input("Enter search query")
    if not query:
        return
    
    subreddit = get_user_input("Subreddit to search (optional, press Enter for all)", default=None)
    limit = get_user_input("Maximum results", int, 25)
    
    try:
        print(f"\n🔍 Searching for: '{query}'...")
        results = bot.search_and_analyze(
            query=query,
            subreddit_name=subreddit,
            limit=limit
        )
        
        print(f"\n📊 Search Results:")
        print(f"   • Total Results: {results['total_results']}")
        print(f"   • Query: {results['query']}")
        if results['subreddit']:
            print(f"   • Subreddit: r/{results['subreddit']}")
        
        print(f"\n🤖 AI Analysis:")
        print(results['analysis'])
        
        save = get_user_input("Save results to file? (y/n)", default='y').lower() == 'y'
        if save:
            filename = bot.save_data_to_file(results)
            print(f"💾 Results saved to: {filename}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def monitor_subreddit(bot: RedditBot):
    """Handle subreddit monitoring"""
    print("\n" + "="*60)
    print("MONITOR SUBREDDIT FOR KEYWORDS")
    print("="*60)
    
    subreddit = get_user_input("Enter subreddit name (without r/)")
    if not subreddit:
        return
    
    keywords_input = get_user_input("Enter keywords (comma-separated)")
    if not keywords_input:
        return
    
    keywords = [k.strip() for k in keywords_input.split(',')]
    duration = get_user_input("Monitoring duration (hours)", int, 1)
    
    action_options = ['comment', 'log', 'both']
    print(f"Action options: {', '.join(action_options)}")
    action = get_user_input("Action to take on matches", default='log')
    if action not in action_options:
        action = 'log'
    
    print(f"\n👁️ Starting monitoring...")
    print(f"   • Subreddit: r/{subreddit}")
    print(f"   • Keywords: {', '.join(keywords)}")
    print(f"   • Duration: {duration} hours")
    print(f"   • Action: {action}")
    
    try:
        results = bot.monitor_subreddit(
            subreddit_name=subreddit,
            keywords=keywords,
            action=action,
            duration_hours=duration
        )
        
        print(f"\n📊 Monitoring Results:")
        print(f"   • Total Matches: {results['total_matches']}")
        
        if results['matches']:
            print("\n🎯 Matches Found:")
            for match in results['matches'][:5]:  # Show first 5 matches
                print(f"   • '{match['keyword']}' in: {match['title'][:40]}...")
        
        save = get_user_input("Save monitoring results to file? (y/n)", default='y').lower() == 'y'
        if save:
            filename = bot.save_data_to_file(results)
            print(f"💾 Results saved to: {filename}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def post_custom_comment(bot: RedditBot):
    """Handle custom comment posting"""
    print("\n" + "="*60)
    print("POST CUSTOM COMMENT")
    print("="*60)
    
    post_url = get_user_input("Enter Reddit post URL or post ID")
    if not post_url:
        return
    
    # Extract post ID from URL if needed
    if 'reddit.com' in post_url:
        try:
            post_id = post_url.split('/comments/')[1].split('/')[0]
        except:
            print("❌ Invalid Reddit URL format")
            return
    else:
        post_id = post_url
    
    print("\nComment options:")
    print("1. Write custom comment")
    print("2. Generate AI comment")
    
    option = get_user_input("Choose option (1/2)", int, 1)
    
    try:
        if option == 1:
            comment_text = get_user_input("Enter your comment")
            if not comment_text:
                return
            
            result = bot.client.post_comment(post_id, comment_text, validate=True)
        else:
            subreddit = get_user_input("Enter subreddit name (for context)", default="")
            result = bot.client.generate_and_post_comment(post_id, subreddit)
        
        if result['success']:
            print(f"✅ Comment posted successfully!")
            print(f"   • Comment ID: {result['comment_id']}")
            print(f"   • Permalink: {result['permalink']}")
        else:
            print(f"❌ Failed to post comment: {result['error']}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def show_bot_stats(bot: RedditBot):
    """Display bot statistics"""
    print("\n" + "="*60)
    print("BOT STATISTICS")
    print("="*60)
    
    try:
        stats = bot.get_bot_stats()
        
        print(f"🤖 Bot Performance:")
        print(f"   • Runtime: {stats['runtime_hours']:.1f} hours")
        print(f"   • Comments Posted: {stats['comments_posted']}")
        print(f"   • Posts Retrieved: {stats['posts_retrieved']}")
        print(f"   • Errors: {stats['errors']}")
        print(f"   • Success Rate: {stats['success_rate']:.1f}%")
        print(f"   • Started: {stats['start_time']}")
        
        # Get user info
        user_info = bot.client.get_user_info()
        print(f"\n👤 Account Information:")
        print(f"   • Username: {user_info['name']}")
        print(f"   • Comment Karma: {user_info['comment_karma']:,}")
        print(f"   • Link Karma: {user_info['link_karma']:,}")
        print(f"   • Total Karma: {user_info['total_karma']:,}")
        print(f"   • Account Age: {(datetime.now().timestamp() - user_info['created_utc']) / (365.25 * 24 * 3600):.1f} years")
        
    except Exception as e:
        print(f"❌ Error getting stats: {e}")

def schedule_auto_commenting(bot: RedditBot):
    """Handle scheduling setup"""
    print("\n" + "="*60)
    print("SCHEDULE AUTO-COMMENTING")
    print("="*60)
    
    subreddit = get_user_input("Enter subreddit name (without r/)")
    if not subreddit:
        return
    
    interval = get_user_input("Interval between comments (hours)", int, 6)
    max_comments = get_user_input("Max comments per session", int, 3)
    
    try:
        bot.schedule_auto_commenting(
            subreddit_name=subreddit,
            interval_hours=interval,
            max_comments=max_comments
        )
        
        print(f"✅ Scheduled auto-commenting:")
        print(f"   • Subreddit: r/{subreddit}")
        print(f"   • Interval: Every {interval} hours")
        print(f"   • Max comments per session: {max_comments}")
        print("\n⚠️  Note: Keep the application running for scheduled tasks to work")
        
        run_scheduler = get_user_input("Start scheduler now? (y/n)", default='n').lower() == 'y'
        if run_scheduler:
            print("🔄 Starting scheduler... (Press Ctrl+C to stop)")
            bot.run_scheduler()
            
    except Exception as e:
        print(f"❌ Error setting up schedule: {e}")

def main():
    """Main application function"""
    parser = argparse.ArgumentParser(description='Reddit Bot - ScraperBot v1.0')
    parser.add_argument('--auto', action='store_true', help='Run in automated mode')
    parser.add_argument('--subreddit', help='Target subreddit for automated mode')
    parser.add_argument('--comments', type=int, default=5, help='Number of comments in auto mode')
    
    args = parser.parse_args()
    
    print_banner()
    
    try:
        print("🔄 Initializing Reddit Bot...")
        bot = RedditBot()
        print("✅ Bot initialized successfully!")
        
        if args.auto:
            # Automated mode
            subreddit = args.subreddit or get_user_input("Enter subreddit for auto mode")
            if subreddit:
                print(f"🤖 Running in automated mode on r/{subreddit}")
                bot.auto_comment_on_posts(subreddit, max_comments=args.comments)
            return
        
        # Interactive mode
        while True:
            print_menu()
            choice = get_user_input("Select an option (0-9)", int)
            
            if choice == 0:
                print("👋 Goodbye!")
                break
            elif choice == 1:
                retrieve_subreddit_data(bot)
            elif choice == 2:
                auto_comment_on_posts(bot)
            elif choice == 3:
                search_and_analyze(bot)
            elif choice == 4:
                monitor_subreddit(bot)
            elif choice == 5:
                post_custom_comment(bot)
            elif choice == 6:
                show_bot_stats(bot)
            elif choice == 7:
                schedule_auto_commenting(bot)
            elif choice == 8:
                # Export current data
                stats = bot.get_bot_stats()
                filename = bot.save_data_to_file(stats, "bot_stats.json")
                print(f"💾 Bot statistics exported to: {filename}")
            elif choice == 9:
                try:
                    user_info = bot.client.get_user_info()
                    print(f"\n👤 User Information:")
                    for key, value in user_info.items():
                        print(f"   • {key.replace('_', ' ').title()}: {value}")
                except Exception as e:
                    print(f"❌ Error getting user info: {e}")
            else:
                print("❌ Invalid option. Please try again.")
            
            input("\nPress Enter to continue...")
            
    except KeyboardInterrupt:
        print("\n\n👋 Bot stopped by user.")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        logger.error(f"Fatal error in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()