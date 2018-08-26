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
        conn = sqlite3.connect('Posts'+config.subreddit+'.db')
        while True:
            try:
                print('Starting searching...')
                post = 0
                # first get 1000 posts from the top of the subreddit
                for submission in subreddit.top('all', limit=1000):
                    post += 1
                    print(
                        '{} --> Starting new submission {}'.format(post, submission.id))
                    result = database.isLogged(conn, submission.url, submission.media,
                                               submission.selftext, submission.permalink, submission.created_utc)
                    if result != [['delete', -1, -1, -1]] and (result == [] or submission.created_utc != result[0][2]):
                        database.addPost(conn, submission.created_utc, submission.url,
                                         submission.media, submission.permalink, submission.selftext)
                        print('Added {}'.format(submission.permalink))
                post = 0
                # then get 1000 posts from new of the subreddit
                for submission in subreddit.new(limit=1000):
                    post += 1
                    print(
                        '{} --> Starting new submission {}'.format(post, submission.id))
                    result = database.isLogged(conn, submission.url, submission.media,
                                               submission.selftext, submission.permalink, submission.created_utc)
                    if result != [['delete', -1, -1, -1]] and (result == [] or submission.created_utc != result[0][2]):
                        database.addPost(conn, submission.created_utc, submission.url,
                                         submission.media, submission.permalink, submission.selftext)
                        print('Added {}'.format(submission.permalink))
                post = 0
                # then check posts as they come in
                for submission in subreddit.stream.submissions():
                    post += 1
                    print(
                        '{} --> Starting new submission {}'.format(post, submission.id))
                    result = database.isLogged(conn, submission.url, submission.media,
                                               submission.selftext, submission.permalink, submission.created_utc)
                    if result != [['delete', -1, -1, -1]] and (result == [] or submission.created_utc != result[0][2]):
                        database.addPost(conn, submission.created_utc, submission.url,
                                         submission.media, submission.permalink, submission.selftext)
                        print('Added {}'.format(submission.permalink))
                    if result != [] and result != [['delete', -1, -1, -1]] and post > 1:
                        print('reported')
                        # report and make a comment
                        submission.report('REPOST ALERT')
                        cntr = 0
                        table = ''
                        for i in result:
                            table = table + \
                                str(cntr) + '|[post](https://reddit.com' + \
                                i[0] + ')|' + i[1] + '|' + \
                                str(i[3]) + '%' + '\n'
                            cntr += 1
                        fullText = 'I have detected that this may be a repost: \n\nNum|Post|Date|Match\n:--:|:--:|:--:|:--:\n' + table + \
                            '\n*Beep Boop* I am a bot | [Source](https://github.com/xXAligatorXx/repostChecker) | Contact u/XXAligatorXx for inquiries | The bot will delete its message after -2 score'
                        doThis = True
                        while doThis:
                            try:
                                submission.reply(fullText)
                                doThis = False
                            except:
                                doThis = True

            # except KeyboardInterrupt:
            #     try:
            #         print('test')
            #         raise
            #     except:
            #         self.bucket.put(sys.exc_info())
                raise('fuck')
            except Exception:
                self.bucket.put(sys.exc_info())
                # except Exception as e:
                #     print('test')
                #     if '503' in str(e):
                #         print('503 from server')
                #     else:
                #         f = open('errs.txt', 'a')
                #         f.write(str(e))


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
