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
    sub = 0
    for submission in subreddit.top('all', limit=10000):
        sub += 1
        print("{} --> Starting new submission {}".format(sub, submission.id))
        if (not Database.isLogged(conn, submission.url, submission.selftext)):
            Database.addUser(conn, submission.title, submission.created, submission.url, submission.selftext)
            print("Added {}".format(submission.title))
    sub = 0
    for submission in subreddit.stream.submissions():
        sub += 1
        print("{} --> Starting new submission {}".format(sub, submission.id))
        if (not Database.isLogged(conn, submission.url, submission.selftext)):
            Database.addUser(conn, submission.title, submission.created, submission.url, submission.selftext)
            print("Added {}".format(submission.title))
        elif sub > 100:
            submission.report('REPOST')
        

Database.initDatabase(conn)
findPosts()
print(Database.getAll(conn))