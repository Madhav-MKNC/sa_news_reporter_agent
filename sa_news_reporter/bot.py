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


# --- Data Persistence ---
def get_last_mention_id():
    if os.path.exists(LAST_MENTION_FILE):
        with open(LAST_MENTION_FILE, 'r', encoding='utf-8') as f:
            return f.read().strip()
    return None

def set_last_mention_id(mention_id):
    with open(LAST_MENTION_FILE, 'w', encoding='utf-8') as f:
        f.write(str(mention_id))


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


async def post_insight():
    cprint("[Insight] Generating tweet text...", color=Colors.Text.WHITE)
    text = generate_insight_tweet()
    if not text:
        cprint("[ERROR] No tweet text generated for scheduled post.", color=Colors.Text.RED)
        return
    await client.create_tweet(text=text)
    cprint(f"[Insight Posted]\n{text}", color=Colors.Text.LGREEN)


# --- Mention Handling --- (3)
async def fetch_new_mentions():
    cprint("[Mentions] Fetching new mentions...", color=Colors.Text.YELLOW)
    last_id = get_last_mention_id()
    result = await client.search_tweet(f"@{BOT_HANDLE}", "Latest", count=20)
    new_mentions = []
    for tweet in result:
        tweet_id = str(tweet.id)
        if last_id and int(tweet_id) <= int(last_id):
            continue
        tweet_text = (tweet.full_text or tweet.text or "").strip()
        lowered = tweet_text.lower()
        bot_tag = f"@{BOT_HANDLE.lower()}"
        # Only include tweets that start with your tag
        if lowered.startswith(bot_tag) or lowered.startswith(f".{bot_tag}") or lowered.startswith(f" {bot_tag}"):
            cprint(f"[Mention] {tweet.user.screen_name}: {tweet_text}", color=Colors.Text.CYAN)
            new_mentions.append((tweet_id, tweet))
    # Sort by tweet_id ascending (oldest first)
    new_mentions.sort(key=lambda x: int(x[0]))
    return new_mentions


# --- Mention Reply Logic ---
async def handle_mention(tweet_id, tweet):
    # # --- (1) ---
    # author_handle = tweet.get('user', {}).get('screen_name', '')
    # tweet_text = tweet.get('full_text', '').replace(f'@{BOT_HANDLE}', '').strip()
    # cprint(f"[Mention] New mention from @{author_handle}: {tweet_text}", color=Colors.Text.MAGENTA)

    # --- (2) ---
    author_handle = tweet.user.screen_name or ""
    tweet_text = tweet.full_text or tweet.text or ""
    cprint(f"[Mention] New mention from @{author_handle}: {tweet_text}", color=Colors.Text.MAGENTA)

    messages = [
        {"role": "system", "content": REPLY_SYSTEM_PROMPT},
        {"role": "user", "content": REPLY_PROMPT.format(author_handle=author_handle, tweet_text=tweet_text)}
    ]
    response = get_llm_response(messages)
    messages.append({"role": "assistant", "content": response})
    # cprint(f"[Raw llm response]\n{response}", color=Colors.Text.WHITE)

    try:
        action_json = Parser().get_action(response)
        # cprint(f"[Parsed]\n{json.dumps(dict(action_json), indent=4)}", color=Colors.Text.YELLOW)
    except Exception as e:
        cprint(f"[ERROR] Failed to parse LLM response: {e}", color=Colors.Text.RED)
        return

    if action_json['action'] == 'tweet':
        reply_text = action_json['text']
        await client.create_tweet(text=reply_text, reply_to=tweet_id)
        cprint(f"[Reply] @{author_handle}: {reply_text}", color=Colors.Text.LGREEN)

    elif action_json['action'] == 'research':
        cprint(f"[Research] Function: {action_json['function']}", color=Colors.Text.YELLOW)
        params = action_json['params']

        if action_json['function'] == 'semantic_search':
            results = adj_news.semantic_search(
                query=params.get('query'),
                limit=int(params.get('limit', 10)),
                include_context=bool(params.get('include_context', False))
            )

        elif action_json['function'] == 'list_markets':
            results = adj_news.list_markets(
                limit=params.get('limit', 5),
                offset=params.get('offset', 0),
                platform=params.get('platform', None),
                status=params.get('status', None),
                category=params.get('category', None),
                market_type=params.get('market_type', None),
                keyword=params.get('keyword', None),
                tag=params.get('tag', None),
                created_after=params.get('created_after', None),
                created_before=params.get('created_before', None),
                probability_min=params.get('probability_min', None),
                probability_max=params.get('probability_max', None),
                sort_by=params.get('sort_by', None),
                sort_dir=params.get('sort_dir', None),
                include_closed=params.get('include_closed', None),
                include_resolved=params.get('include_resolved', None)
            )

        elif action_json['function'] == "get_market_news":
            results = adj_news.get_market_news(
                market = params.get('market'),
                days = int(params.get('days', 7)),
                limit = int(params.get('limit', 5)),
                exclude_domains = params.get('exclude_domains', None)
            )

        else:
            cprint(f"[ERROR] Unknown research function: {action_json['function']}", color=Colors.Text.RED)
            return

        messages.append(
            {
                "role": "user", 
                "content": REPLY_FOLLOW_UP_PROMPT.format(
                    action_results=str(results), 
                    author_handle=author_handle
                )
            }
        )
        reply = get_llm_response(messages)
        cprint(f"[Follow-up LLM response]\n{reply}", color=Colors.Text.YELLOW)

        try:
            tweet_json = Parser().get_action(reply)
            # cprint(f"[Parsed]\n{json.dumps(dict(tweet_json), indent=4)}", color=Colors.Text.YELLOW)
            if tweet_json['action'] == 'tweet':
                await client.create_tweet(text=tweet_json['text'], reply_to=tweet_id)
                cprint(f"[Reply] @{author_handle}: {tweet_json['text']}", color=Colors.Text.LGREEN)
        except Exception as e:
            cprint(f"[ERROR] Failed to reply: {e}", color=Colors.Text.RED)


# --- Function to post a "Hello World" tweet ---
async def post_hello_world():
    hello_text = "Hello, World! #HelloWorld"
    await client.create_tweet(text=hello_text)
    cprint(f"[Hello World Posted]\n{hello_text}", color=Colors.Text.LGREEN)

# --- Function to fetch latest trending news from Explore section using Twikit ---
# --- Function to search for trending news using Twikit ---
# --- Function to search for trending news using Twikit ---
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
