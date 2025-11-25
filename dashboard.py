import streamlit as st
import os
import json
import pandas as pd
from datetime import datetime
import urllib.parse

from app.configs import NEWS_DATA_STORE_DIR

# --- Page Setup ---
st.set_page_config(
    page_title="SA News Karnataka Reporter",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Custom CSS ---
st.markdown("""
<style>
    /* Global Background */
    .stApp {
        background-color: #0E1117;
    }
    
    /* Search Bar Styling */
    .stTextInput > div > div > input {
        background-color: #262730;
        color: #ffffff;
        border: 1px solid #4a4a4a;
        border-radius: 8px;
    }

    /* Card Container Border */
    div[data-testid="stVerticalBlock"] > div[style*="background-color"] {
        border: 1px solid #303030;
    }

    /* Clickable Tag Badge */
    a.tag-badge {
        background-color: #1E1E1E;
        border: 1px solid #333;
        color: #00ADB5 !important; /* Force Teal color */
        padding: 4px 12px;
        border-radius: 15px;
        font-size: 0.85em;
        font-weight: 500;
        margin-right: 6px;
        display: inline-block;
        margin-bottom: 4px;
        text-decoration: none; /* Remove underline */
        transition: all 0.2s ease;
    }

    a.tag-badge:hover {
        background-color: #333;
        border-color: #00ADB5;
        color: #fff !important;
        transform: translateY(-1px);
    }

    /* Time Stamp */
    .timestamp {
        color: #767676;
        font-size: 0.8em;
        font-family: monospace;
    }
    
    /* Post Button Override */
    div.stButton > button {
        border-radius: 8px;
        font-weight: 600;
        border: none;
    }
</style>
""", unsafe_allow_html=True)

# --- Helper Functions ---


def to_bold_unicode(text):
    """Converts text to bold unicode characters for X (Twitter)."""
    normal = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    bold = "𝐀𝐁𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏𝐐𝐑𝐒𝐓𝐔𝐕𝐖𝐗𝐘𝐙𝐚𝐛𝐜𝐝𝐞𝐟𝐠𝐡𝐢𝐣𝐤𝐥𝐦𝐧𝐨𝐩𝐪𝐫𝐬𝐭𝐮𝐯𝐰𝐱𝐲𝐳𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗"
    trans_table = str.maketrans(normal, bold)
    return text.translate(trans_table)


def load_data():
    if not os.path.exists(NEWS_DATA_STORE_DIR):
        return pd.DataFrame()

    data_list = []
    for folder_name in os.listdir(NEWS_DATA_STORE_DIR):
        folder_path = os.path.join(NEWS_DATA_STORE_DIR, folder_name)
        if os.path.isdir(folder_path):
            json_path = os.path.join(folder_path, "data.json")
            if os.path.exists(json_path):
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        item = json.load(f)
                        try:
                            dt_obj = datetime.strptime(
                                item.get('id', ''), "%I_%M_%p_%d_%m_%Y")
                        except ValueError:
                            dt_obj = datetime.fromtimestamp(
                                os.path.getctime(json_path))

                        data_list.append({
                            "id": item.get('id'),
                            "headline": item.get('headline_str', 'Untitled'),
                            "content": item.get('content_str', ''),
                            "tags": item.get('tags_list', ''),
                            "datetime": dt_obj,
                            "display_time": dt_obj.strftime("%d %b %Y, %I:%M %p")
                        })
                except Exception:
                    continue

    df = pd.DataFrame(data_list)
    if not df.empty:
        df = df.sort_values(by="datetime", ascending=False)
    return df

# --- Main Interface ---


col_header, col_refresh = st.columns([0.85, 0.15])
with col_header:
    st.title("⚡ Maal Dashboard")
with col_refresh:
    st.write("")
    st.write("")
    if st.button("🔄 Refresh"):
        st.rerun()

df = load_data()

# Search Bar
search_query = st.text_input(
    "Search", placeholder="Type to search headlines...", label_visibility="collapsed")

if not df.empty and search_query:
    df = df[df['headline'].str.contains(search_query, case=False, na=False)]

if not df.empty:
    st.caption(f"Showing {len(df)} updates")
else:
    st.info("No news items found.")

# Feed Display
for index, row in df.iterrows():
    with st.container(border=True):

        # Date
        st.markdown(
            f"<div class='timestamp'>📅 {row['display_time']}</div>", unsafe_allow_html=True)

        # Headline
        st.subheader(row['headline'])

        # Content
        st.write(row['content'])

        st.write("")  # Spacer

        col_tags, col_action = st.columns([0.75, 0.25])

        with col_tags:
            # --- UPDATED: Clickable Tags ---
            raw_tags = row['tags']
            if raw_tags:
                tag_list = raw_tags.split(" ")
                html_tags = ""
                for t in tag_list:
                    if t:
                        # Construct the Trend URL: https://x.com/search?q=%23TAG...
                        trend_url = f"https://x.com/search?q=%23{t}&src=trend_click&vertical=trends"
                        # Add clickable anchor tag
                        html_tags += f"<a href='{trend_url}' target='_blank' class='tag-badge'>#{t}</a>"

                st.markdown(html_tags, unsafe_allow_html=True)
            else:
                st.caption("No tags")

        with col_action:
            # Post Button
            tweet_headline = to_bold_unicode(row['headline'])
            tweet_tags = " ".join(
                [f"#{t}" for t in row['tags'].split(" ") if t])
            full_text = f"{tweet_headline}\n\n{row['content']}\n\n{tweet_tags}"
            encoded_text = urllib.parse.quote(full_text)
            x_url = f"https://x.com/intent/tweet?text={encoded_text}"

            st.link_button("🚀 Post to X", url=x_url,
                           type="primary", use_container_width=True)
