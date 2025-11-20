# pipeline.py
import glob, json, pathlib, datetime, math

RAW = pathlib.Path("data/raw")
CANDS = pathlib.Path("data/candidates")
CANDS.mkdir(parents=True, exist_ok=True)

def load_latest_raw():
    files = sorted(glob.glob(str(RAW/"raw_*.json")), reverse=True)
    items = []
    for f in files[:5]:
        items.extend(json.load(open(f, encoding="utf-8")).get("items", []))
    return items

def dedupe(items):
    seen = set()
    out = []
    for it in items:
        key = it["text"].strip().lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out

def score(item):
    return math.log(1 + item.get("likes", 0)) * 0.7 + math.log(1 + item.get("retweets", 0)) * 1.3

def run_pipeline():
    items = dedupe(load_latest_raw())
    for it in items:
        s = score(it)
        if s < 3: continue  # adjustable threshold

        cid = f"{int(datetime.datetime.utcnow().timestamp())}_{it['id']}"
        summary = it["text"][:250]

        cand = {
            "id": cid,
            "headline": summary[:80],
            "tweet_variants": [],
            "cluster_summary": summary,
            "sources": [{"url": it["url"], "author": it["author"]}],
            "media_urls": [],
            "created_at": datetime.datetime.utcnow().isoformat()
        }

        json.dump(cand, open(CANDS/f"{cid}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print("Created candidate:", cid)

if __name__ == "__main__":
    run_pipeline()
