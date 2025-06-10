# Reddit Bot with AI Integration

AI-powered Reddit bot using Google Gemini and agno agent for intelligent content validation and automated commenting.

## Installation & Usage

**System Requirements:**
- Linux, macOS, or Windows (with Git Bash/WSL)
- Python 3.8 or higher
- pip (Python package manager)
- Internet connection for API access

**API Credentials Required:**
- Reddit API credentials (Client ID, Client Secret, Username, Password)
- Google Gemini API key

### Installation Steps

1. **Download and setup the project:**

```bash
git clone https://github.com/kadavilrahul/reddit-bot.git
```

```bash
cd reddit-bot
```

2. **Run the automated setup and execution:**
```bash
bash run.sh
```

The `run.sh` script will automatically:
- Check system requirements (Python 3.8+, pip)
- Create and activate a virtual environment
- Install all required dependencies from `requirements.txt`
- Create a sample `.env` file if one doesn't exist
- Run setup verification tests
- Launch the interactive bot menu

### API Credentials Setup

When you first run `bash run.sh`, it will create a `.env` file with placeholder values. Update this file with your actual credentials:

**Reddit API Setup:**
1. Go to [Reddit App Preferences](https://www.reddit.com/prefs/apps)
2. Click "Create App" → Choose "script" type
3. Note your Client ID and Client Secret
4. Update `.env` file with your Reddit credentials

**Google Gemini API Setup:**
1. Get your API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Update `GEMINI_API_KEY` in `.env` file

**Example `.env` file:**
```bash
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
```

### Usage Examples

**1. Interactive Mode (Recommended):**
```bash
bash run.sh
# Select option 1 from the menu
```

**2. Quick Automated Commenting:**
```bash
bash run.sh
# Select option 2, then enter subreddit name and comment count
```

**3. Demo/Example Mode:**
```bash
bash run.sh
# Select option 3 to run example scripts
```

### Verification Commands

**Check if installation worked:**
```bash
# Activate the virtual environment
source reddit_bot_env/bin/activate

# Test imports
python -c "import praw, agno; print('✅ All packages installed correctly')"

# Test configuration
python -c "from config import Config; print('✅ Configuration loaded successfully')"
```

## File Organization

```
reddit-bot/
├── run.sh                 # Main execution script (use this to run the bot)
├── main.py                # Interactive menu application
├── reddit_bot.py          # Core bot functionality and orchestration
├── reddit_client.py       # Reddit API client wrapper
├── validators.py          # AI content validation using agno agent
├── config.py             # Configuration management
├── setup.py              # Setup verification and testing
├── example_usage.py      # Usage examples and demos
├── requirements.txt      # Python dependencies
├── .env                 # Environment variables (created automatically)
└── reference/
    └── agno_usage.txt    # agno agent usage reference
```

## Features

- **Automated Commenting**: Generate and post AI-powered comments using Google Gemini
- **Content Validation**: agno agent integration for safety and appropriateness checking
- **Data Retrieval**: Extract comprehensive data from subreddits and posts
- **Search & Analysis**: Search Reddit posts with AI-powered analysis
- **Keyword Monitoring**: Monitor subreddits for specific keywords with automated actions
- **Rate Limiting**: Built-in protection against API abuse
- **Interactive Menu**: User-friendly command-line interface

**Key Files:**
- **`run.sh`**: Main script - handles setup, dependencies, and execution
- **`validators.py`**: agno agent integration for AI-powered content validation
- **`reddit_bot.py`**: Core bot logic and Reddit operations
- **`.env`**: Configuration file (auto-created, needs your API credentials)

## Troubleshooting

### Common Issues and Solutions

**1. Permission Denied Error:**
```bash
chmod +x run.sh
bash run.sh
```

**2. Python Version Issues:**
```bash
# Check Python version
python3 --version
# Should be 3.8 or higher

# If python3 not found, install Python 3.8+
# Ubuntu/Debian: sudo apt update && sudo apt install python3 python3-pip
# macOS: brew install python3
# Windows: Download from python.org
```

**3. Virtual Environment Issues:**
```bash
# Remove existing environment and recreate
rm -rf reddit_bot_env
bash run.sh
```

**4. Dependency Installation Failures:**
```bash
# Check internet connection and try again
# Or manually install dependencies:
source reddit_bot_env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

**5. API Connection Issues:**
- Verify your `.env` file has actual credentials (not placeholder values)
- Test Reddit API: Go to [Reddit App Preferences](https://www.reddit.com/prefs/apps) and verify your app
- Test Gemini API: Visit [Google AI Studio](https://makersuite.google.com/app/apikey) and verify your key

**6. agno Integration Issues:**
```bash
# Test agno installation
source reddit_bot_env/bin/activate
python -c "from agno.agent import Agent; from agno.models.google.gemini import Gemini; print('✅ agno working')"
```

### Log Files

Check `reddit_bot_setup.log` for detailed error information:
```bash
tail -f reddit_bot_setup.log
```

### Manual Recovery

If automated setup fails, you can run components manually:
```bash
# Create virtual environment
python3 -m venv reddit_bot_env
source reddit_bot_env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run setup verification
python setup.py

# Run main application
python main.py
```

## Tested Environments

- **Ubuntu 20.04/22.04** - Fully tested ✅
- **macOS 12+** - Tested ✅  
- **Windows 10/11** (Git Bash/WSL) - Tested ✅
- **Python 3.8, 3.9, 3.10, 3.11** - Compatible ✅

## Configuration

### Bot Behavior Settings

Edit `config.py` to customize:
- Rate limiting delays
- Comment length limits
- Maximum posts per request
- Validation settings

### Advanced Usage

**Environment Variables:**
- `REDDIT_USER_AGENT`: Custom user agent string
- `GEMINI_MODEL`: Specific Gemini model to use
- `RATE_LIMIT_DELAY`: Delay between API calls (seconds)

## Safety Features

- **Content Validation**: All comments validated by AI before posting
- **Rate Limiting**: Automatic delays prevent API abuse
- **Policy Compliance**: Reddit guidelines checking
- **Error Handling**: Comprehensive error recovery
- **Logging**: Detailed operation logs for monitoring

## Support

For issues:
1. Check the troubleshooting section above
2. Review `reddit_bot_setup.log` for detailed errors
3. Verify your API credentials are correct
4. Ensure Python 3.8+ is installed

**Quick Start Command:**
```bash
bash run.sh
```

This single command handles everything from setup to execution!