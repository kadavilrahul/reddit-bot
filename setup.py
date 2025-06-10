#!/usr/bin/env python3
"""
Setup script for Reddit Bot
Helps with initial configuration and testing
"""
import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def install_dependencies():
    """Install required Python packages"""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def check_env_file():
    """Check if .env file exists and has required variables"""
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ .env file not found")
        return False
    
    required_vars = [
        "REDDIT_CLIENT_ID",
        "REDDIT_CLIENT_SECRET", 
        "REDDIT_USERNAME",
        "REDDIT_PASSWORD",
        "GEMINI_API_KEY"
    ]
    
    with open(env_path, 'r') as f:
        content = f.read()
    
    missing_vars = []
    for var in required_vars:
        if f"{var}=" not in content or f"{var}=YOUR_" in content:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing or incomplete environment variables: {', '.join(missing_vars)}")
        print("   Please update your .env file with actual credentials")
        return False
    
    print("✅ Environment variables configured")
    return True

def test_imports():
    """Test if all required modules can be imported"""
    print("🧪 Testing imports...")
    
    modules = [
        ("praw", "Reddit API client"),
        ("agno", "agno agent framework"),
        ("google.generativeai", "Google Generative AI"),
        ("dotenv", "Environment variable loader"),
        ("schedule", "Task scheduler")
    ]
    
    failed_imports = []
    
    for module, description in modules:
        try:
            __import__(module)
            print(f"   ✅ {module} - {description}")
        except ImportError:
            print(f"   ❌ {module} - {description}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\n❌ Failed to import: {', '.join(failed_imports)}")
        print("   Try running: pip install -r requirements.txt")
        return False
    
    return True

def test_reddit_connection():
    """Test Reddit API connection"""
    print("🔗 Testing Reddit API connection...")
    
    try:
        from config import Config
        Config.validate_config()
        
        import praw
        reddit = praw.Reddit(
            client_id=Config.REDDIT_CLIENT_ID,
            client_secret=Config.REDDIT_CLIENT_SECRET,
            username=Config.REDDIT_USERNAME,
            password=Config.REDDIT_PASSWORD,
            user_agent=Config.REDDIT_USER_AGENT
        )
        
        # Test authentication
        user = reddit.user.me()
        print(f"   ✅ Connected as: {user.name}")
        print(f"   📊 Comment Karma: {user.comment_karma:,}")
        print(f"   📊 Link Karma: {user.link_karma:,}")
        return True
        
    except Exception as e:
        print(f"   ❌ Reddit connection failed: {e}")
        return False

def test_gemini_connection():
    """Test Google Gemini API connection"""
    print("🤖 Testing Gemini AI connection...")
    
    try:
        from agno.models.google.gemini import Gemini
        from config import Config
        
        model = Gemini(
            id=Config.GEMINI_MODEL,
            api_key=Config.GEMINI_API_KEY
        )
        
        # Simple test
        from agno.agent import Agent
        test_agent = Agent(
            name="Test Agent",
            role="Test",
            model=model,
            instructions="You are a test agent. Respond with 'Connection successful!'"
        )
        
        response = test_agent.run("Test connection")
        print(f"   ✅ Gemini AI connected successfully")
        print(f"   🤖 Test response: {response.content[:50]}...")
        return True
        
    except Exception as e:
        print(f"   ❌ Gemini AI connection failed: {e}")
        return False

def create_sample_config():
    """Create a sample configuration file"""
    print("📝 Creating sample configuration...")
    
    sample_config = """
# Reddit Bot Configuration
# Copy this to .env and fill in your actual credentials

# Reddit API Credentials (from https://www.reddit.com/prefs/apps)
REDDIT_CLIENT_ID=your_reddit_client_id_here
REDDIT_CLIENT_SECRET=your_reddit_client_secret_here
REDDIT_USERNAME=your_reddit_username
REDDIT_PASSWORD=your_reddit_password
REDDIT_USER_AGENT=ScraperBot

# Google Gemini API (from https://makersuite.google.com/app/apikey)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_ENDPOINT=https://generativelanguage.googleapis.com/v1beta/models/
GEMINI_MODEL=gemini-2.0-flash-preview-05-20
"""
    
    with open(".env.sample", "w") as f:
        f.write(sample_config.strip())
    
    print("✅ Sample configuration created as .env.sample")

def main():
    """Main setup function"""
    print("🚀 Reddit Bot Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    # Test imports
    if not test_imports():
        return False
    
    # Check environment file
    if not check_env_file():
        create_sample_config()
        print("\n⚠️  Please configure your .env file with actual credentials")
        print("   1. Get Reddit API credentials from: https://www.reddit.com/prefs/apps")
        print("   2. Get Gemini API key from: https://makersuite.google.com/app/apikey")
        print("   3. Update .env file with your credentials")
        print("   4. Run setup.py again to test connections")
        return False
    
    # Test connections
    reddit_ok = test_reddit_connection()
    gemini_ok = test_gemini_connection()
    
    print("\n" + "=" * 50)
    print("SETUP SUMMARY")
    print("=" * 50)
    
    if reddit_ok and gemini_ok:
        print("✅ Setup completed successfully!")
        print("🎉 Your Reddit Bot is ready to use!")
        print("\nNext steps:")
        print("   • Run: python main.py")
        print("   • Or try examples: python example_usage.py")
        return True
    else:
        print("❌ Setup incomplete")
        if not reddit_ok:
            print("   • Fix Reddit API credentials")
        if not gemini_ok:
            print("   • Fix Gemini API credentials")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n👋 Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        sys.exit(1)