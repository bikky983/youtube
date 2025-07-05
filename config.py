import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
if os.path.exists('.env'):
    load_dotenv()

# YouTube API credentials
CLIENT_SECRETS_FILE = "client_secret.json"
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

# File paths
POSTED_VIDEOS_FILE = "posted_videos.txt"
COMMENTS_FILE = "comments.txt"
ERROR_LOG_FILE = "error.log"
CHANNEL_IDS_FILE = "channel_ids.txt"

# Load channel IDs from file or environment variable
def load_channel_ids():
    # First try to get from environment variable
    if os.getenv("CHANNEL_IDS"):
        return os.getenv("CHANNEL_IDS").split(",")
    
    # If not in environment, try to load from file
    if os.path.exists(CHANNEL_IDS_FILE):
        with open(CHANNEL_IDS_FILE, 'r') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    # Default to empty list if no channel IDs found
    return []

CHANNEL_IDS = load_channel_ids()

# Comment delay in seconds (3 hours)
COMMENT_DELAY = 3 * 60 * 60  # 3 hours in seconds

# Maximum retries for failed API calls
MAX_RETRIES = 5

# Initial retry delay in seconds
INITIAL_RETRY_DELAY = 60 