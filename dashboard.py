import streamlit as st
import os
import json
import pandas as pd
from datetime import datetime
import time

from app.configs import NEWS_DATA_STORE_DIR


# Page Config
st.set_page_config(
    page_title="News Bot Dashboard",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS Styling ---
st.markdown("""
<style>
    .reportview-container {
        background: #0e1117;
    }
    .news-card {
        background-color: #262730;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        border-left: 5px solid #ff4b4b;
    }
    .headline {
        color: #ffffff;
        font-size: 22px;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .meta-tag {
        background-color: #31333F;
        color: #00d4b1;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 12px;
        margin-right: 5px;
    }
    .timestamp {
        color: #808495;
        font-size: 12px;
        font-style: italic;
    }
</style>
""", unsafe_allow_html=True)

# --- Data Loading Function ---
def load_data():
    """Reads all JSON files from the data store directory."""
    if not os.path.exists(NEWS_DATA_STORE_DIR):
        return pd.DataFrame()

    data_list = []
    
    # Iterate over all directories in the store
    for folder_name in os.listdir(NEWS_DATA_STORE_DIR):
        folder_path = os.path.join(NEWS_DATA_STORE_DIR, folder_name)
        
        if os.path.isdir(folder_path):
            json_path = os.path.join(folder_path, "data.json")
            
            if os.path.exists(json_path):
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        item = json.load(f)
                        
                        # Parsing the ID back to datetime object for sorting
                        # Format: %I_%M_%p_%d_%m_%Y (e.g., 05_13_PM_26_11_2025)
                        try:
                            dt_obj = datetime.strptime(item['id'], "%I_%M_%p_%d_%m_%Y")
                        except ValueError:
                            # Fallback if ID format changes or is invalid
                            dt_obj = datetime.fromtimestamp(os.path.getctime(json_path))

                        data_list.append({
                            "id": item.get('id'),
                            "headline": item.get('headline_str', 'No Headline'),
                            "content": item.get('content_str', ''),
                            "tags": item.get('tags_list', ''), # This is a string "tag1 tag2" based on models.py
                            "datetime": dt_obj,
                            "display_time": dt_obj.strftime("%Y-%m-%d %I:%M %p")
                        })
                except Exception as e:
                    st.error(f"Error reading {json_path}: {e}")

    df = pd.DataFrame(data_list)
    if not df.empty:
        # Sort by datetime descending (newest first)
        df = df.sort_values(by="datetime", ascending=False)
    return df

# --- Main App Logic ---

# Sidebar
with st.sidebar:
    st.title("🤖 Bot Control")
    st.markdown("---")
    
    if st.button("🔄 Refresh Feed", type="primary"):
        st.rerun()
    
    auto_refresh = st.toggle("Auto-refresh (10s)", value=False)
    
    st.markdown("### Filters")
    search_term = st.text_input("Search Headlines", "")
    
    # Statistics
    df = load_data()
    st.markdown("---")
    st.markdown("### Stats")
    if not df.empty:
        st.metric("Total Articles", len(df))
        st.metric("Latest Update", df.iloc[0]['display_time'])
    else:
        st.write("No data found.")

# Main Feed
st.title("🔥 Trending News Feed")
st.caption(f"Reading from: `{NEWS_DATA_STORE_DIR}`")

if df.empty:
    st.info("No news items found yet. Run `bot.py` to fetch data.")
else:
    # Filter logic
    if search_term:
        df = df[df['headline'].str.contains(search_term, case=False, na=False)]

    # Display Loop
    for index, row in df.iterrows():
        # Using a container for card-like look
        with st.container(border=True):
            
            # Header: Headline + Time
            c1, c2 = st.columns([0.8, 0.2])
            with c1:
                st.subheader(row['headline'])
            with c2:
                st.caption(f"🕒 {row['display_time']}")
            
            # Content
            st.write(row['content'])
            
            # Footer: Tags + ID
            st.markdown("---")
            tags_str = row['tags']
            
            # Format tags nicely
            if tags_str:
                tags = tags_str.split(" ")
                # Create HTML for badges
                tags_html = "".join([f"<span style='background-color:#333; color:#4CAF50; padding:2px 8px; border-radius:10px; margin-right:5px; font-size:0.8em;'>#{tag}</span>" for tag in tags if tag])
                st.markdown(tags_html, unsafe_allow_html=True)
            
            with st.expander("View JSON Raw Data"):
                st.json({
                    "id": row['id'],
                    "headline": row['headline'],
                    "tags": row['tags']
                })

# Auto-refresh logic
if auto_refresh:
    time.sleep(10)
    st.rerun()