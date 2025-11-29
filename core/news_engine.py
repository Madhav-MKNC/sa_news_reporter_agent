# news engine

import requests

import xml.etree.ElementTree as ET

from core.colored import cprint, Colors


class NewsEngine:
    def __init__(self):
        cprint(" [ENGINE] NewsEngine Subsystem Initialized (RSS Mode).", color=Colors.Text.CYAN)
        # Namespace required to parse Google's custom XML tags
        self.namespaces = {'ht': 'https://trends.google.com/trends/trendingsearches/daily'}

    def get_trending_news_raw(self, verbose=True):
        if verbose: cprint(" [ENGINE] Connecting to Google Trends RSS Feed...", color=Colors.Text.BLUE)
        
        trending_news = []
        # The RSS feed is the most stable endpoint. geo=US can be changed to your target region.
        url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US"
        
        try:
            response = requests.get(url)
            if verbose: cprint(f" [ENGINE] HTTP Response: {response.status_code}", color=Colors.Text.YELLOW)
            
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                items = root.findall('.//item')
                
                if verbose: cprint(f" [ENGINE] Feed parsed. Found {len(items)} trending topics.", color=Colors.Text.MAGENTA)
                
                for item in items:
                    title = item.find('title').text
                    
                    # Extract news articles from the custom namespace tags
                    news_items_xml = item.findall('ht:news_item', self.namespaces)
                    articles = []
                    
                    for news in news_items_xml:
                        article_title = news.find('ht:news_item_title', self.namespaces).text
                        article_url = news.find('ht:news_item_url', self.namespaces).text
                        articles.append({
                            "title": article_title,
                            "url": article_url
                        })

                    # Map to your existing structure
                    news_item = {
                        "title": title,
                        # Use the first article's URL as the main URL, or None
                        "url": articles[0]['url'] if articles else None,
                        "articles": articles
                    }
                    
                    trending_news.append(news_item)
                    if verbose: cprint(f" [ENGINE] Extracted: {title}", color=Colors.Text.Bright.BLACK)

            else:
                cprint(f" [ENGINE] Error: RSS Feed returned status {response.status_code}", color=Colors.Text.RED)

        except Exception as e:
            cprint(f"[NEWS ENGINE] Failed to fetch trending news: {e}", color=Colors.Text.RED)
        
        if verbose: cprint(f" [ENGINE] Data collection complete. Yielding {len(trending_news)} items.", color=Colors.Text.GREEN)
        return trending_news



# # --- Insightful Scheduled Post (2) ---
# # NOTE: We will use google trends for sure
# def generate_insight_data():
#     queries = ["AI regulation", "Trump", "Fed interest rates", "elon"]
#     try:
#         response = requests.get("https://trends.google.com/trends/hottrends/visualize/internal/data")
#         if response.status_code == 200:
#             topics = response.json()
#             queries = random.sample(topics, k=min(len(topics), 5))
#     except:
#         pass
#     random.shuffle(queries)
#     for query in queries:
#         results = adj_news.semantic_search(query=query, limit=5)
#         if results: return results
#     return None


# def generate_insight_tweet():
#     market_data = generate_insight_data()
#     messages = [
#         {"role": "system", "content": POST_SYSTEM_PROMPT},
#         {"role": "user", "content": POST_PROMPT.format(market_data=market_data)}
#     ]
#     response = get_llm_response(messages)
#     # cprint(f"[Raw llm response]\n{response}", color=Colors.Text.WHITE)
#     try:
#         tweet_json = Parser().get_action(response)
#         # cprint(f"[Parsed]\n{json.dumps(dict(tweet_json), indent=4)}", color=Colors.Text.YELLOW)
#         if tweet_json['action'] == 'tweet':
#             return tweet_json['text']
#     except Exception as e:
#         cprint(f"[ERROR] Failed to parse LLM response for scheduled post: {e}", color=Colors.Text.RED)
#     return None




# # --- Function to search for trending news using Twikit ---
# async def search_trending_news():
#     try:
#         # Search for tweets using popular trending keywords (can be adjusted to match your needs)
#         trending_keywords = ["#BreakingNews", "#Trending", "#News", "#WorldNews", "#TopStory"]
#         trending_news = []

#         for keyword in trending_keywords:
#             try:
#                 # Search for tweets related to the keyword (you can change count to adjust the number of tweets to fetch)
#                 search_results = await client.search_tweet(keyword, "Latest", count=5)

#                 # Log the search results to see the tweets fetched
#                 cprint(f"[INFO] Searching for keyword: {keyword}", color=Colors.Text.YELLOW)
                
#                 if not search_results:
#                     cprint(f"[INFO] No results found for keyword: {keyword}", color=Colors.Text.RED)
#                     continue

#                 for tweet in search_results:
#                     # Log the tweet content for debugging
#                     tweet_text = tweet.full_text or tweet.text
#                     cprint(f"[TWEET LOG] {tweet.user.screen_name}: {tweet_text}", color=Colors.Text.CYAN)

#                     tweet_data = {
#                         "tweet": tweet_text,
#                         "author": tweet.user.screen_name,
#                         "url": f"https://twitter.com/{tweet.user.screen_name}/status/{tweet.id}"
#                     }
#                     trending_news.append(tweet_data)

#             except Exception as search_error:
#                 cprint(f"[ERROR] Failed to search tweets for keyword '{keyword}': {search_error}", color=Colors.Text.RED)
        
#         if not trending_news:
#             cprint("[ERROR] No trending news found.", color=Colors.Text.RED)

#         return trending_news

#     except Exception as e:
#         cprint(f"[ERROR] Failed to search trending news: {e}", color=Colors.Text.RED)
#         return None

