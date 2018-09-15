# packages that need to be pip installed
import praw

# packages that come with python
import sqlite3
import random
import sys
import traceback
import time
from threading import Thread, Timer
from queue import Queue

# other files
import config
import database

reddit = praw.Reddit(client_id=config.client_id,
                     client_secret=config.client_secret,
                     username=config.username,
                     password=config.password,
                     user_agent=config.user_agent)

subreddit = reddit.subreddit(config.subSettings[0][0])

conn = sqlite3.connect('Posts'+config.subSettings[0][0]+'.db')


def deleteComment():
    while True:
        try:
            for comment in reddit.redditor('RepostCheckerBot').comments.new(limit=50):
                if(comment.score < -1):
                    f = open('fails.txt', 'a')
                    f.write(str(comment.body))
                    comment.delete()

        except Exception as e:
            print(e)
            print(repr(e))
            if '503' in str(e):
                print('503 from server')
            else:
                f = open('errs.txt', 'a')
                f.write(str(traceback.format_exc()) + '\n')
# the main function


def findTopPosts(q):
    conn = sqlite3.connect('Posts'+config.subSettings[0][0]+'.db')
    top = False
    hot = True
    firstTime = True
    limitVal = config.subSettings[0][4]
    print('Starting searching...')
    while True:
        try:
            post = 0
            top = False
            hot = True
            # first get 50 posts from the top of the subreddit
            for submission in subreddit.top('all', limit=limitVal):
                while True:
                    if (not q.empty()) or firstTime:
                        try:
                            x = q.queue[0]
                        except IndexError as e:
                            if 'deque index out of range' not in str(e):
                                raise IndexError(e)
                        if firstTime or (x is not None and x is 'doneRunningNew'):
                            firstTime = False
                            top = True
                            hot = False
                            post += 1
                            result = database.isLogged(
                                conn,
                                submission.url,
                                submission.media,
                                submission.selftext,
                                submission.permalink,
                                submission.created_utc,
                                top,
                                hot,
                            )

                            if result != [['delete', -1, -1, -1, -1]] and (result == [] or submission.created_utc != result[0][2]):
                                database.addPost(
                                    conn,
                                    submission.created_utc,
                                    submission.url,
                                    submission.media,
                                    submission.permalink,
                                    submission.selftext,
                                    top,
                                    hot,
                                )
                                print('{} --> Added {}'.format(post,
                                                               submission.permalink))
                            with q.mutex:
                                q.queue.clear()
                            q.put('doneRunningTop')
                            break

        except Exception as e:
            print(e)
            print(repr(e))
            if '503' in str(e):
                print('503 from server')
            else:
                f = open('errs.txt', 'a')
                f.write(str(traceback.format_exc()))


def findHotPosts(q):
    conn = sqlite3.connect('Posts'+config.subSettings[0][0]+'.db')
    top = False
    hot = True
    limitVal = config.subSettings[0][5]
    while True:
        try:
            post = 0
            # then get 50 posts from trending of the subreddit
            for submission in subreddit.hot(limit=limitVal):
                while True:
                    if not q.empty():
                        try:
                            x = q.queue[0]
                        except IndexError as e:
                            if 'deque index out of range' not in str(e):
                                raise IndexError(e)
                        if x is not None and x is 'doneRunningTop':
                            post += 1
                            result = database.isLogged(
                                conn,
                                submission.url,
                                submission.media,
                                submission.selftext,
                                submission.permalink,
                                submission.created_utc,
                                top,
                                hot,
                            )
                            if result != [['delete', -1, -1, -1, -1]] and (result == [] or submission.created_utc != result[0][2]):
                                database.addPost(
                                    conn,
                                    submission.created_utc,
                                    submission.url,
                                    submission.media,
                                    submission.permalink,
                                    submission.selftext,
                                    top,
                                    hot,
                                )
                                print('{} --> Added {}'.format(post,
                                                               submission.permalink))
                            with q.mutex:
                                q.queue.clear()
                            q.put('doneRunningHot')
                            break

        except Exception as e:
            print(e)
            print(repr(e))
            if '503' in str(e):
                print('503 from server')
            else:
                f = open('errs.txt', 'a')
                f.write(str(traceback.format_exc()) + q.queue + q.empty())


def findNewPosts(q):
    conn = sqlite3.connect('Posts'+config.subSettings[0][0]+'.db')
    top = False
    hot = False
    limitVal = config.subSettings[0][6]
    while True:
        try:
            post = 0
            # then get 1000 posts from new of the subreddit
            for submission in subreddit.new(limit=limitVal):
                while True:
                    if not q.empty():
                        try:
                            x = q.queue[0]
                        except IndexError as e:
                            if 'deque index out of range' not in str(e):
                                raise IndexError(e)
                        if x is not None and x is 'doneRunningHot':
                            post += 1
                            result = database.isLogged(
                                conn,
                                submission.url,
                                submission.media,
                                submission.selftext,
                                submission.permalink,
                                submission.created_utc,
                                top,
                                hot,
                            )
                            if result != [['delete', -1, -1, -1, -1]] and (result == [] or submission.created_utc != result[0][2]):
                                database.addPost(
                                    conn,
                                    submission.created_utc,
                                    submission.url,
                                    submission.media,
                                    submission.permalink,
                                    submission.selftext,
                                    top,
                                    hot,
                                )
                                print('{} --> Added {}'.format(post,
                                                               submission.permalink))
                            if result != [] and result != [['delete', -1, -1, -1, -1]]:
                                print('reported')
                                # report and make a comment
                                submission.report('REPOST ALERT')
                                cntr = 0
                                table = ''
                                for i in result:
                                    table = table + \
                                        str(cntr) + '|[post](https://reddit.com' + \
                                        i[0] + ')|' + i[1] + '|' + \
                                        str(i[4]) + '%' + '\n'
                                    cntr += 1
                                fullText = 'I have detected that this may be a repost: \n\nNum|Post|Date|Match\n:--:|:--:|:--:|:--:\n' + table + \
                                    '\n*Beep Boop* I am a bot | [Source](https://github.com/xXAligatorXx/repostChecker) | Contact u/XXAligatorXx for inquiries | The bot will delete its message at -2 score'
                                doThis = True
                                while doThis:
                                    try:
                                        submission.reply(fullText)
                                        doThis = False
                                    except:
                                        doThis = True
                            with q.mutex:
                                q.queue.clear()
                            q.put('doneRunningNew')
                            break
            limitVal = 10
        except Exception as e:
            print(e)
            print(repr(e))
            if '503' in str(e):
                print('503 from server')
            else:
                f = open('errs.txt', 'a')
                f.write(str(traceback.format_exc()))


database.initDatabase(conn)

q = Queue()
deleteThread = Thread(target=deleteComment)
findTopThread = Thread(target=findTopPosts, args=(q,))
findHotThread = Thread(target=findHotPosts, args=(q,))
findNewThread = Thread(target=findNewPosts, args=(q,))
deleteOldThread = Thread(
    target=database.deleteOldFromDatabase)

deleteThread.start()
findTopThread.start()
findHotThread.start()
findNewThread.start()
deleteOldThread.start()

deleteThread.join()
findTopThread.join()
findHotThread.join()
findNewThread.join()
deleteOldThread.join()
