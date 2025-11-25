# trends_pipeline.py
import re
import asyncio
from datetime import datetime, timezone
from collections import defaultdict

from pytrends.request import TrendReq
from twikit import Client, Tweet

# trends_pipeline.py
import re
from pytrends.request import TrendReq
from pytrends.exceptions import ResponseError

from app.colored import cprint, Colors


def get_trend_keywords(top_n=40, dedupe=True):
    """
    Returns a list of keywords from Google Trends (India), prioritizing most recent.
    Robust fallback: realtime -> daily trending.
    """
    return ['pm modi', 'market']
    pytrends = TrendReq(hl='en-US', tz=330)

    titles = []
    try:
        # 1) Realtime (last 24h)
        df = pytrends.realtime_trending_searches(pn='IN')  # 'cat' arg can 404; omit it
        if df is not None and not df.empty:
            if 'title' in df.columns:
                titles = df['title'].dropna().astype(str).tolist()
            elif 'query' in df.columns:
                titles = df['query'].dropna().astype(str).tolist()
    except ResponseError:
        pass
    except Exception:
        pass

    if not titles:
        try:
            # 2) Daily trending as fallback (country name, not code)
            df2 = pytrends.trending_searches(pn='india')
            if df2 is not None and not df2.empty:
                # df2 is usually a single column of queries
                col = df2.columns[0]
                titles = df2[col].dropna().astype(str).tolist()
        except ResponseError:
            pass
        except Exception:
            pass

    # still nothing? return empty (caller can handle)
    if not titles:
        return []

    # clean + clamp
    cleaned = []
    for k in titles:
        k = re.sub(r'\s+', ' ', k).strip()
        if 2 <= len(k) <= 60:
            cleaned.append(k)

    if dedupe:
        seen, uniq = set(), []
        for k in cleaned:
            kl = k.lower()
            if kl in seen:
                continue
            seen.add(kl)
            uniq.append(k)
        cleaned = uniq

    return cleaned[:top_n]

# --- 2) Twitter search for each keyword (Twikit) ---
async def search_twitter_for_keywords(client: Client, keywords, per_keyword=6, min_like=20, min_rt=5):
    out = defaultdict(list)
    for kw in keywords:
        try:
            tweets = await client.search_tweet(kw, "Top", count=per_keyword)
        except Exception:
            continue
        for tw in tweets:
            if not isinstance(tw, Tweet): 
                continue
            if not tw.text: 
                continue
            if (tw.favorite_count or 0) < min_like and (tw.retweet_count or 0) < min_rt:
                continue
            txt = tw.text.replace("\n", " ").strip()
            media_urls = []
            if tw.media:
                for m in tw.media:
                    u = getattr(m, "media_url_https", None) or getattr(m, "url", None)
                    if u: media_urls.append(u)
            out[kw].append({
                "id": str(tw.id),
                "text": txt,
                "author": getattr(tw.user, "screen_name", None),
                "likes": int(getattr(tw, "favorite_count", 0) or 0),
                "retweets": int(getattr(tw, "retweet_count", 0) or 0),
                "replies": int(getattr(tw, "reply_count", 0) or 0),
                "timestamp": tw.created_at.isoformat() if getattr(tw, "created_at", None) else None,
                "url": f"https://x.com/{tw.user.screen_name}/status/{tw.id}" if getattr(tw, "user", None) else None,
                "media_urls": media_urls
            })
    return out  # dict[keyword] -> list[tweet dict]

# --- 3) Build raw_news items per keyword (aggregate top tweets) ---
def make_raw_news_from_cluster(keyword: str, tweets: list, top_k=5):
    # sort by simple virality
    scored = sorted(
        tweets,
        key=lambda t: (t["likes"]*0.7 + t["retweets"]*1.3 + t["replies"]*0.3),
        reverse=True
    )[:top_k]

    full_text = " ".join(t["text"] for t in scored)[:2000]
    headline_str = keyword[:120]

    media_urls = []
    for t in scored:
        media_urls.extend(t.get("media_urls", []))
    # dedupe media
    media_urls = list(dict.fromkeys(media_urls))

    # primary source = best tweet url if exists
    primary_url = next((t["url"] for t in scored if t.get("url")), None)

    return {
        "headline_str": headline_str,
        "full_text": full_text,
        "url": primary_url,
        "author": None,  # aggregated; leave None
        "likes": sum(t["likes"] for t in scored),
        "retweets": sum(t["retweets"] for t in scored),
        "replies": sum(t["replies"] for t in scored),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "media_urls": media_urls,
        "category_guess": guess_category(keyword, full_text),
        "sources": [
            {"url": t["url"], "author": t["author"], "timestamp": t["timestamp"]}
            for t in scored if t.get("url")
        ],
        "keyword": keyword
    }

def guess_category(keyword: str, text: str):
    k = f"{keyword} {text}".lower()
    if any(w in k for w in ["election", "minister", "assembly", "bjp", "congress", "rahul", "modi", "siddaramaiah", "bommai"]):
        return "politics"
    if any(w in k for w in ["startup", "tech", "ai", "software", "app", "nvidia", "apple", "google"]):
        return "tech"
    if any(w in k for w in ["match", "cricket", "t20", "odi", "football", "goal", "ipl"]):
        return "sports"
    if any(w in k for w in ["hospital", "vaccine", "virus", "health", "doctor"]):
        return "health"
    if any(w in k for w in ["market", "gdp", "stocks", "sensex", "nifty"]):
        return "business"
    return "other"

# --- 4) Orchestrator: trends -> twitter -> raw_news list ---
async def build_trends_news_items(client: Client, top_n_keywords=30, per_keyword=6, verbose=True):
    keywords = get_trend_keywords(top_n=top_n_keywords)
    if verbose:
        cprint(f" [TRENDS] Retrieved {len(keywords)} trending keywords.", color=Colors.Text.CYAN)
    clusters = await search_twitter_for_keywords(client, keywords, per_keyword=per_keyword)
    if verbose:
        total_tweets = sum(len(tws) for tws in clusters.values())
        cprint(f" [TWITTER] Retrieved a total of {total_tweets} tweets across {len(clusters)} keywords.", color=Colors.Text.CYAN)
    raw_items = []
    for kw, tws in clusters.items():
        if not tws: 
            continue
        raw_items.append(make_raw_news_from_cluster(kw, tws, top_k=min(5, len(tws))))
        if verbose:
            cprint(f" [CLUSTER] Keyword '{kw}' -> {len(tws)} tweets -> 1 raw news item.", color=Colors.Text.CYAN)
    return raw_items

# --- Function to search for trending news using Twikit ---
async def search_trending_news_on_x(client: Client, per_keyword=5, min_like=20, min_rt=5, verbose=True):
    """
    Works like build_trends_news_items in I/O:
      - Input: client, per_keyword, verbose (plus like/RT thresholds)
      - Output: list of raw_news dicts (same schema as make_raw_news_from_cluster)
    Internals: searches fixed trending hashtags instead of Google Trends.
    """
    trending_keywords = ["#BreakingNews", "#Trending", "#News", "#WorldNews", "#TopStory"]

    clusters = defaultdict(list)

    for keyword in trending_keywords:
        try:
            tweets = await client.search_tweet(keyword, "Top", count=per_keyword)
            if verbose:
                cprint(f" [TRENDING] Searching '{keyword}' -> {len(tweets) if tweets else 0} tweets.",
                       color=Colors.Text.YELLOW)
        except Exception as e:
            if verbose:
                cprint(f" [ERROR] Search failed for '{keyword}': {e}", color=Colors.Text.RED)
            continue

        if not tweets:
            continue

        for tw in tweets:
            try:
                if not isinstance(tw, Tweet):
                    continue
                if not getattr(tw, "text", None):
                    continue
                if (getattr(tw, "favorite_count", 0) or 0) < min_like and \
                   (getattr(tw, "retweet_count", 0) or 0) < min_rt:
                    continue

                txt = tw.text.replace("\n", " ").strip()
                media_urls = []
                if getattr(tw, "media", None):
                    for m in tw.media:
                        u = getattr(m, "media_url_https", None) or getattr(m, "url", None)
                        if u:
                            media_urls.append(u)

                clusters[keyword].append({
                    "id": str(tw.id),
                    "text": txt,
                    "author": getattr(tw.user, "screen_name", None),
                    "likes": int(getattr(tw, "favorite_count", 0) or 0),
                    "retweets": int(getattr(tw, "retweet_count", 0) or 0),
                    "replies": int(getattr(tw, "reply_count", 0) or 0),
                    "timestamp": tw.created_at.isoformat() if getattr(tw, "created_at", None) else None,
                    "url": f"https://x.com/{tw.user.screen_name}/status/{tw.id}" if getattr(tw, "user", None) else None,
                    "media_urls": media_urls
                })
            except Exception:
                continue

    if verbose:
        total = sum(len(v) for v in clusters.values())
        cprint(f" [TWITTER] Retrieved a total of {total} tweets across {len(clusters)} keywords.",
               color=Colors.Text.CYAN)

    raw_items = []
    for kw, tws in clusters.items():
        if not tws:
            continue
        raw_items.append(make_raw_news_from_cluster(kw, tws, top_k=min(5, len(tws))))
        if verbose:
            cprint(f" [CLUSTER] Keyword '{kw}' -> {len(tws)} tweets -> 1 raw news item.",
                   color=Colors.Text.CYAN)

    return raw_items
