import praw
import sqlite3
import random 
import Config
import Database

reddit = praw.Reddit(client_id=Config.client_id,
                     client_secret=Config.client_secret,
                     username=Config.username,
                     password=Config.password,
                     user_agent=Config.user_agent)

subreddit = reddit.subreddit('ihadastroke')

conn = sqlite3.connect("Posts.db")

def findPosts():
    print("Starting searching...")
    post = 0
    for submission in subreddit.top('all', limit=10000):
        post += 1
        print("{} --> Starting new submission {}".format(post, submission.id))
        result = Database.isLogged(conn, submission.url, submission.selftext, submission.created)
        if (result[0] == ""):
            Database.addUser(conn, submission.created, submission.url, submission.permalink, submission.selftext)
            print("Added {}".format(submission.permalink))
    psot = 0
    for submission in subreddit.stream.submissions():
        post += 1
        print("{} --> Starting new submission {}".format(post, submission.id))
        result = Database.isLogged(conn, submission.url, submission.selftext, submission.created)
        if (result[0] == ""):
            Database.addUser(conn, submission.created, submission.url, submission.permalink, submission.selftext)
            print("Added {}".format(submission.permalink))
        elif post > 100:
            submission.report('REPOST ALERT: https://reddit.com' + result[0])
            doThis = True
            while doThis:
                try:
                    submission.reply('I have detected that this may be a [repost](https://reddit.com' + result[0] + ') from ' + result[1] + "\n\n*Beep Boop* I am a bot | [Source](https://github.com/xXAligatorXx/repostChecker) | Contact u/XXAligatorXx for inquiries.")
                    doThis = False
                except:
                    doThis = True

Database.initDatabase(conn)
findPosts()
print(Database.getAll(conn))
