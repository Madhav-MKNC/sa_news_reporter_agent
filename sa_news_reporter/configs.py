# --- Config ---

import os
from dotenv import load_dotenv
load_dotenv()

USERNAME = os.getenv('TWITTER_USERNAME')
EMAIL = os.getenv('TWITTER_EMAIL')
PASSWORD = os.getenv('TWITTER_PASSWORD')
COOKIES_PATH = os.getenv('TWITTER_COOKIES_PATH')

BOT_HANDLE = os.getenv('BOT_HANDLE', 'pnp_agent')
DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() in ['true', '1', 'yes']

LAST_MENTION_FILE = os.getenv('LAST_MENTION_FILE', 'last_mention_id.txt')
MENTION_POLL_INTERVAL = int(os.getenv('MENTION_POLL_INTERVAL', 60))  # seconds
INSIGHT_POST_INTERVAL = int(os.getenv('INSIGHT_POST_INTERVAL', 1800))  # seconds

