# fetcher.py
import json, time, datetime, pathlib

RAW = pathlib.Path("data/raw")
RAW.mkdir(parents=True, exist_ok=True)

def fetch_trending():
    # TODO: Replace with working Twikit calls
    # Should return list of dicts:
    #   { "id": "...", "text": "...", "likes": int, "retweets": int, "url": "...", "author": "..." }
    items = []

    # TEST item (delete later)
    items.append({
        "id": f"t{int(time.time())}",
        "text": "Major update in Karnataka politics 🔥",
        "likes": 301,
        "retweets": 91,
        "url": "https://x.com/example/status/1",
        "author": "test_user"
    })

    out = {
        "fetched_at": datetime.datetime.utcnow().isoformat(),
        "items": items
    }
    fname = RAW / f"raw_{int(time.time())}.json"
    json.dump(out, open(fname, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("Fetched:", len(items))

if __name__ == "__main__":
    fetch_trending()
