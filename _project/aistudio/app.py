import streamlit as st
import asyncio
import urllib.parse
from backend import get_twitter_trends, run_editorial_crew
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="SA News Deck", page_icon="📰", layout="centered")

# Custom CSS for better inputs
st.markdown("""
    <style>
    div.stButton > button:first-child {background-color: #00acee; color: white;}
    .stTextArea textarea {font-size: 16px;}
    </style>
    """, unsafe_allow_html=True)

st.title("📰 SA News Karnataka")
st.caption("Automated Command Center")

# Initialize State
if 'drafts' not in st.session_state:
    st.session_state.drafts = []

# --- ACTION BAR ---
col1, col2 = st.columns([1, 2])

with col1:
    if st.button("🔄 Scan & Generate", type="primary", use_container_width=True):
        st.session_state.drafts = [] # Clear old
        
        with st.status("🚀 Agents Activated...", expanded=True) as status:
            
            st.write("📡 Connecting to Twitter...")
            # Run async scraper
            raw_news = asyncio.run(get_twitter_trends())
            
            if raw_news and isinstance(raw_news[0], dict) and "error" in raw_news[0]:
                st.error(raw_news[0]['error'])
                status.update(label="Failed", state="error")
            elif not raw_news:
                st.warning("No news found.")
                status.update(label="Done", state="complete")
            else:
                st.write(f"🔍 Found {len(raw_news)} potential stories.")
                st.write("🧠 AI Editor is drafting...")
                
                # Generate 2 variations
                try:
                    draft1 = run_editorial_crew(raw_news)
                    st.session_state.drafts.append(draft1)
                    
                    # If we have enough news, generate a second different one
                    if len(raw_news) > 2:
                        draft2 = run_editorial_crew(raw_news[::-1]) # Reverse list context
                        st.session_state.drafts.append(draft2)
                        
                    status.update(label="Drafts Ready!", state="complete", expanded=False)
                except Exception as e:
                    st.error(f"AI Error: {e}")

# --- DRAFTS AREA ---
st.divider()

if not st.session_state.drafts:
    st.info("Ready to start. Click 'Scan & Generate'.")

for i, content in enumerate(st.session_state.drafts):
    with st.container(border=True):
        st.subheader(f"Draft Option {i+1}")
        
        # Edit Area
        final_text = st.text_area(
            "Edit Tweet", 
            value=content, 
            height=120, 
            key=f"draft_{i}",
            label_visibility="collapsed"
        )
        
        # Stats
        c_len = len(final_text)
        st.caption(f"Characters: {c_len} / 280")
        
        # Intent Link
        encoded = urllib.parse.quote(final_text)
        url = f"https://twitter.com/intent/tweet?text={encoded}"
        
        # Post Button
        st.link_button("🚀 Open in Twitter", url, use_container_width=True)
