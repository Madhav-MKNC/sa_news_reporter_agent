import streamlit as st
import os
import json
import pandas as pd
from datetime import datetime
import urllib.parse
from collections import Counter

# --- CONFIGURATION ---
# Try/Except block allows this to run even if your config file is missing during testing
try:
    from app.configs import NEWS_DATA_STORE_DIR
except ImportError:
    NEWS_DATA_STORE_DIR = "news_data"  # Default fallback
    os.makedirs(NEWS_DATA_STORE_DIR, exist_ok=True)

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="SA News | Editor Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM THEME & CSS ---
st.markdown("""
<style>
    /* IMPORT FONT: Inter (Professional, clean, similar to X/Twitter) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* APP BACKGROUND */
    .stApp {
        background-color: #000000; /* Pitch Black for high contrast */
    }

    /* CUSTOM CARD STYLING */
    /* We target Streamlit's container with border */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #16181c; /* Dark Gray Card */
        border: 1px solid #2f3336;
        border-radius: 12px;
        padding: 10px;
        transition: transform 0.2s, border-color 0.2s;
    }
    
    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: #1d9bf0; /* Twitter Blue Hover */
        box-shadow: 0 4px 20px rgba(29, 155, 240, 0.1);
    }

    /* TEXT INPUT (SEARCH) */
    .stTextInput > div > div > input {
        background-color: #202327;
        color: white;
        border: 1px solid #2f3336;
        border-radius: 20px; /* Pill shape search */
        padding: 10px 15px;
    }
    .stTextInput > div > div > input:focus {
        border-color: #1d9bf0;
        background-color: #000000;
    }

    /* HEADLINES */
    .news-header {
        font-size: 1.15rem;
        font-weight: 700;
        color: #e7e9ea;
        margin-bottom: 8px;
        line-height: 1.3;
    }

    /* BODY TEXT */
    .news-content {
        font-size: 0.95rem;
        color: #d6d9db;
        line-height: 1.6;
        margin-bottom: 12px;
        font-weight: 400;
    }

    /* META DATA (Time) */
    .meta-text {
        font-size: 0.75rem;
        color: #71767b;
        font-family: 'Inter', sans-serif; /* Ensure consistency */
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        gap: 5px;
    }

    /* TAG CHIPS */
    .tag-container {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 8px;
    }
    a.tag-chip {
        background-color: rgba(29, 155, 240, 0.1);
        color: #1d9bf0;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        text-decoration: none;
        font-weight: 600;
        transition: background-color 0.2s;
    }
    a.tag-chip:hover {
        background-color: rgba(29, 155, 240, 0.2);
        text-decoration: none;
    }

    /* BUTTONS */
    /* Primary (Post to X) */
    div.stButton > a[kind="primary"] {
        background-color: #1d9bf0;
        color: white;
        border-radius: 20px;
        font-weight: 700;
        border: none;
        text-decoration: none;
        display: inline-flex;
        justify-content: center;
        align-items: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    div.stButton > a[kind="primary"]:hover {
        background-color: #1a8cd8;
    }

    /* SIDEBAR STYLING */
    [data-testid="stSidebar"] {
        background-color: #000000;
        border-right: 1px solid #2f3336;
    }
    .sidebar-stat {
        font-size: 2rem;
        font-weight: 700;
        color: #e7e9ea;
    }
    .sidebar-label {
        font-size: 0.85rem;
        color: #71767b;
    }
    
    /* SCROLLBAR */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #000000; 
    }
    ::-webkit-scrollbar-thumb {
        background: #2f3336; 
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #536471; 
    }
</style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---


def get_time_display(dt_obj):
    """Clean time format like 'Now', '5m ago', or date."""
    diff = datetime.now() - dt_obj
    seconds = diff.total_seconds()

    if seconds < 60:
        return "Just now"
    elif seconds < 3600:
        return f"{int(seconds // 60)}m ago"
    elif seconds < 86400:
        return f"{int(seconds // 3600)}h ago"
    else:
        return dt_obj.strftime("%d %b • %I:%M %p")


def to_bold_unicode(text):
    """Converts text to bold unicode for X."""
    normal = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    bold = "𝐀𝐁𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏𝐐𝐑𝐒𝐓𝐔𝐕𝐖𝐗𝐘𝐙𝐚𝐛𝐜𝐝𝐞𝐟𝐠𝐡𝐢𝐣𝐤𝐥𝐦𝐧𝐨𝐩𝐪𝐫𝐬𝐭𝐮𝐯𝐰𝐱𝐲𝐳𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗"
    trans_table = str.maketrans(normal, bold)
    return text.translate(trans_table)


@st.cache_data(ttl=60)  # Cache data for 60 seconds to improve performace
def load_data():
    if not os.path.exists(NEWS_DATA_STORE_DIR):
        return pd.DataFrame()

    data_list = []
    try:
        folders = os.listdir(NEWS_DATA_STORE_DIR)
    except OSError:
        return pd.DataFrame()

    for folder_name in folders:
        folder_path = os.path.join(NEWS_DATA_STORE_DIR, folder_name)
        if os.path.isdir(folder_path):
            json_path = os.path.join(folder_path, "data.json")
            if os.path.exists(json_path):
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        item = json.load(f)
                        # Parse Timestamp
                        try:
                            dt_obj = datetime.strptime(
                                item.get('id', ''), "%I_%M_%p_%d_%m_%Y")
                        except ValueError:
                            dt_obj = datetime.fromtimestamp(
                                os.path.getctime(json_path))

                        # Clean Tags
                        raw_tags = item.get('tags_list', '')
                        tags = [t.strip()
                                for t in raw_tags.split(" ") if t.strip()]

                        data_list.append({
                            "id": item.get('id'),
                            "headline": item.get('headline_str', 'Untitled'),
                            "content": item.get('content_str', ''),
                            "tags": tags,
                            "datetime": dt_obj,
                            "display_time": get_time_display(dt_obj)
                        })
                except Exception:
                    continue

    df = pd.DataFrame(data_list)
    if not df.empty:
        df = df.sort_values(by="datetime", ascending=False)
    return df

# --- MAIN APP LOGIC ---


# 1. Load Data
df = load_data()

# 2. Sidebar (Analytics & Filters)
with st.sidebar:
    st.markdown("## 📊 Dashboard")

    if not df.empty:
        # Stats
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.markdown(
                f"<div class='sidebar-stat'>{len(df)}</div><div class='sidebar-label'>News Items</div>", unsafe_allow_html=True)
        with col_s2:
            # Calculate unique tags
            all_tags = [tag for tags in df['tags'] for tag in tags]
            st.markdown(
                f"<div class='sidebar-stat'>{len(set(all_tags))}</div><div class='sidebar-label'>Topics</div>", unsafe_allow_html=True)

        st.markdown("---")

        # Tag Filter
        st.markdown("### 🔥 Trending Topics")
        tag_counts = Counter(all_tags).most_common(10)

        # 'All' option logic handled via session state or simple selection
        selected_tag_filter = st.radio(
            "Filter by Topic",
            ["All"] + [f"#{tag} ({count})" for tag, count in tag_counts],
            label_visibility="collapsed"
        )
    else:
        st.info("No data connected.")
        selected_tag_filter = "All"

# 3. Main Feed Header
c1, c2, c3 = st.columns([0.15, 0.7, 0.15], gap="small")
with c1:
    st.markdown("### ⚡ **Maal**")
with c2:
    search_query = st.text_input(
        "Search", placeholder="Search headlines...", label_visibility="collapsed")
with c3:
    if st.button("Refresh ↺", type="secondary", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

# 4. Filter Logic
filtered_df = df.copy()

# Apply Search
if search_query:
    filtered_df = filtered_df[filtered_df['headline'].str.contains(
        search_query, case=False, na=False)]

# Apply Sidebar Tag Filter
if selected_tag_filter != "All":
    # Extract tag name from "tag (count)" string
    clean_tag = selected_tag_filter.split(" (")[0].replace("#", "")
    # Filter rows where list of tags contains the clean_tag
    filtered_df = filtered_df[filtered_df['tags'].apply(
        lambda x: clean_tag in x)]


# 5. Render Feed
if filtered_df.empty:
    st.markdown("""
        <div style='text-align: center; padding: 50px; color: #71767b;'>
            <h2>📭</h2>
            <p>No news items found.</p>
        </div>
    """, unsafe_allow_html=True)
else:
    for index, row in filtered_df.iterrows():
        # Using Streamlit container with styling hook
        with st.container(border=True):

            # Top Row: Time | ID (optional)
            st.markdown(f"""
            <div class='meta-text'>
                <span>🕒 {row['display_time']}</span>
            </div>
            """, unsafe_allow_html=True)

            # Middle Row: Headline & Content
            st.markdown(
                f"<div class='news-header'>{row['headline']}</div>", unsafe_allow_html=True)
            st.markdown(
                f"<div class='news-content'>{row['content']}</div>", unsafe_allow_html=True)

            # Bottom Row: Tags (Left) and Button (Right)
            col_tags, col_btn = st.columns([0.8, 0.2], gap="small")

            with col_tags:
                if row['tags']:
                    tags_html = "<div class='tag-container'>"
                    for t in row['tags']:
                        url = f"https://x.com/search?q=%23{t}"
                        tags_html += f"<a href='{url}' target='_blank' class='tag-chip'>#{t}</a>"
                    tags_html += "</div>"
                    st.markdown(tags_html, unsafe_allow_html=True)

            with col_btn:
                # Prepare X Payload
                tweet_headline = to_bold_unicode(row['headline'])
                tweet_tags = " ".join([f"#{t}" for t in row['tags']])
                full_text = f"{tweet_headline}\n\n{row['content']}\n\n{tweet_tags}"
                encoded_text = urllib.parse.quote(full_text)
                x_url = f"https://x.com/intent/tweet?text={encoded_text}"

                # Render Link Button
                st.link_button("Post 𝕏", x_url, type="primary",
                               use_container_width=True)
