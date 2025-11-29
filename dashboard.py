import streamlit as st
import os
import json
import pandas as pd
from datetime import datetime, timezone
import urllib.parse
from collections import Counter
import shutil
import asyncio

from app.bot import update_from_trends

# --- CONFIG ---
try:
    from app.configs import NEWS_DATA_STORE_DIR
except ImportError:
    NEWS_DATA_STORE_DIR = "news_data"

# Ensure directory exists
if not os.path.exists(NEWS_DATA_STORE_DIR):
    os.makedirs(NEWS_DATA_STORE_DIR, exist_ok=True)

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Maal | Editor",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- VERCEL/GEIST INSPIRED CSS ---
st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    /* Base */
    html, body, [class*="css"] { 
        font-family: 'Inter', sans-serif; 
        color: #ededed;
        background-color: #000000;
    }
    .stApp { background-color: #000000; }

    /* Card */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #0a0a0a;
        border: 1px solid #333;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 16px;
        transition: border-color 0.2s ease;
    }
    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: #555;
    }

    /* Text */
    .headline {
        font-size: 1.2rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: #fff;
        margin-bottom: 10px;
    }
    .content-text {
        font-size: 0.95rem;
        line-height: 1.6;
        color: #a1a1a1;
        margin-bottom: 20px;
        white-space: pre-wrap;
    }
    .meta-mono {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        color: #666;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 10px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Tags */
    .section-label {
        font-size: 0.7rem;
        color: #444;
        font-weight: 700;
        text-transform: uppercase;
        margin-bottom: 8px;
    }
    .tag-container {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin-bottom: 16px;
    }
    .tag-pill {
        background: #111;
        border: 1px solid #333;
        color: #999;
        padding: 4px 10px;
        border-radius: 100px;
        font-size: 0.75rem;
        text-decoration: none;
        transition: 0.2s;
    }
    .tag-pill:hover {
        background: #fff;
        color: #000;
        border-color: #fff;
    }

    /* Sources */
    .source-box {
        background: #050505;
        border: 1px dashed #222;
        padding: 12px;
        border-radius: 6px;
        display: flex;
        flex-direction: column;
        gap: 6px;
    }
    .source-link {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        color: #444;
        text-decoration: none;
        overflow-wrap: break-word;
        word-break: break-all;
    }
    .source-link:hover {
        color: #3291ff;
        text-decoration: underline;
    }

    /* Inputs & Buttons */
    .stTextInput input {
        background-color: #0a0a0a !important;
        border: 1px solid #333 !important;
        color: #fff !important;
    }
    .stButton button {
        background-color: #000;
        border: 1px solid #333;
        color: #ccc;
        border-radius: 6px;
    }
    .stButton button:hover {
        border-color: #fff;
        color: #fff;
    }
    button[kind="primary"] {
        background-color: #fff !important;
        color: #000 !important;
        border: none !important;
        font-weight: 600;
    }
</style>""", unsafe_allow_html=True)

# --- HELPERS ---


def safe_parse_timestamp(ts_str):
    """
    Parses timestamp string. 
    Returns a datetime object.
    """
    if not ts_str:
        return datetime.now()
    try:
        # Standard ISO parsing (handles +00:00)
        return datetime.fromisoformat(ts_str)
    except Exception:
        try:
            # Fallback for weird formats, try ignoring TZ
            clean_ts = ts_str.split('+')[0].split('.')[0].replace('Z', '')
            return datetime.strptime(clean_ts, "%Y-%m-%dT%H:%M:%S")
        except:
            return datetime.now()


def get_relative_time(dt):
    """
    Calculates time ago, handling both Aware and Naive datetimes.
    """
    # 1. Determine "Now" based on the timezone awareness of 'dt'
    if dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None:
        # dt is aware (has timezone), so get 'now' with that timezone
        now = datetime.now(dt.tzinfo)
    else:
        # dt is naive (no timezone), so get naive 'now'
        now = datetime.now()

    # 2. Calculate difference
    diff = now - dt
    s = diff.total_seconds()

    # 3. Format output
    if s < 0:
        # If time is in the future (e.g. server clock drift), just say 'Just now'
        return "Just now"
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
    bold = "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭" \
           "𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇" \
           "𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟕𝟴𝟵"
    return text.translate(str.maketrans(normal, bold))


@st.cache_data(ttl=2)
def load_data():
    items = []

    if not os.path.exists(NEWS_DATA_STORE_DIR):
        return pd.DataFrame()

    folders = os.listdir(NEWS_DATA_STORE_DIR)

    for folder in folders:
        folder_path = os.path.join(NEWS_DATA_STORE_DIR, folder)
        json_path = os.path.join(folder_path, "data.json")

        if not os.path.exists(json_path):
            continue

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # --- PARSING ---
            item_id = data.get("id", folder)
            dt = safe_parse_timestamp(data.get("timestamp_str"))
            headline = data.get("headline_str") or "Untitled"
            content = data.get("content_str") or ""

            # Tags
            raw_tags = data.get("tags_list", [])
            if raw_tags is None:
                raw_tags = []
            if isinstance(raw_tags, str):
                raw_tags = raw_tags.split()
            tags = [str(t).replace("#", "").strip() for t in raw_tags if t]

            # Sources
            raw_sources = data.get("source_list", [])
            if raw_sources is None:
                raw_sources = []
            if isinstance(raw_sources, str):
                raw_sources = raw_sources.split()
            sources = [str(s) for s in raw_sources if s]

            items.append({
                "id": item_id,
                "headline": headline,
                "content": content,
                "tags": tags,
                "sources": sources,
                "datetime": dt,
                "display_time": get_relative_time(dt)
            })
        except Exception as e:
            print(f"Skipped {folder}: {e}")
            continue

    df = pd.DataFrame(items)
    if not df.empty:
        df = df.sort_values(by="datetime", ascending=False)

    return df


# --- APP LAYOUT ---
df = load_data()

# SIDEBAR
with st.sidebar:
    st.markdown("### ⚡ Maal")
    st.caption(f"Storage: `{os.path.abspath(NEWS_DATA_STORE_DIR)}`")

    # --- UPDATE MAAL SECTION ---
    st.markdown("---")
    with st.expander("Update Maal", expanded=False):
        # Initialize session state for keywords
        if "trending_keywords" not in st.session_state:
            st.session_state["trending_keywords"] = []

        # Input to add keyword
        kw_input = st.text_input(
            "Add Keyword", key="kw_in", placeholder="Enter topic...")
        if st.button("Add", use_container_width=True):
            if kw_input and kw_input not in st.session_state["trending_keywords"]:
                st.session_state["trending_keywords"].append(kw_input)
                st.rerun()

        st.caption("Keywords List:")

        # Display list with Edit/Remove capabilities
        # We use a copy to allow modification during iteration
        if not st.session_state["trending_keywords"]:
            st.markdown(
                "<span style='color:#666;font-size:0.8rem'>No keywords added.</span>", unsafe_allow_html=True)

        for i, kw in enumerate(st.session_state["trending_keywords"]):
            c_edit, c_rem = st.columns([0.8, 0.2])

            # Edit functionality: Text input acts as display & edit
            new_val = c_edit.text_input(
                label="Edit",
                value=kw,
                key=f"kw_edit_{i}",
                label_visibility="collapsed"
            )

            # Update state if changed
            if new_val != kw:
                st.session_state["trending_keywords"][i] = new_val

            # Remove button
            if c_rem.button("✕", key=f"kw_rem_{i}"):
                st.session_state["trending_keywords"].pop(i)
                st.rerun()

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        # Update Button
        if st.button("Run Update", type="primary", use_container_width=True):
            if st.session_state["trending_keywords"]:
                with st.spinner("Updating from trends..."):
                    asyncio.run(update_from_trends(
                        keywords=st.session_state["trending_keywords"]))
                st.success("Maal Updated!")
                st.cache_data.clear()
                st.rerun()
            else:
                st.warning("Please add at least one keyword.")

    st.markdown("---")
    # ---------------------------

    if not df.empty:
        all_tags = [t for tags in df["tags"] for t in tags]
        # Count tags
        if all_tags:
            tag_counts = Counter(all_tags).most_common(20)
            c1, c2 = st.columns(2)
            c1.metric("News", len(df))
            c2.metric("Topics", len(set(all_tags)))

            st.markdown("---")
            st.markdown("**Topics**")
            selected_tag = st.radio(
                "Filter",
                ["All"] + [f"#{t} ({c})" for t, c in tag_counts],
                label_visibility="collapsed"
            )
        else:
            st.metric("News", len(df))
            selected_tag = "All"
    else:
        selected_tag = "All"
        st.info("No news items found.")

# HEADER
c_title, c_search, c_btn = st.columns([0.2, 0.6, 0.2])
with c_title:
    st.markdown("<h3 style='margin:0;padding-top:5px;'>Feed</h3>",
                unsafe_allow_html=True)
with c_search:
    search_query = st.text_input(
        "Search", placeholder="Search headlines...", label_visibility="collapsed")
with c_btn:
    if st.button("Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.write("")

# FILTER
filtered_df = df.copy()

if not filtered_df.empty:
    if search_query:
        filtered_df = filtered_df[
            filtered_df["headline"].str.contains(search_query, case=False, na=False) |
            filtered_df["content"].str.contains(
                search_query, case=False, na=False)
        ]

    if selected_tag != "All":
        target_tag = selected_tag.split(" (")[0].replace("#", "")
        filtered_df = filtered_df[filtered_df["tags"].apply(
            lambda x: target_tag in x)]

# RENDER
if filtered_df.empty:
    st.markdown(
        f"""
        <div style='text-align:center; padding: 60px; color: #444;'>
            <h2>📭</h2>
            <p>No items found.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    for _, row in filtered_df.iterrows():
        with st.container(border=True):

            # META (Time)
            # We format datetime carefully
            dt_str = row['datetime'].strftime('%b %d, %I:%M %p')

            st.markdown(f"""
                <div class='meta-mono'>
                    <span style='color:#fff'>● Live</span>
                    <span>{row['display_time']}</span>
                    <span style='opacity:0.3'>|</span>
                    <span>{dt_str}</span>
                </div>
                <div class='headline'>{row['headline']}</div>
                <div class='content-text'>{row['content']}</div>
            """, unsafe_allow_html=True)

            # CONTENT GRID
            col_main, col_side = st.columns([0.75, 0.25])

            with col_main:
                # Tags
                if row['tags']:
                    tags_html = "<div class='tag-container'>"
                    for t in row['tags']:
                        tags_html += f"<a class='tag-pill' href='https://x.com/search?q=%23{t}' target='_blank'>#{t}</a>"
                    tags_html += "</div>"
                    st.markdown(tags_html, unsafe_allow_html=True)

                # Sources
                if row['sources']:
                    st.markdown(
                        "<div class='section-label'>SOURCES</div>", unsafe_allow_html=True)
                    sources_html = "<div class='source-box'>"
                    for s in row['sources']:
                        sources_html += f"<a class='source-link' href='{s}' target='_blank'>🔗 {s}</a>"
                    sources_html += "</div>"
                    st.markdown(sources_html, unsafe_allow_html=True)

            with col_side:
                st.markdown("<div style='height:10px'></div>",
                            unsafe_allow_html=True)

                # Post to X
                tweet_body = (
                    to_bold_unicode(row["headline"]) + "\n\n" +
                    row["content"] + "\n\n" +
                    " ".join([f"#{t}" for t in row['tags']])
                )
                x_intent = "https://x.com/intent/tweet?text=" + \
                    urllib.parse.quote(tweet_body)

                st.link_button("Post on 𝕏", x_intent,
                               type="primary", use_container_width=True)

                # Delete Logic
                del_key = f"del_{row['id']}"
                conf_key = f"conf_{row['id']}"

                if st.button("Delete", key=del_key, use_container_width=True):
                    st.session_state[conf_key] = True

                if st.session_state.get(conf_key, False):
                    st.markdown(
                        "<div style='text-align:center;font-size:0.8rem;margin:5px 0;color:#ff4444'>Confirm?</div>", unsafe_allow_html=True)
                    c_y, c_n = st.columns(2)
                    if c_y.button("Yes", key=f"y_{row['id']}", use_container_width=True):
                        try:
                            shutil.rmtree(os.path.join(
                                NEWS_DATA_STORE_DIR, row['id']))
                            st.session_state[conf_key] = False
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))

                    if c_n.button("No", key=f"n_{row['id']}", use_container_width=True):
                        st.session_state[conf_key] = False
                        st.rerun()
