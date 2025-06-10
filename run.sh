#!/bin/bash
set -e

# Reddit Bot Setup and Execution Script
PROJECT_NAME="ScraperBot v1.0"
VENV_NAME="reddit_bot_env"
PYTHON_CMD="python3"
LOG_FILE="reddit_bot_setup.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging and output functions
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
    log "INFO: $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    log "SUCCESS: $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    log "WARNING: $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    log "ERROR: $1"
}

print_header() {
    echo -e "${BLUE}$1${NC}"
    log "$1"
}

# Check system requirements
check_requirements() {
    print_header "=== CHECKING SYSTEM REQUIREMENTS ==="
    
    # Check Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
        print_success "Python 3 found: $PYTHON_VERSION"
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2)
        if [[ $PYTHON_VERSION == 3.* ]]; then
            print_success "Python 3 found: $PYTHON_VERSION"
            PYTHON_CMD="python"
        else
            print_error "Python 3.8+ required, found: $PYTHON_VERSION"
            exit 1
        fi
    else
        print_error "Python not found. Please install Python 3.8+"
        exit 1
    fi
    
    # Check pip
    if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
        print_error "pip not found. Please install pip"
        exit 1
    fi
    
    print_success "System requirements check passed"
}

# Setup virtual environment
setup_virtual_environment() {
    print_header "=== SETTING UP VIRTUAL ENVIRONMENT ==="
    
    # Remove existing environment
    if [ -d "$VENV_NAME" ]; then
        print_info "Removing existing virtual environment..."
        rm -rf "$VENV_NAME"
    fi
    
    # Create new environment
    print_info "Creating virtual environment: $VENV_NAME"
    $PYTHON_CMD -m venv "$VENV_NAME"
    
    # Activate environment
    source "$VENV_NAME/bin/activate"
    print_success "Virtual environment created and activated"
    
    # Upgrade pip
    pip install --upgrade pip > /dev/null 2>&1
    print_success "pip upgraded to latest version"
}

# Install dependencies
install_dependencies() {
    print_header "=== INSTALLING DEPENDENCIES ==="
    
    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt not found"
        exit 1
    fi
    
    print_info "Installing packages from requirements.txt..."
    pip install -r requirements.txt
    
    if [ $? -eq 0 ]; then
        print_success "All dependencies installed successfully"
        print_info "Installed packages:"
        pip list --format=columns 2>/dev/null | head -15 2>/dev/null || pip list --format=columns 2>/dev/null
    else
        print_error "Failed to install dependencies"
        exit 1
    fi
}

# Check environment configuration
check_environment() {
    print_header "=== CHECKING ENVIRONMENT CONFIGURATION ==="
    
    if [ ! -f ".env" ]; then
        print_warning ".env file not found. Creating sample..."
        cat > .env << 'EOF'
# Reddit API Credentials
REDDIT_CLIENT_ID=your_reddit_client_id_here
REDDIT_CLIENT_SECRET=your_reddit_client_secret_here
REDDIT_USERNAME=your_reddit_username
REDDIT_PASSWORD=your_reddit_password
REDDIT_USER_AGENT=ScraperBot

# Google Gemini API
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_ENDPOINT=https://generativelanguage.googleapis.com/v1beta/models/
GEMINI_MODEL=gemini-2.0-flash-exp
EOF
        print_warning "Please update .env file with your actual credentials"
        return 1
    fi
    
    # Check for placeholder values
    if grep -q "your_.*_here" .env; then
        print_warning "Found placeholder values in .env file"
        print_info "Please update .env with your actual API credentials"
        return 1
    fi
    
    print_success "Environment configuration looks good"
    return 0
}

# Run setup verification
run_setup_verification() {
    print_header "=== RUNNING SETUP VERIFICATION ==="
    
    if [ -f "setup.py" ]; then
        print_info "Running setup verification..."
        $PYTHON_CMD setup.py
        
        if [ $? -eq 0 ]; then
            print_success "Setup verification passed"
        else
            print_warning "Setup verification completed with warnings"
        fi
    else
        print_warning "Setup script not found: setup.py"
    fi
    
    # Test agno integration
    if [ -f "test_agno.py" ]; then
        print_info "Testing agno integration..."
        $PYTHON_CMD test_agno.py
        
        if [ $? -eq 0 ]; then
            print_success "agno integration test passed"
        else
            print_warning "agno integration test failed"
        fi
    fi
}

# Show execution menu
show_execution_menu() {
    print_header "=== REDDIT BOT EXECUTION MENU ==="
    echo ""
    echo "Choose execution mode:"
    echo "1. Interactive Mode (Full Menu)"
    echo "2. Automated Mode (Quick Comment)"
    echo "3. Example/Demo Mode"
    echo "4. Exit"
    echo ""
}

# Execute bot
execute_bot() {
    while true; do
        show_execution_menu
        read -p "Enter your choice (1-4): " choice
        
        case $choice in
            1)
                print_info "Starting interactive mode..."
                $PYTHON_CMD main.py
                ;;
            2)
                print_info "Starting automated mode..."
                read -p "Enter subreddit name: " subreddit
                read -p "Enter number of comments (default 5): " num_comments
                num_comments=${num_comments:-5}
                $PYTHON_CMD -c "
from reddit_bot import RedditBot
bot = RedditBot()
bot.auto_comment_on_posts('$subreddit', $num_comments)
"
                ;;
            3)
                print_info "Running example/demo mode..."
                if [ -f "example_usage.py" ]; then
                    $PYTHON_CMD example_usage.py
                else
                    print_warning "example_usage.py not found"
                fi
                ;;
            4)
                print_info "Exiting..."
                break
                ;;
            *)
                print_warning "Invalid choice. Please enter 1-4."
                ;;
        esac
        
        echo ""
        read -p "Press Enter to continue or Ctrl+C to exit..."
        echo ""
    done
}

# Cleanup function
cleanup() {
    print_info "Cleaning up..."
    if [ -n "$VIRTUAL_ENV" ]; then
        deactivate 2>/dev/null || true
    fi
}

# Main execution
main() {
    # Set up cleanup trap
    trap cleanup EXIT
    
    # Show banner
    echo "=================================================="
    echo "🤖 $PROJECT_NAME - Setup & Execution"
    echo "=================================================="
    echo ""
    
    # Initialize log
    echo "Setup started at $(date)" > "$LOG_FILE"
    
    # Run setup steps
    check_requirements
    setup_virtual_environment
    install_dependencies
    
    # Check environment and run verification
    if check_environment; then
        run_setup_verification
        
        print_header "=== SETUP COMPLETE ==="
        print_success "✅ Reddit Bot is ready to use!"
        echo ""
        
        execute_bot
    else
        print_header "=== SETUP INCOMPLETE ==="
        print_warning "⚠️  Please update your .env file with valid credentials"
        print_info "Then run this script again"
    fi
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi