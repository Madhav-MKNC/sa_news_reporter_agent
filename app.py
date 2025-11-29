import os
import json
import shutil
import asyncio
from uuid import uuid4
import pandas as pd
import urllib.parse
from datetime import datetime
from collections import Counter
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify

from twikit import Client

# Import your existing modules
from core.bot import update_from_trends, twikit_login
from core.configs import NEWS_DATA_STORE_DIR
from core.colored import cprint, Colors

app = Flask(__name__)
app.secret_key = str(uuid4())


# --- Auth ---
client = Client('en-US')



# --- HELPERS ---


def safe_parse_timestamp(ts_str):
    if not ts_str:
        return datetime.now()
    try:
        return datetime.fromisoformat(ts_str)
    except Exception:
        try:
            clean_ts = ts_str.split('+')[0].split('.')[0].replace('Z', '')
            return datetime.strptime(clean_ts, "%Y-%m-%dT%H:%M:%S")
        except:
            return datetime.now()


def get_relative_time(dt):
    if dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None:
        now = datetime.now(dt.tzinfo)
    else:
        now = datetime.now()

    diff = now - dt
    s = diff.total_seconds()

    if s < 60:
        return "Just now"
    if s < 3600:
        return f"{int(s//60)}m ago"
    if s < 86400:
        return f"{int(s//3600)}h ago"
    if s < 604800:
        return f"{int(s//86400)}d ago"
    return dt.strftime("%Y-%m-%d")


def to_bold_unicode(text):
    if not text:
        return ""
    normal = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    bold = "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟕𝟴𝟵"
    return text.translate(str.maketrans(normal, bold))


def load_data():
    items = []
    if not os.path.exists(NEWS_DATA_STORE_DIR):
        return []

    folders = os.listdir(NEWS_DATA_STORE_DIR)
    for folder in folders:
        folder_path = os.path.join(NEWS_DATA_STORE_DIR, folder)
        json_path = os.path.join(folder_path, "data.json")

        if not os.path.exists(json_path):
            continue

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            item_id = data.get("id", folder)
            dt = safe_parse_timestamp(data.get("timestamp_str"))

            # Tags
            raw_tags = data.get("tags_list", [])
            if isinstance(raw_tags, str):
                raw_tags = raw_tags.split()
            tags = [str(t).replace("#", "").strip() for t in raw_tags if t]

            # Sources
            raw_sources = data.get("source_list", [])
            if isinstance(raw_sources, str):
                raw_sources = raw_sources.split()
            sources = [str(s) for s in raw_sources if s]

            # Twitter Intent
            headline = data.get("headline_str") or "Untitled"
            content = data.get("content_str") or ""
            tweet_body = f"{to_bold_unicode(headline)}\n\n{content}\n\n" + \
                " ".join([f"#{t}" for t in tags])
            x_intent = "https://x.com/intent/tweet?text=" + \
                urllib.parse.quote(tweet_body)

            items.append({
                "id": item_id,
                "headline": headline,
                "content": content,
                "tags": tags,
                "sources": sources,
                "datetime": dt,
                "display_time": get_relative_time(dt),
                "fmt_time": dt.strftime('%b %d, %I:%M %p'),
                "x_link": x_intent
            })
        except Exception as e:
            print(f"Skipped {folder}: {e}")
            continue

    # Sort items (Newest first)
    items.sort(key=lambda x: x['datetime'], reverse=True)
    return items

# --- ROUTES ---


@app.route('/')
def index():
    # Load Data
    items = load_data()

    # Session Keywords Defaults
    DEFAULT_KEYWORDS = ["#BreakingNews", "#Karnataka", "#news", "#india"]

    if 'trending_keywords' not in session:
        session['trending_keywords'] = DEFAULT_KEYWORDS
    elif not session['trending_keywords']:  # If list exists but is empty
        session['trending_keywords'] = DEFAULT_KEYWORDS

    # Stats & Tags
    all_tags = [t for item in items for t in item["tags"]]
    tag_counts = Counter(all_tags).most_common(20)
    unique_topics = len(set(all_tags))

    # Backend Filtering (Optional now that we have frontend search, but good for deep linking)
    search_query = request.args.get('search', '').lower()
    selected_tag = request.args.get('tag', 'All')

    if selected_tag != "All":
        items = [i for i in items if selected_tag in i['tags']]

    # We return ALL items for the search query to allow JS realtime filtering
    # But if a tag is selected, we only return those tagged items.

    return render_template('index.html',
                           items=items,
                           news_count=len(items),
                           topics_count=unique_topics,
                           tag_counts=tag_counts,
                           selected_tag=selected_tag,
                           keywords=session['trending_keywords'],
                           search_query=search_query,
                           store_dir=os.path.abspath(NEWS_DATA_STORE_DIR))


@app.route('/keyword/add', methods=['POST'])
def add_keyword():
    kw = request.form.get('keyword')
    if kw and kw not in session.get('trending_keywords', []):
        session['trending_keywords'].append(kw)
        session.modified = True
    return redirect(url_for('index'))


@app.route('/keyword/remove/<int:index>')
def remove_keyword(index):
    kws = session.get('trending_keywords', [])
    if 0 <= index < len(kws):
        kws.pop(index)
        session['trending_keywords'] = kws
    return redirect(url_for('index'))


@app.route('/keyword/edit', methods=['POST'])
def edit_keyword():
    """Endpoint to update a keyword via AJAX"""
    try:
        data = request.json
        index = int(data.get('index'))
        new_value = data.get('value')

        kws = session.get('trending_keywords', [])
        if 0 <= index < len(kws) and new_value:
            kws[index] = new_value
            session['trending_keywords'] = kws
            return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    return jsonify({"status": "error"}), 400


@app.route('/update-trends', methods=['POST'])
def update_trends():
    kws = session.get('trending_keywords', [])
    if not kws:
        flash("Please add at least one keyword.")
        return redirect(url_for('index'))

    # Call bot function (it handles its own client now)
    print(f"[keywords] {kws}")
    asyncio.run(update_from_trends(client=client, keywords=kws))

    flash("Maal Updated Successfully!")
    return redirect(url_for('index'))


@app.route('/delete/<item_id>')
def delete_item(item_id):
    target_path = os.path.join(NEWS_DATA_STORE_DIR, item_id)
    if os.path.exists(target_path):
        try:
            shutil.rmtree(target_path)
            flash("Item deleted.")
        except Exception as e:
            flash(f"Error deleting: {e}")
    return redirect(url_for('index'))


async def main():
    await twikit_login(client=client)
    app.run(debug=True, port=5000)


if __name__ == '__main__':
    asyncio.run(main())
