# --- Config ---

from app.colored import cprint, Colors

import os
from dotenv import load_dotenv
load_dotenv()

USERNAME = os.getenv('TWITTER_USERNAME')
PASSWORD = os.getenv('TWITTER_PASSWORD')
COOKIES_PATH = os.getenv('TWITTER_COOKIES_PATH')

BOT_HANDLE = USERNAME
DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() in ['true', '1', 'yes']
NEWS_FETCH_INTERVAL = int(os.getenv('NEWS_FETCH_INTERVAL', 600))  # 10 minutes
NEWS_DATA_STORE_DIR = os.getenv('NEWS_DATA_STORE_DIR')

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
log_var("PASSWORD", PASSWORD, secure=True)
log_var("COOKIES_PATH", COOKIES_PATH)

cprint("\n General Settings ", color=Colors.Text.Bright.MAGENTA)
cprint("-" * 60, color=Colors.Text.Bright.MAGENTA)

cprint(f"  BOT_HANDLE             : {BOT_HANDLE}", color=Colors.Text.CYAN)
cprint(f"  DEBUG_MODE             : {DEBUG_MODE}", color=Colors.Text.CYAN)
cprint(f"  NEWS_FETCH_INTERVAL      : {NEWS_FETCH_INTERVAL}", color=Colors.Text.CYAN)
cprint(f"  NEWS_DATA_STORE_DIR    : {NEWS_DATA_STORE_DIR}", color=Colors.Text.CYAN)

cprint("\n" + "=" * 60, color=Colors.Text.Bright.GREEN)
cprint(" ENVIRONMENT LOADING COMPLETE ", color=Colors.Text.Bright.GREEN)
cprint("=" * 60 + "\n", color=Colors.Text.Bright.GREEN)
