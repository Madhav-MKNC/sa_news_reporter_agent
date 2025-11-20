from twikit import Client
import asyncio
import os

async def main():
    client = Client('en-US')
    print("=====================================")
    print("🔐 TWITTER/X LOGIN SETUP")
    print("=====================================")
    print("This script will save a 'cookies.json' file locally.")
    print("You only need to do this ONCE (unless cookies expire).\\n")
    
    username = input("Enter Twitter Username (without @): ")
    email = input("Enter Email associated with Twitter: ")
    password = input("Enter Password: ")

    print("\\nAttempting login... (This acts like a real browser)")

    try:
        # Twikit login sequence
        await client.login(
            auth_info_1=username,
            auth_info_2=email,
            password=password
        )
        client.save_cookies('cookies.json')
        print("\\n✅ SUCCESS! 'cookies.json' saved.")
        print("You can now run 'streamlit run app.py'")
    except Exception as e:
        print(f"\\n❌ Login failed: {e}")
        print("Tip: If you have 2FA, Twikit might struggle. Disable 2FA temporarily or use a fresh account.")

if __name__ == "__main__":
    asyncio.run(main())
