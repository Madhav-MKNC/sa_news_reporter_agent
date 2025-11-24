import os
import json
import asyncio
from time import sleep

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


def write_and_save_full_news(raw_news: dict, verbose=True):
    messages = [
        {"role": "system", "content": NEWS_GENERATE_SYSTEM_PROMPT},
        {"role": "user", "content": NEWS_GENERATE_PROMPT.format(raw_news=raw_news)}
    ]

    response = get_llm_response(messages)
    news_json = Parser().get_news_json(response)
    
    if verbose:
        cprint(f"[LLM] Raw Response:\n{response}", color=Colors.Text.CYAN)
        cprint(f"[PARSER] Parsed News JSON:\n{json.dumps(dict(news_json), indent=4)}", color=Colors.Text.MAGENTA)

    news_item = NewsItemModel.from_dict(news_json)
    news_item.create_dir()
    news_item.save_json()
    
    if verbose:
        cprint(f"[MAAL] Saved News Item: {news_item.id}", color=Colors.Text.GREEN)


# --- Get Trending News ---
def update_maal(verbose=True):
    trending_news = news_engine.get_trending_news_raw()
    for raw_news in trending_news:
        if verbose: cprint(f"[MAAL] Processing News: {raw_news['headline_str']}", color=Colors.Text.GREEN)
        write_and_save_full_news(raw_news, verbose=verbose)


# --- Main Loop ---
async def main():
    await twikit_login()
    try:
        while True:
            cprint("[MAAL] Updating maal...", color=Colors.Text.YELLOW)
            update_maal()
            sleep(NEWS_FETCH_INTERVAL)
    except KeyboardInterrupt:
        cprint("[END] Stopping bot due to keyboard interrupt.", color=Colors.Text.RED)


if __name__ == "__main__":
    asyncio.run(main())
