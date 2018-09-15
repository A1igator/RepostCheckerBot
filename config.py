import os

client_id = os.environ['BOT_CLIENT_ID']
client_secret = os.environ['BOT_CLIENT_SECRET']
user_agent = os.environ['BOT_USER_AGENT']
username = os.environ['BOT_USERNAME']
password = os.environ['BOT_PASSWORD']
subSettings = [
    [
        os.environ['BOT_SUBREDDIT'],
        int(os.environ['BOT_TOP_DAYS']) if 'BOT_TOP_DAYS' in os.environ else None,
        int(os.environ['BOT_HOT_DAYS']) if 'BOT_HOT_DAYS' in os.environ else None,
        int(os.environ['BOT_NEW_DAYS']) if 'BOT_NEW_DAYS' in os.environ else None,
        int(os.environ['BOT_TOP_NUM_POSTS']) if 'BOT_TOP_NUM_POSTS' in os.environ else 1000,
        int(os.environ['BOT_HOT_NUM_POSTS']) if 'BOT_HOT_NUM_POSTS' in os.environ else 1000,
        int(os.environ['BOT_NEW_NUM_POSTS']) if 'BOT_NEW_NUM_POSTS' in os.environ else 1000,
        int(os.environ['BOT_THRESH'])
    ],
]
