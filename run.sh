#!/bin/bash

# Reddit Bot CLI - Comprehensive Reddit automation and analysis tool
RED='\033[0;31m'; GREEN='\033[0;32m'; BLUE='\033[0;34m'; YELLOW='\033[1;33m'; NC='\033[0m'

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
VENV_NAME="reddit_bot_env"
PYTHON_CMD="python3"
LOG_FILE="/var/log/reddit-bot.log"

# Logging and utility functions
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

confirm_action() {
    echo -n "$1 (y/N): "
    read -r response
    case "$response" in
        [yY]|[yY][eE][sS]) return 0 ;;
        *) return 1 ;;
    esac
}

confirm_action_default_yes() {
    echo -n "$1 (Y/n): "
    read -r response
    case "$response" in
        [nN]|[nN][oO]) return 1 ;;
        *) return 0 ;;
    esac
}

# === Core Setup Functions ===
setup_env() {
    cd "$SCRIPT_DIR"
    if [ ! -d "$VENV_NAME" ]; then
        echo "Creating virtual environment..."
        $PYTHON_CMD -m venv "$VENV_NAME"
        echo "✓ Virtual environment created"
    fi
    
    source "$VENV_NAME/bin/activate"
    
    if [ ! -f "$VENV_NAME/.deps_installed" ]; then
        echo "Installing dependencies..."
        pip install -r requirements.txt -q
        touch "$VENV_NAME/.deps_installed"
        echo "✓ Dependencies installed"
    fi
}

run_python() {
    setup_env
    $PYTHON_CMD "$@"
}

# Helper function to offer saving data to file
offer_save() {
    local data_type="$1"
    echo ""
    if confirm_action_default_yes "Save $data_type to file?"; then
        echo "Saving $data_type to file..."
        run_python -c "
from reddit_bot import RedditBot
import datetime
try:
    filename = f'reddit_{data_type.lower().replace(' ', '_')}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json'
    print(f'✓ Data would be saved to: {filename}')
    print('(Note: Actual save functionality needs data context)')
except Exception as e:
    print(f'Error: {e}')
"
    fi
}

# === Profile & Account Functions ===
profile_view() {                                         # View your Reddit profile information
    echo "Getting your Reddit profile..."
    log "Retrieving Reddit profile"
    run_python -c "
from reddit_bot import RedditBot
import datetime
try:
    bot = RedditBot()
    user = bot.client.get_user_info()
    print()
    print('=== PROFILE INFORMATION ===')
    print(f'Username: {user[\"name\"]}')
    print(f'Comment Karma: {user[\"comment_karma\"]:,}')
    print(f'Link Karma: {user[\"link_karma\"]:,}')
    print(f'Total Karma: {user[\"total_karma\"]:,}')
    
    created = datetime.datetime.fromtimestamp(user['created_utc'])
    age = datetime.datetime.now() - created
    print(f'Account Age: {age.days} days ({age.days/365.25:.1f} years)')
    print(f'Email Verified: {\"Yes\" if user[\"has_verified_email\"] else \"No\"}')
    print(f'Gold Member: {\"Yes\" if user[\"is_gold\"] else \"No\"}')
    print(f'Moderator: {\"Yes\" if user[\"is_mod\"] else \"No\"}')
    print()
except Exception as e:
    print(f'Error: {e}')
"
}

profile_posts() {                                        # Get your recent posts and submissions
    echo "Retrieving your recent posts..."
    log "Retrieving user posts"
    run_python -c "
from reddit_bot import RedditBot
try:
    bot = RedditBot()
    # Get user's posts using Reddit API
    reddit = bot.client.reddit
    user = reddit.user.me()
    
    print()
    print('=== YOUR RECENT POSTS ===')
    posts = list(user.submissions.new(limit=10))
    for i, post in enumerate(posts, 1):
        print(f'{i:2}. {post.title[:70]}...')
        print(f'    r/{post.subreddit} | Score: {post.score} | Comments: {post.num_comments}')
        print(f'    Created: {post.created_utc}')
        print()
    
    print('=== YOUR RECENT COMMENTS ===')
    comments = list(user.comments.new(limit=5))
    for i, comment in enumerate(comments, 1):
        print(f'{i}. {comment.body[:100]}...')
        print(f'   Score: {comment.score} | r/{comment.subreddit}')
        print()
        
except Exception as e:
    print(f'Error: {e}')
"
}

# === Content Retrieval Functions ===
posts_get() {                                           # Retrieve posts from specified subreddit
    local subreddit="${1:-technology}"
    local limit="${2:-10}"
    local sort="${3:-hot}"
    
    echo "Getting posts from r/$subreddit..."
    log "Retrieving $limit posts from r/$subreddit (sort: $sort)"
    run_python -c "
from reddit_bot import RedditBot
try:
    bot = RedditBot()
    data = bot.retrieve_subreddit_data('$subreddit', sort_by='$sort', limit=$limit)
    print()
    print(f'=== r/{data[\"subreddit\"]} - {data[\"total_posts\"]} posts ===')
    for i, post in enumerate(data['posts'][:10], 1):
        print(f'{i:2}. {post[\"title\"][:70]}...')
        print(f'    Score: {post[\"score\"]} | Comments: {post[\"num_comments\"]} | Author: {post[\"author\"]}')
        print()
    
    if data.get('summary'):
        s = data['summary']
        print('=== SUMMARY ===')
        print(f'Average Score: {s.get(\"average_score\", 0):.1f}')
        print(f'Total Comments: {s.get(\"total_comments\", 0)}')
        print(f'Top Post: {s.get(\"top_post\", \"N/A\")[:60]}...')
    
    print()
    save_choice = input('Save this data to file? (y/N): ').strip().lower()
    if save_choice in ['y', 'yes']:
        filename = bot.save_data_to_file(data)
        print(f'✓ Data saved to: {filename}')
        
except Exception as e:
    print(f'Error: {e}')
"
}

posts_search() {                                        # Search posts with AI analysis
    local query="$1"
    local subreddit="$2"
    local limit="${3:-25}"
    
    if [ -z "$query" ]; then
        echo "Usage: posts_search <query> [subreddit] [limit]"
        return 1
    fi
    
    echo "Searching for: '$query'..."
    log "Searching for '$query' in ${subreddit:-all subreddits}"
    
    # Prepare subreddit parameter for Python
    local subreddit_param="None"
    if [ -n "$subreddit" ]; then
        subreddit_param="'$subreddit'"
    fi
    
    run_python -c "
from reddit_bot import RedditBot
try:
    bot = RedditBot()
    results = bot.search_and_analyze('$query', $subreddit_param, $limit)
    print()
    print(f'=== SEARCH RESULTS: {results[\"total_results\"]} found ===')
    print(f'Query: {results[\"query\"]}')
    if results.get('subreddit'):
        print(f'Subreddit: r/{results[\"subreddit\"]}')
    print()
    
    print('=== AI ANALYSIS ===')
    print(results['analysis'])
    print()
    
    print('=== TOP RESULTS ===')
    for i, post in enumerate(results['posts'][:5], 1):
        print(f'{i}. {post[\"title\"][:60]}...')
        print(f'   r/{post[\"subreddit\"]} | Score: {post[\"score\"]} | Comments: {post[\"num_comments\"]}')
        print()
    
    print()
    save_choice = input('Save search results to file? (y/N): ').strip().lower()
    if save_choice in ['y', 'yes']:
        filename = bot.save_data_to_file(results)
        print(f'✓ Search results saved to: {filename}')
        
except Exception as e:
    print(f'Error: {e}')
"
}

# === Automation Functions ===
comment_custom() {                                      # Post a custom comment to specific post
    local post_url="$1"
    local comment_text="$2"
    
    if [ -z "$post_url" ]; then
        echo "=== POST CUSTOM COMMENT ==="
        echo -n "Enter Reddit post URL or post ID: "
        read -r post_url
        if [ -z "$post_url" ]; then
            echo "Post URL cannot be empty."
            return
        fi
        
        echo -n "Enter your comment text: "
        read -r comment_text
        if [ -z "$comment_text" ]; then
            echo "Comment text cannot be empty."
            return
        fi
    fi
    
    echo "Posting custom comment..."
    log "Posting custom comment to $post_url"
    run_python -c "
from reddit_bot import RedditBot
try:
    bot = RedditBot()
    # Extract post ID from URL if needed
    post_url = '$post_url'
    if 'reddit.com' in post_url:
        try:
            post_id = post_url.split('/comments/')[1].split('/')[0]
        except:
            print('Invalid Reddit URL format')
            exit(1)
    else:
        post_id = post_url
    
    result = bot.client.post_comment(post_id, '$comment_text', validate=True)
    
    if result['success']:
        print(f'✓ Comment posted successfully!')
        print(f'  Comment ID: {result[\"comment_id\"]}')
        print(f'  Permalink: {result[\"permalink\"]}')
    else:
        print(f'✗ Failed to post comment: {result[\"error\"]}')
        
except Exception as e:
    print(f'Error: {e}')
"
}

comment_auto() {                                        # Auto-comment on subreddit posts
    local subreddit="$1"
    local count="${2:-3}"
    local sort="${3:-new}"
    
    if [ -z "$subreddit" ]; then
        echo "Usage: comment_auto <subreddit> [count] [sort]"
        return 1
    fi
    
    echo "WARNING: This will post AI-generated comments!"
    if ! confirm_action "Continue with auto-commenting on r/$subreddit?"; then
        echo "Operation cancelled."
        return
    fi
    
    echo "Auto-commenting on r/$subreddit..."
    log "Auto-commenting: $count comments on r/$subreddit"
    run_python -c "
from reddit_bot import RedditBot
try:
    bot = RedditBot()
    results = bot.auto_comment_on_posts('$subreddit', $count, '$sort')
    
    successful = sum(1 for r in results if r['success'])
    failed = len(results) - successful
    
    print()
    print(f'=== RESULTS: {successful} successful, {failed} failed ===')
    
    if successful > 0:
        print()
        print('SUCCESSFUL COMMENTS:')
        for result in results:
            if result['success']:
                print(f'  ✓ {result[\"post_title\"][:50]}...')
                print(f'    Comment ID: {result[\"comment_id\"]}')
    
    if failed > 0:
        print()
        print('FAILED COMMENTS:')
        for result in results:
            if not result['success']:
                print(f'  ✗ {result[\"post_title\"][:50]}...')
                print(f'    Error: {result[\"error\"]}')
        
except Exception as e:
    print(f'Error: {e}')
"
}

monitor_keywords() {                                    # Monitor subreddit for keywords
    local subreddit="$1"
    local keywords="$2"
    local duration="${3:-0.1}"
    local action="${4:-log}"
    
    if [ -z "$subreddit" ] || [ -z "$keywords" ]; then
        echo "Usage: monitor_keywords <subreddit> <keywords> [duration] [action]"
        return 1
    fi
    
    echo "Monitoring r/$subreddit for: $keywords..."
    log "Monitoring r/$subreddit for keywords: $keywords"
    run_python -c "
from reddit_bot import RedditBot
try:
    bot = RedditBot()
    keywords_list = '$keywords'.split(',')
    keywords_list = [k.strip() for k in keywords_list]
    
    results = bot.monitor_subreddit('$subreddit', keywords_list, '$action', $duration)
    
    print()
    print(f'=== MONITORING RESULTS ===')
    print(f'Subreddit: r/{results[\"subreddit\"]}')
    print(f'Keywords: {', '.join(results[\"keywords\"])}')
    print(f'Duration: {results[\"duration_hours\"]} hours')
    print(f'Matches Found: {results[\"total_matches\"]}')
    
    if results['matches']:
        print()
        print('KEYWORD MATCHES:')
        for match in results['matches'][:10]:
            print(f'  • \"{match[\"keyword\"]}\" in: {match[\"title\"][:50]}...')
        
except Exception as e:
    print(f'Error: {e}')
"
}

# === Statistics & Data Functions ===
stats_bot() {                                          # Show bot performance statistics
    echo "Getting bot statistics..."
    log "Retrieving bot statistics"
    run_python -c "
from reddit_bot import RedditBot
import datetime
try:
    bot = RedditBot()
    stats = bot.get_bot_stats()
    user_info = bot.client.get_user_info()
    
    print()
    print('=== BOT PERFORMANCE ===')
    print(f'Runtime: {stats[\"runtime_hours\"]:.1f} hours')
    print(f'Comments Posted: {stats[\"comments_posted\"]}')
    print(f'Posts Retrieved: {stats[\"posts_retrieved\"]}')
    print(f'Errors: {stats[\"errors\"]}')
    print(f'Success Rate: {stats[\"success_rate\"]:.1f}%')
    print(f'Started: {stats[\"start_time\"]}')
    print()
    
    print('=== ACCOUNT INFO ===')
    print(f'Username: {user_info[\"name\"]}')
    print(f'Total Karma: {user_info[\"total_karma\"]:,}')
    print(f'Comment Karma: {user_info[\"comment_karma\"]:,}')
    print(f'Link Karma: {user_info[\"link_karma\"]:,}')
    
    created = datetime.datetime.fromtimestamp(user_info['created_utc'])
    age = datetime.datetime.now() - created
    print(f'Account Age: {age.days} days ({age.days/365.25:.1f} years)')
    
except Exception as e:
    print(f'Error: {e}')
"
}

data_export() {                                        # Export bot data to JSON files
    echo "Exporting bot data..."
    log "Exporting bot data"
    run_python -c "
from reddit_bot import RedditBot
import datetime
try:
    bot = RedditBot()
    stats = bot.get_bot_stats()
    user_info = bot.client.get_user_info()
    
    export_data = {
        'export_timestamp': datetime.datetime.now().isoformat(),
        'bot_statistics': stats,
        'user_information': user_info
    }
    
    filename = bot.save_data_to_file(export_data, 'reddit_bot_export.json')
    print(f'✓ Data exported to: {filename}')
    
except Exception as e:
    print(f'Error: {e}')
"
}

# === Setup & Utility Functions ===
setup_install() {                                      # Install dependencies and setup environment
    echo "Setting up Reddit Bot environment..."
    log "Running environment setup"
    
    # Check Python
    if command -v python3 >/dev/null 2>&1; then
        echo "✓ Python 3 found: $(python3 --version)"
    else
        echo "✗ Python 3 not found. Please install Python 3.8+"
        return 1
    fi
    
    # Setup virtual environment and install deps
    setup_env
    
    # Test imports
    echo "Testing imports..."
    run_python -c "
try:
    import praw, agno, dotenv
    print('✓ All required packages imported successfully')
except ImportError as e:
    print(f'✗ Import error: {e}')
"
    
    echo "✓ Environment setup completed!"
}

test_connections() {                                   # Test Reddit and AI API connections
    echo "Testing API connections..."
    log "Testing API connections"
    run_python -c "
from reddit_bot import RedditBot
try:
    print('Testing Reddit API connection...')
    bot = RedditBot()
    user = bot.client.get_user_info()
    print(f'✓ Reddit API: Connected as {user[\"name\"]}')
    
    print('Testing Gemini AI connection...')
    test_response = bot.validator.validation_agent.run('Test connection')
    print(f'✓ Gemini AI: Connected - {test_response.content[:50]}...')
    
except Exception as e:
    print(f'✗ Connection test failed: {e}')
"
}

logs_view() {                                          # Show recent bot activity logs
    echo "=== RECENT BOT LOGS ==="
    if [ -f "$LOG_FILE" ]; then
        tail -20 "$LOG_FILE"
    else
        echo "No log file found at $LOG_FILE"
    fi
}

# === Interactive Functions ===
interactive_posts() {                                 # Interactive post retrieval with prompts
    echo "=== GET SUBREDDIT POSTS ==="
    echo -n "Enter subreddit name without r/ (default: technology): "
    read -r subreddit
    subreddit=${subreddit:-technology}
    
    echo -n "Number of posts (default: 10): "
    read -r limit
    limit=${limit:-10}
    
    echo -n "Sort by (hot/new/top/rising, default: hot): "
    read -r sort_by
    sort_by=${sort_by:-hot}
    
    posts_get "$subreddit" "$limit" "$sort_by"
}

interactive_search() {                                # Interactive search with prompts
    echo "=== SEARCH POSTS WITH AI ==="
    echo -n "Enter search query: "
    read -r query
    if [ -z "$query" ]; then
        echo "Search query cannot be empty."
        return
    fi
    
    echo -n "Enter subreddit without r/ (default: all subreddits): "
    read -r subreddit
    
    echo -n "Maximum results (default: 25): "
    read -r limit
    limit=${limit:-25}
    
    echo "Searching for: '$query'..."
    log "Searching for '$query' in ${subreddit:-all subreddits}"
    
    # Prepare subreddit parameter for Python - same logic as posts_search
    local subreddit_param="None"
    if [ -n "$subreddit" ]; then
        subreddit_param="'$subreddit'"
    fi
    
    run_python -c "
from reddit_bot import RedditBot
try:
    bot = RedditBot()
    results = bot.search_and_analyze('$query', $subreddit_param, $limit)
    print()
    print(f'=== SEARCH RESULTS: {results[\"total_results\"]} found ===')
    print(f'Query: {results[\"query\"]}')
    if results.get('subreddit'):
        print(f'Subreddit: r/{results[\"subreddit\"]}')
    print()
    
    print('=== AI ANALYSIS ===')
    print(results['analysis'])
    print()
    
    print('=== TOP RESULTS ===')
    for i, post in enumerate(results['posts'][:5], 1):
        print(f'{i}. {post[\"title\"][:60]}...')
        print(f'   r/{post[\"subreddit\"]} | Score: {post[\"score\"]} | Comments: {post[\"num_comments\"]}')
        print()
    
    print()
    save_choice = input('Save search results to file? (y/N): ').strip().lower()
    if save_choice in ['y', 'yes']:
        filename = bot.save_data_to_file(results)
        print(f'✓ Search results saved to: {filename}')
        
except Exception as e:
    print(f'Error: {e}')
"
}

interactive_comment() {                               # Interactive auto-commenting with prompts
    echo "=== AUTO-COMMENT ON POSTS ==="
    echo -n "Enter subreddit name without r/ (required): "
    read -r subreddit
    if [ -z "$subreddit" ]; then
        echo "Subreddit name cannot be empty."
        return
    fi
    
    echo -n "Enter number of comments (default 3): "
    read -r count
    count=${count:-3}
    
    echo -n "Sort posts by (new/hot/rising, default new): "
    read -r sort_by
    sort_by=${sort_by:-new}
    
    comment_auto "$subreddit" "$count" "$sort_by"
}

interactive_monitor() {                               # Interactive keyword monitoring with prompts
    echo "=== MONITOR KEYWORDS ==="
    echo -n "Enter subreddit name without r/ (required): "
    read -r subreddit
    if [ -z "$subreddit" ]; then
        echo "Subreddit name cannot be empty."
        return
    fi
    
    echo -n "Enter keywords (comma-separated): "
    read -r keywords
    if [ -z "$keywords" ]; then
        echo "Keywords cannot be empty."
        return
    fi
    
    echo -n "Enter monitoring duration in hours (default 0.1): "
    read -r duration
    duration=${duration:-0.1}
    
    echo -n "Action on matches (log/comment/both, default log): "
    read -r action
    action=${action:-log}
    
    monitor_keywords "$subreddit" "$keywords" "$duration" "$action"
}

# Display interactive menu
show_menu() {
    echo "=== 👤 Reddit Profile & Analysis ==="
    echo " 1. View Profile Information     ./run.sh profile-view        # Get detailed account stats, karma, and verification status"
    echo " 2. View Your Posts & Comments   ./run.sh profile-posts       # Show your recent submissions and comment history"
    echo ""
    echo "=== 📄 Content Retrieval & Analysis ==="
    echo " 3. Get Subreddit Posts          ./run.sh interactive-posts   # Guided post retrieval with smart defaults"
    echo " 4. Search Posts with AI         ./run.sh interactive-search  # AI-powered search with guided prompts"
    echo ""
    echo "=== 🤖 Automation & Posting ==="
    echo " 5. Post Custom Comment          ./run.sh comment-custom      # Post custom comment: ./run.sh comment-custom <post_url> '<text>'"
    echo " 6. Auto-Comment on Posts        ./run.sh interactive-comment # Guided auto-commenting with safety prompts"
    echo " 7. Monitor Keywords             ./run.sh interactive-monitor # Guided keyword monitoring setup"
    echo ""
    echo ""
    echo "=== 📊 Statistics & Data Management ==="
    echo " 8. Bot Performance Stats        ./run.sh stats-bot           # Show runtime stats, success rates, and account info"
    echo " 9. Export Data to JSON          ./run.sh data-export         # Export all bot data and statistics to files"
    echo "10. View Activity Logs           ./run.sh logs-view           # Display recent bot activity and error logs"
    echo ""
    echo "=== ⚙️ Setup & Configuration ==="
    echo "11. Install Dependencies         ./run.sh setup-install       # Setup virtual environment and install packages"
    echo "12. Test API Connections         ./run.sh test-connections    # Verify Reddit API and Gemini AI connectivity"
    echo ""
    echo "0. Exit Menu"
    echo "==========="
    echo ""
    read -p "Select option (0-12): " choice
    handle_menu_choice "$choice"
}

# Handle menu selection with return to menu
handle_menu_choice() {
    case "$1" in
        # Profile & Analysis
        1) profile_view; pause_return ;;
        2) profile_posts; pause_return ;;
        # Content Retrieval  
        3) interactive_posts; pause_return ;;
        4) interactive_search; pause_return ;;
        # Automation
        5) comment_custom; pause_return ;;
        6) interactive_comment; pause_return ;;
        7) interactive_monitor; pause_return ;;
        # Statistics & Data
        8) stats_bot; pause_return ;;
        9) data_export; pause_return ;;
        10) logs_view; pause_return ;;
        # Setup & Configuration
        11) setup_install; pause_return ;;
        12) test_connections; pause_return ;;
        0) echo "Exiting Reddit Bot..."; exit 0 ;;
        *) echo "Invalid option. Please select 0-12."; pause_return ;;
    esac
    # Return to menu after each operation
    show_menu
}

# Utility function to pause and return to menu
pause_return() {
    echo ""
    read -p "Press Enter to return to main menu..."
    clear
}



# Main entry point
main() {
    cd "$SCRIPT_DIR"
    
    if [[ $# -eq 0 ]]; then
        show_menu
    else
        case "$1" in
            # Profile & Analysis
            profile-view) profile_view ;;
            profile-posts) profile_posts ;;
            # Content Retrieval
            posts-get) posts_get "$2" "$3" "$4" ;;
            posts-search) posts_search "$2" "$3" "$4" ;;
            interactive-posts) interactive_posts ;;
            interactive-search) interactive_search ;;
            # Automation
            comment-custom) comment_custom "$2" "$3" ;;
            comment-auto) comment_auto "$2" "$3" "$4" ;;
            monitor-keywords) monitor_keywords "$2" "$3" "$4" "$5" ;;
            interactive-comment) interactive_comment ;;
            interactive-monitor) interactive_monitor ;;
            # Statistics & Data
            stats-bot) stats_bot ;;
            data-export) data_export ;;
            logs-view) logs_view ;;
            # Setup & Configuration
            setup-install) setup_install ;;
            test-connections) test_connections ;;
            # Legacy support
            profile|posts|search|comment|monitor|stats|setup|test|logs|export)
                echo "Legacy command detected. Use new format:"
                echo "  profile -> profile-view"
                echo "  posts -> posts-get"
                echo "  search -> posts-search"
                echo "  comment -> comment-auto"
                echo "  monitor -> monitor-keywords"
                echo "  stats -> stats-bot"
                echo "  setup -> setup-install"
                echo "  test -> test-connections"
                echo "  logs -> logs-view"
                echo "  export -> data-export"
                ;;
            *)
                echo "Usage: $0 [command] - Run without arguments to see all options"
                echo ""
                echo "Quick Commands:"
                echo "  profile-view      View Reddit profile information and account stats"
                echo "  profile-posts     Show your recent posts and comments"
                echo "  posts-get         Get subreddit posts: posts-get technology 10 hot"
                echo "  posts-search      Search with AI: posts-search 'AI news' technology 25"
                echo "  comment-auto      Auto-comment: comment-auto artificial 3 new"
                echo "  monitor-keywords  Monitor: monitor-keywords AI 'GPT,neural' 1 log"
                echo "  stats-bot         Show bot performance statistics"
                echo "  setup-install     Install dependencies and setup environment"
                echo "  test-connections  Test Reddit and AI API connectivity"
                echo ""
                echo "Interactive Commands:"
                echo "  interactive-posts    Guided post retrieval with prompts"
                echo "  interactive-search   Guided search with step-by-step setup"
                echo "  interactive-comment  Guided auto-commenting with safety checks"
                echo "  interactive-monitor  Guided keyword monitoring configuration"
                echo ""
                echo "Run './run.sh' without arguments for interactive menu"
                ;;
        esac
    fi
}

main "$@"