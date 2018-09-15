import os

client_id = os.environ['BOT_CLIENT_ID']
client_secret = os.environ['BOT_CLIENT_SECRET']
user_agent = os.environ['BOT_USER_AGENT']
username = os.environ['BOT_USERNAME']
password = os.environ['BOT_PASSWORD']
subSettings = [
    [
        os.environ['BOT_SUBREDDIT'],
        int(6),
        int(os.environ['BOT_HOT_DAYS']),
        int(os.environ['BOT_NEW_DAYS']),
        int(os.environ['BOT_TOP_NUM_POSTS']) if os.environ['BOT_TOP_NUM_POSTS'] else 1000,
        int(os.environ['BOT_HOT_NUM_POSTS']) if os.environ['BOT_HOT_NUM_POSTS'] else 1000,
        int(os.environ['BOT_NEW_NUM_POSTS']) if os.environ['BOT_NEW_NUM_POSTS'] else 1000,
        int(os.environ['BOT_THRESH'])
    ],
]
