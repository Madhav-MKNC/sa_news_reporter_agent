import asyncio
from twikit import Client
import datetime
import time

USERNAME = ''
EMAIL = ''
PASSWORD = ''


# Initialize client
client = Client('en-US')

async def main():
    await client.login(
        auth_info_1=USERNAME,
        auth_info_2=EMAIL,
        password=PASSWORD,
        # cookies_file='cookies.json'
    )
    
    # await client.create_tweet(
    #     text=f'hello world {datetime.datetime.now()} {time.time()}',
    #     reply_to="1936294890796990637"
    # )
    
    await notifications = client.get_notifications(type='Mentions', count=10)
    


asyncio.run(main())

