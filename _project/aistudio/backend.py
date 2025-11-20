import os
import asyncio
from dotenv import load_dotenv
from twikit import Client
from crewai import Agent, Task, Crew
from langchain_groq import ChatGroq

# Load environment variables
load_dotenv()

# Initialize LLM
api_key = os.getenv("GROQ_API_KEY")
if not api_key or "YOUR_ACTUAL_KEY" in api_key:
    # Fallback warning (will fail if not set)
    print("⚠️ WARNING: GROQ_API_KEY not set in .env file.")

llm = ChatGroq(
    api_key=api_key,
    model="llama3-70b-8192",
    temperature=0.6
)

# --- AGENTS ---

# 1. The Reporter
reporter = Agent(
    role='SA News Reporter',
    goal='Identify top trending news topics relevant to Karnataka and India.',
    backstory='You are a senior digital journalist. You filter out spam, K-pop fan wars, and clickbait to find genuine news.',
    verbose=True,
    llm=llm
)

# 2. The Writer
writer = Agent(
    role='SA News Chief Editor',
    goal='Craft viral, professional tweet drafts.',
    backstory="""You correspond for 'SA News Karnataka'. 
    Your Style:
    - Headline: Crispy and Urgent.
    - Body: Informative but short.
    - Tone: Professional yet engaging. 
    - Tags: Use #SANewsKarnataka #Bengaluru.
    - NO 'AI words' like 'Delve', 'Unleash', 'Tapestry'.""",
    verbose=True,
    llm=llm
)

# --- FUNCTIONS ---

async def get_twitter_trends():
    """Scrapes Twitter using saved cookies."""
    client = Client('en-US')
    
    if not os.path.exists('cookies.json'):
        return [{"error": "❌ No cookies.json found! Please run 'python setup_login.py' first."}]

    try:
        client.load_cookies('cookies.json')
    except Exception:
         return [{"error": "❌ Cookies invalid. Please re-run 'python setup_login.py'."}]

    # Define Search Queries
    queries = ["Karnataka Politics", "Bengaluru Infrastructure", "Bangalore Rain", "Sandalwood News"]
    news_items = []

    print("Starting Scrape...")
    try:
        for q in queries:
            # Get top 2 tweets per topic to keep it fast
            tweets = await client.search_tweet(q, product='Top', count=2)
            for tweet in tweets:
                # Basic spam filter
                if len(tweet.text) > 40: 
                    news_items.append(f"Topic: {q} | Tweet: {tweet.text} | User: {tweet.user.name}")
    except Exception as e:
        return [{"error": f"Scraping error: {str(e)}"}]
        
    # Deduping
    return list(set(news_items))

def run_editorial_crew(raw_text_list):
    """Feeds scraped data into CrewAI."""
    
    if not raw_text_list:
        return "No news found to process."

    # Feed top items
    context_data = "\\n\\n".join(raw_text_list[:6])

    task_analyze = Task(
        description=f"""
        Review these raw tweets: 
        {context_data}
        
        Select the single most impactful story for a Karnataka audience. 
        Extract the key facts.
        """,
        agent=reporter
    )

    task_write = Task(
        description="""
        Using the facts from the Reporter, write a viral tweet.
        - Max 280 chars.
        - Must be ready to post.
        - Do NOT include media links in text (user handles that).
        Output ONLY the tweet text.
        """,
        agent=writer
    )

    crew = Crew(
        agents=[reporter, writer],
        tasks=[task_analyze, task_write],
        verbose=False
    )

    result = crew.kickoff()
    return str(result)
