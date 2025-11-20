# --- Config ---

from utils.colored import cprint, Colors

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

# ---- Colored Logs After Loading ENVs ----

def log_var(name, value, secure=False):
    """Pretty print env variables with status colors."""
    if value:
        disp = "*" * len(value) if secure else value
        color = Colors.Text.GREEN
    else:
        disp = "(missing)"
        color = Colors.Text.Bright.RED

    cprint(f"  {name:<22} : {disp}", color=color)


# ===== ENVIRONMENT CONFIG SUMMARY =====
cprint("\n" + "=" * 60, color=Colors.Text.Bright.BLUE)
cprint(" ENVIRONMENT CONFIGURATION SUMMARY ", color=Colors.Text.Bright.CYAN)
cprint("=" * 60, color=Colors.Text.Bright.BLUE)

cprint(" Sensitive Variables ", color=Colors.Text.Bright.YELLOW)
cprint("-" * 60, color=Colors.Text.Bright.YELLOW)

log_var("USERNAME", USERNAME)
log_var("EMAIL", EMAIL)
log_var("PASSWORD", PASSWORD, secure=True)
log_var("COOKIES_PATH", COOKIES_PATH)

cprint("\n General Settings ", color=Colors.Text.Bright.MAGENTA)
cprint("-" * 60, color=Colors.Text.Bright.MAGENTA)

cprint(f"  BOT_HANDLE             : {BOT_HANDLE}", color=Colors.Text.CYAN)
cprint(f"  DEBUG_MODE             : {DEBUG_MODE}", color=Colors.Text.CYAN)
cprint(f"  LAST_MENTION_FILE      : {LAST_MENTION_FILE}", color=Colors.Text.CYAN)
cprint(f"  MENTION_POLL_INTERVAL  : {MENTION_POLL_INTERVAL}s", color=Colors.Text.CYAN)
cprint(f"  INSIGHT_POST_INTERVAL  : {INSIGHT_POST_INTERVAL}s", color=Colors.Text.CYAN)

cprint("\n" + "=" * 60, color=Colors.Text.Bright.GREEN)
cprint(" ENVIRONMENT LOADING COMPLETE ", color=Colors.Text.Bright.GREEN)
cprint("=" * 60 + "\n", color=Colors.Text.Bright.GREEN)
