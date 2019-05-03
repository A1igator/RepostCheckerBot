import os

client_id = os.environ['BOT_CLIENT_ID']
client_secret = os.environ['BOT_CLIENT_SECRET']
user_agent = os.environ['BOT_USER_AGENT']
username = os.environ['BOT_USERNAME']
password = os.environ['BOT_PASSWORD']
sub_settings = [[
        os.environ['BOT_SUBREDDIT' + i],
        int(os.environ['BOT_TOP_DAYS' + i]) if 'BOT_TOP_DAYS' + i in os.environ else None,
        int(os.environ['BOT_HOT_DAYS' + i]) if 'BOT_HOT_DAYS' + i in os.environ else None,
        int(os.environ['BOT_NEW_DAYS' + i]) if 'BOT_NEW_DAYS' + i in os.environ else None,
        int(os.environ['BOT_TOP_NUM_POSTS' + i]) if 'BOT_TOP_NUM_POSTS' + i in os.environ else 1000,
        int(os.environ['BOT_HOT_NUM_POSTS' + i]) if 'BOT_HOT_NUM_POSTS' + i in os.environ else 1000,
        int(os.environ['BOT_NEW_NUM_POSTS' + i]) if 'BOT_NEW_NUM_POSTS' + i in os.environ else 1000,
        int(os.environ['BOT_THRESH' +i]) if 'BOT_THRESH' + i in os.environ else 5,
        bool(os.environ['BOT_TEXT_IN_IMAGE' + i]) if 'BOT_TEXT_IN_IMAGE' + i in os.environ else False,
    ] for i in [str(x) for x in range(5)]]
