# Repost Checker

# Overview
This bot is able to notice reposts of any kind(link, text, picture) where the original post has not been deleted, report the post, and make a comment with details about the original post. It can be configured to work with any subreddit's rules.

# Setup
1. download python 3.5+.
2. download/clone the repository.
3. "pip3 install -r requirements.txt" to install dependencies.
4. set up environmental variables for the config file with your bot [credintionals](https://github.com/reddit-archive/reddit/wiki/OAuth2) and subreddit.
5. run app.py with "python3 app.py".

# Dependencies
[praw](https://praw.readthedocs.io/en/latest/) : connecting to reddit

[pillow](https://pillow.readthedocs.io/en/latest/): getting the image in a usable format

[dhash](https://github.com/Jetsetter/dhash): seeing the difference between images

[Levenshtein](https://github.com/ztane/python-Levenshtein/): seeing the difference between texts

[PyAV](https://github.com/mikeboers/PyAV): turning videoes into frames

# Contribution
Feel free to fork the repository and tackle any issues. You may also open new issues.

# Subreddits using the bot
[r/ihadastroke](https://www.reddit.com/r/ihadastroke/)
[r/ProgrammerHumor](https://www.reddit.com/r/ProgrammerHumor)

if you are using the bot and your subreddit is not listed above, please [contact me](https://www.reddit.com/user/XXAligatorXx)
