import os
import json
import asyncio
import time

from twikit import Client

from app.configs import (
    COOKIES_PATH,
    NEWS_FETCH_INTERVAL,
)
from app.news_engine import NewsEngine
from app.llms import get_llm_response
from app.llms.prompts import NEWS_GENERATE_SYSTEM_PROMPT, NEWS_GENERATE_PROMPT
from app.llms.parser import Parser
from app.models import NewsItemModel
from app.colored import cprint, Colors
from app.trends_pipeline import build_trends_news_items, search_trending_news_on_x


# --- Auth ---
client = Client('en-US')

# --- Initialize NewsEngine ---
news_engine = NewsEngine()


async def twikit_login():
    cprint(" [AUTH] Initializing authentication sequence...", color=Colors.Text.CYAN)
    if os.path.exists(COOKIES_PATH):
        cprint(f" [AUTH] Loading cookies from: {COOKIES_PATH}", color=Colors.Text.YELLOW)
        client.load_cookies(COOKIES_PATH)  # No await needed
        try:
            await client.refresh_auth()  # This is asynchronous, so we keep await here
            return
        except Exception as e:
            pass
    else:
        cprint(" [AUTH] No cookies found at path.", color=Colors.Text.RED)
    # You can use client.login() if needed
    # await client.login(
    #     auth_info_1=USERNAME,
    #     auth_info_2=EMAIL,
    #     password=PASSWORD,
    # )
    # await client.save_cookies(COOKIES_PATH)


def write_and_save_full_news(raw_news: dict, verbose=True):
    cprint(f" [PROCESS] Processing news item: {raw_news.get('headline_str', 'Unknown')[:50]}...", color=Colors.Text.BLUE)
    messages = [
        {"role": "system", "content": NEWS_GENERATE_SYSTEM_PROMPT},
        {"role": "user", "content": NEWS_GENERATE_PROMPT.format(raw_news=raw_news)}
    ]

    if verbose:
        cprint(" [LLM] Dispatching request to LLM...", color=Colors.Text.MAGENTA)

    response = get_llm_response(messages)

    if verbose:
        cprint(f"[LLM] Raw Response:\n{response}", color=Colors.Text.CYAN)

    news_json = Parser().get_news_json(response)

    if verbose:
        cprint(f"[PARSER] Parsed News JSON:\n{json.dumps(dict(news_json), indent=4)}", color=Colors.Text.MAGENTA)

    news_item = NewsItemModel.from_dict(news_json)
    news_item.create_dir()
    cprint(" [SYSTEM] Saving news data to disk...", color=Colors.Text.YELLOW)
    news_item.save_json()
    
    if verbose:
        cprint(f"[MAAL] Saved News Item: {news_item.id}", color=Colors.Text.GREEN)
    cprint(" [PROCESS] Item processing completed.", color=Colors.Text.GREEN)


# --- Get Trending News ---
def update_maal(verbose=True):
    cprint(" [ENGINE] Fetching trending news feed...", color=Colors.Text.CYAN)
    trending_news = news_engine.get_trending_news_raw(verbose=True)
    cprint(f" [ENGINE] Retrieved {len(trending_news)} trending items.", color=Colors.Text.GREEN)
    for raw_news in trending_news:
        if verbose: cprint(f"[MAAL] Processing News: {raw_news['headline_str']}", color=Colors.Text.GREEN)
        write_and_save_full_news(raw_news, verbose=verbose)


async def update_from_trends(verbose=True):
    # raw_items = await build_trends_news_items(client, top_n_keywords=30, per_keyword=6)
    raw_items = await search_trending_news_on_x(client, per_keyword=6, verbose=verbose)
    if verbose:
        cprint(f" [ENGINE] Retrieved {len(raw_items)} news items from trends.", color=Colors.Text.GREEN)
    for raw_news in raw_items:
        if verbose:
            cprint(f"[MAAL] From Trends kw='{raw_news['keyword']}'", color=Colors.Text.GREEN)
        write_and_save_full_news(raw_news, verbose=verbose)


# --- Main Loop ---
async def main():
    await twikit_login()
    cprint(" [BOT] Login sequence finished.", color=Colors.Text.GREEN)
    try:
        while True:
            cprint("[MAAL] Updating maal...", color=Colors.Text.YELLOW)
            # update_maal()
            await update_from_trends()

            # COUNTDOWN
            for i in range(NEWS_FETCH_INTERVAL, 0, -1):
                # Generate the # symbols, starting with NEWS_FETCH_INTERVAL and decreasing
                hashes = "#" * i
                # Print the countdown with the decreasing number of hashes
                print(f"  {i:0{len(str(NEWS_FETCH_INTERVAL))}d} seconds...", end='\r')
                time.sleep(1)
    except KeyboardInterrupt:
        cprint("[END] Stopping bot due to keyboard interrupt.", color=Colors.Text.RED)


if __name__ == "__main__":
    cprint(" [BOT] System Startup.", color=Colors.Text.Bright.WHITE, bg_color=Colors.Background.BLUE)
    asyncio.run(main())
