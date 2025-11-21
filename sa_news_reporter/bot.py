import os
import time
import json
import random
import asyncio
import requests

from twikit import Client

from .configs import (
    BOT_HANDLE,
    USERNAME,
    EMAIL,
    PASSWORD,
    COOKIES_PATH,
    MENTION_POLL_INTERVAL, 
    INSIGHT_POST_INTERVAL,
    LAST_MENTION_FILE
)
from news_engine import NewsEngine
from llms import get_llm_response
from llms.prompts import *
from llms.parser import Parser
from utils.colored import cprint, Colors


# --- Auth ---
client = Client('en-US')

# --- Initialize AdjNews ---
adj_news = NewsEngine()


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


# --- Insightful Scheduled Post (2) ---
# NOTE: We will use google trends for sure
def generate_insight_data():
    queries = ["AI regulation", "Trump", "Fed interest rates", "elon"]
    try:
        response = requests.get("https://trends.google.com/trends/hottrends/visualize/internal/data")
        if response.status_code == 200:
            topics = response.json()
            queries = random.sample(topics, k=min(len(topics), 5))
    except:
        pass
    random.shuffle(queries)
    for query in queries:
        results = adj_news.semantic_search(query=query, limit=5)
        if results: return results
    return None


def generate_insight_tweet():
    market_data = generate_insight_data()
    messages = [
        {"role": "system", "content": POST_SYSTEM_PROMPT},
        {"role": "user", "content": POST_PROMPT.format(market_data=market_data)}
    ]
    response = get_llm_response(messages)
    # cprint(f"[Raw llm response]\n{response}", color=Colors.Text.WHITE)
    try:
        tweet_json = Parser().get_action(response)
        # cprint(f"[Parsed]\n{json.dumps(dict(tweet_json), indent=4)}", color=Colors.Text.YELLOW)
        if tweet_json['action'] == 'tweet':
            return tweet_json['text']
    except Exception as e:
        cprint(f"[ERROR] Failed to parse LLM response for scheduled post: {e}", color=Colors.Text.RED)
    return None


# --- Function to post a "Hello World" tweet ---
async def post_hello_world():
    hello_text = "Hello, World! #HelloWorld"
    await client.create_tweet(text=hello_text)
    cprint(f"[Hello World Posted]\n{hello_text}", color=Colors.Text.LGREEN)


# --- Function to search for trending news using Twikit ---
async def search_trending_news():
    try:
        # Search for tweets using popular trending keywords (can be adjusted to match your needs)
        trending_keywords = ["#BreakingNews", "#Trending", "#News", "#WorldNews", "#TopStory"]
        trending_news = []

        for keyword in trending_keywords:
            try:
                # Search for tweets related to the keyword (you can change count to adjust the number of tweets to fetch)
                search_results = await client.search_tweet(keyword, "Latest", count=5)

                # Log the search results to see the tweets fetched
                cprint(f"[INFO] Searching for keyword: {keyword}", color=Colors.Text.YELLOW)
                
                if not search_results:
                    cprint(f"[INFO] No results found for keyword: {keyword}", color=Colors.Text.RED)
                    continue

                for tweet in search_results:
                    # Log the tweet content for debugging
                    tweet_text = tweet.full_text or tweet.text
                    cprint(f"[TWEET LOG] {tweet.user.screen_name}: {tweet_text}", color=Colors.Text.CYAN)

                    tweet_data = {
                        "tweet": tweet_text,
                        "author": tweet.user.screen_name,
                        "url": f"https://twitter.com/{tweet.user.screen_name}/status/{tweet.id}"
                    }
                    trending_news.append(tweet_data)

            except Exception as search_error:
                cprint(f"[ERROR] Failed to search tweets for keyword '{keyword}': {search_error}", color=Colors.Text.RED)
        
        if not trending_news:
            cprint("[ERROR] No trending news found.", color=Colors.Text.RED)

        return trending_news

    except Exception as e:
        cprint(f"[ERROR] Failed to search trending news: {e}", color=Colors.Text.RED)
        return None


# --- Main Loop ---
async def main():
    await twikit_login()
    last_insight_time = 0
    post_num = 1
    try:
        while True:
            # Post a Hello World tweet
            await search_trending_news()
            await asyncio.sleep(100)

            # # Post insight if interval elapsed
            # start = time.time()
            # if start - last_insight_time > INSIGHT_POST_INTERVAL:
            #     cprint(f"--- insightful post {post_num} ---", color=Colors.Text.YELLOW)
            #     await post_insight()
            #     last_insight_time = start
            #     post_num += 1
            # # Check for new mentions
            # new_mentions = await fetch_new_mentions()
            # for tweet_id, tweet in new_mentions:
            #     await handle_mention(tweet_id, tweet)
            #     set_last_mention_id(tweet_id)
            # end = time.time()
            # await asyncio.sleep(max(0, MENTION_POLL_INTERVAL - (end - start)))
    except KeyboardInterrupt:
        cprint("[INFO] Stopping bot due to keyboard interrupt.", color=Colors.Text.RED)


if __name__ == "__main__":
    asyncio.run(main())
