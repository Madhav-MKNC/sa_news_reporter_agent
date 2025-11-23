import os
import time
import json
import random
import asyncio
import requests
import datetime

from twikit import Client

from app.configs import (
    BOT_HANDLE,
    COOKIES_PATH,
    NEWS_FETCH_INTERVAL
)
from app.news_engine import NewsEngine
from app.llms import get_llm_response
from app.llms.prompts import *
from app.llms.parser import Parser
from app.models import NewsModel
from app.colored import cprint, Colors
from app.utils import generate_filename


# --- Auth ---
client = Client('en-US')

# --- Initialize NewsEngine ---
news_engine = NewsEngine()


async def twikit_login():
    if os.path.exists(COOKIES_PATH):
        client.load_cookies(COOKIES_PATH)  # No await needed
        try:
            await client.refresh_auth()  # This is asynchronous, so we keep await here
            return
        except Exception:
            pass
    # You can use client.login() if needed
    # await client.login(
    #     auth_info_1=USERNAME,
    #     auth_info_2=EMAIL,
    #     password=PASSWORD,
    # )
    # await client.save_cookies(COOKIES_PATH)


# --- Get Trending News ---
def update_maal(verbose=True):
    trending_news = news_engine.get_trending_news()

    # store this in the datastore
    timestamp = datetime.now().strftime("%I_%M_%p_%d_%m_%Y")
    NEWS_DATA_STORE_DIR = "/data/"
    filepath = f"{NEWS_DATA_STORE_DIR.rstrip("/")}/{timestamp}.json"

    if not os.path.exists(NEWS_DATA_STORE_DIR):
        if verbose: cprint(f"[INFO] Creating Path: {NEWS_DATA_STORE_DIR}", color=Colors.Text.YELLOW) # verbosity
        os.makedirs(NEWS_DATA_STORE_DIR)

    if verbose: cprint(f"[INFO] Creating File: {filename}", color=Colors.Text.YELLOW) # verbosity

    filename = generate_filename()
    data = NewsModel(
        # NOTE: format the data
    )
    json_data = data.to_json()
    with open(filepath, 'w', encoding='utf-8') as file:
        json.dump(json_data, file)

    return trending_news


# --- Main Loop ---
async def main():
    await twikit_login()
    try:
        while True:
            cprint("[MAAL] Updating maal...", color=Colors.Text.CYAN)
            update_maal()
            await asyncio.sleep(NEWS_FETCH_INTERVAL)
    except KeyboardInterrupt:
        cprint("[END] Stopping bot due to keyboard interrupt.", color=Colors.Text.RED)


if __name__ == "__main__":
    asyncio.run(main())
