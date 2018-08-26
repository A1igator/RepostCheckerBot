# packages that need to be pip installed
import praw

# packages that come with python
import sqlite3
import random
import sys
import threading
import queue

# other files
import config
import database

reddit = praw.Reddit(client_id=config.client_id,
                     client_secret=config.client_secret,
                     username=config.username,
                     password=config.password,
                     user_agent=config.user_agent)

subreddit = reddit.subreddit(config.subreddit)

conn = sqlite3.connect('Posts'+config.subreddit+'.db')


def deleteComment():
    while True:
        try:
            for comment in reddit.redditor('RepostCheckerBot').comments.new(limit=50):
                if(comment.score is 0):
                    comment.delete()
        except KeyboardInterrupt:
            print('test')

        except Exception as e:
            print('test')
            if '503' in str(e):
                print('503 from server')
            else:
                f = open('errs.txt', 'a')
                f.write(str(e))
# the main function


class findPosts(threading.Thread):

    def __init__(self, bucket):
        threading.Thread.__init__(self)
        self.bucket = bucket

    def run(self):
        try:
            print('test')
        except Exception:
            self.bucket.put(sys.exc_info())


database.initDatabase(conn)
# deleteThread = threading.Thread(target=deleteComment)
# findThread = findPosts()
bucket = queue.Queue()
thread_obj = findPosts(bucket)
thread_obj.start()

while True:
    try:
        exc = bucket.get(block=False)
    except queue.Empty:
        pass
    else:
        exc_type, exc_obj, exc_trace = exc
        # deal with the exception
        print(exc_type, exc_obj)
        print(exc_trace)

    thread_obj.join(0.1)
    if thread_obj.isAlive():
        continue
    else:
        break

# deleteThread.start()
# findThread.start()

# deleteThread.join()
# findThread.join()

print(database.getAll(conn))
