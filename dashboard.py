import streamlit as st
import os
import json
import pandas as pd
from datetime import datetime
import urllib.parse
from collections import Counter
import shutil

# --- CONFIG ---
try:
    from app.configs import NEWS_DATA_STORE_DIR
except ImportError:
    NEWS_DATA_STORE_DIR = "news_data"
    os.makedirs(NEWS_DATA_STORE_DIR, exist_ok=True)

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="SA News | Editor Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS ---
st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background:#000; }
    [data-testid="stVerticalBlockBorderWrapper"] {
        background:#16181c; border:1px solid #2f3336; border-radius:12px;
        padding:10px; transition:.2s;
    }
    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color:#1d9bf0; box-shadow:0 4px 20px rgba(29,155,240,.1);
    }
    .news-header { font-size:1.15rem; font-weight:700; color:#e7e9ea; margin-bottom:8px; }
    .news-content { font-size:.95rem; color:#d6d9db; margin-bottom:12px; }
    .meta-text { font-size:.75rem; color:#71767b; margin-bottom:4px; display:flex; gap:5px; }
    .tag-container { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:8px; }
    a.tag-chip {
        background:rgba(29,155,240,.1); color:#1d9bf0; padding:4px 10px; border-radius:12px;
        font-size:.8rem; text-decoration:none; font-weight:600;
    }
    a.tag-chip:hover { background:rgba(29,155,240,.2); }
</style>""", unsafe_allow_html=True)

# --- HELPERS ---


def parse_datetime_from_id(id_str: str):
    """Extract datetime from: HH_MM_AMPM_DD_MM_YYYY_UUID"""
    try:
        time_segment = id_str.rsplit("_", 1)[0]
        return datetime.strptime(time_segment, "%I_%M_%p_%d_%m_%Y")
    except:
        return None


def get_time_display(dt):
    diff = datetime.now() - dt
    s = diff.total_seconds()
    if s < 60:
        return "Just now"
    if s < 3600:
        return f"{int(s//60)}m ago"
    if s < 86400:
        return f"{int(s//3600)}h ago"
    return dt.strftime("%d %b • %I:%M %p")


def to_bold_unicode(text):
    normal = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    bold = "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭" \
        "𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇" \
        "𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟕𝟴𝟵"
    return text.translate(str.maketrans(normal, bold))


@st.cache_data(ttl=60)
def load_data():
    items = []

    if not os.path.exists(NEWS_DATA_STORE_DIR):
        return pd.DataFrame()

    for folder in os.listdir(NEWS_DATA_STORE_DIR):
        folder_path = os.path.join(NEWS_DATA_STORE_DIR, folder)
        json_path = os.path.join(folder_path, "data.json")

        if not os.path.isdir(folder_path) or not os.path.exists(json_path):
            continue

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            raw_tags = data.get("tags_list", "")

            # Split
            if isinstance(raw_tags, str):
                raw_tags = raw_tags.split()

            # Normalize tags → always "#tag" (never "##tag")
            tags = []
            for t in raw_tags:
                if not t:
                    continue
                # remove all leading #'s then prepend exactly one
                normalized = "#" + t.lstrip("#")
                tags.append(normalized)

            sources = data.get("source_list", "")
            sources = sources.split() if isinstance(sources, str) else sources

            dt = parse_datetime_from_id(data["id"]) or datetime.now()

            items.append({
                "id": data["id"],
                "headline": data.get("headline_str", "Untitled"),
                "content": data.get("content_str", ""),
                "tags": tags,
                "sources": sources,
                "datetime": dt,
                "display_time": get_time_display(dt)
            })
        except:
            continue

    df = pd.DataFrame(items)
    if not df.empty:
        df = df.sort_values(by="datetime", ascending=False)

    return df


# --- MAIN ---
df = load_data()

with st.sidebar:
    st.markdown("## 📊 Dashboard")
    if not df.empty:
        all_tags = [t for tags in df["tags"] for t in tags]
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(
                f"<h2>{len(df)}</h2><p style='color:#71767b;'>News Items</p>", unsafe_allow_html=True)
        with c2:
            st.markdown(
                f"<h2>{len(set(all_tags))}</h2><p style='color:#71767b;'>Topics</p>", unsafe_allow_html=True)

        st.markdown("---")
        tag_counts = Counter(all_tags).most_common(10)

        selected_tag = st.radio(
            "Filter",
            ["All"] + [f"#{tag} ({count})" for tag, count in tag_counts],
            label_visibility="collapsed"
        )
    else:
        selected_tag = "All"

# HEADER
c1, c2, c3 = st.columns([0.15, 0.7, 0.15])
with c1:
    st.markdown("### ⚡ **Maal**")
with c2:
    search_query = st.text_input(
        "Search", placeholder="Search headlines...", label_visibility="collapsed"
    )
with c3:
    if st.button("Refresh ↺", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# FILTER LOGIC
filtered = df.copy()

if search_query:
    filtered = filtered[filtered["headline"].str.contains(
        search_query, case=False, na=False)]

if selected_tag != "All":
    clean_tag = selected_tag.split(" (")[0].replace("#", "")
    filtered = filtered[filtered["tags"].apply(lambda x: clean_tag in x)]

# FEED RENDERING
if filtered.empty:
    st.markdown("<div style='text-align:center;color:#777;padding:40px;'>📭 No news found.</div>",
                unsafe_allow_html=True)

else:
    for _, row in filtered.iterrows():
        with st.container(border=True):

            st.markdown(
                f"<div class='meta-text'>🕒 {row['display_time']}</div>", unsafe_allow_html=True)

            st.markdown(
                f"<div class='news-header'>{row['headline']}</div>", unsafe_allow_html=True)
            st.markdown(
                f"<div class='news-content'>{row['content']}</div>", unsafe_allow_html=True)

            col_tags, col_btn = st.columns([0.75, 0.25])

            # TAGS & SOURCES
            with col_tags:
                tag_html = "<div class='tag-container'>"
                for t in row["tags"]:
                    tag_html += f"<a class='tag-chip' target='_blank' href='https://x.com/search?q=%23{t}'>#{t}</a>"

                for s in row["sources"]:
                    tag_html += f"<a class='tag-chip' style='background:#333;color:#fff;'>📎 {s}</a>"

                tag_html += "</div>"
                st.markdown(tag_html, unsafe_allow_html=True)

            # BUTTONS
            with col_btn:
                # --- POST TO X ---
                tweet = (
                    to_bold_unicode(row["headline"]) +
                    "\n\n" + row["content"] +
                    "\n\n" + " ".join(f"#{t}" for t in row["tags"])
                )
                x_url = "https://x.com/intent/tweet?text=" + \
                    urllib.parse.quote(tweet)

                st.link_button("Post 𝕏", x_url, type="primary",
                               use_container_width=True)

                # --- DELETE BUTTON ---
                del_key = f"delete_{row['id']}"
                confirm_key = f"confirm_{row['id']}"

                if st.button("🗑 Delete", key=del_key):
                    st.session_state[confirm_key] = True

                # --- CONFIRMATION DIALOG ---
                if st.session_state.get(confirm_key, False):
                    st.warning(f"Delete **{row['headline']}** permanently?")
                    c1, c2 = st.columns(2)

                    with c1:
                        if st.button("Yes, delete", type="primary"):
                            try:
                                shutil.rmtree(os.path.join(
                                    NEWS_DATA_STORE_DIR, row["id"]))
                            except Exception as e:
                                st.error(f"Error deleting: {e}")

                            st.session_state[confirm_key] = False
                            st.cache_data.clear()
                            st.rerun()

                    with c2:
                        if st.button("Cancel"):
                            st.session_state[confirm_key] = False
