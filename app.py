# packages that need to be pip installed
import praw

# packages that come with python
import sqlite3
import random
import sys
import traceback
import time
import re
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

class findPosts(Thread):
    def __init__(self, subSettings):
        ''' Constructor. '''
        Thread.__init__(self)
        self.subSettings = subSettings
        self.q = Queue()
    def run(self):
        Thread(target=self.findTopPosts).start()
        Thread(target=self.findHotPosts).start()
        Thread(target=self.findNewPosts).start()
    def findTopPosts(self):
        conn = sqlite3.connect('Posts'+re.sub('([a-zA-Z])', lambda x: x.groups()[0].upper(), self.subSettings[0], 1)+'.db')
        subreddit = reddit.subreddit(self.subSettings[0])
        top = True
        hot = False
        new = False
        firstTime = True
        limitVal = self.subSettings[4]
        print('Starting searching...')
        while True:
            try:
                post = 0
                top = False
                hot = True
                # first get 50 posts from the top of the subreddit
                for submission in subreddit.top('all', limit=limitVal):
                    while True:
                        if (not self.q.empty()) or firstTime:
                            try:
                                x = self.q.queue[0]
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
                                    new,
                                    self.subSettings,
                                )

                                if result != [['delete', -1, -1, -1]] and (result == [] or submission.created_utc != result[0][2]):
                                    database.addPost(
                                        conn,
                                        submission.created_utc,
                                        submission.url,
                                        submission.media,
                                        submission.permalink,
                                        submission.selftext,
                                        submission.author,
                                        submission.score,
                                        submission.title,
                                        top,
                                        hot,
                                        new,
                                    )
                                    print('{} --> Added {}'.format(post,
                                                                submission.permalink))
                                with self.q.mutex:
                                    self.q.queue.clear()
                                self.q.put('doneRunningTop')
                                break

            except Exception as e:
                print(traceback.format_exc())
                if '503' in str(e):
                    print('503 from server')
                else:
                    f = open('errs.txt', 'a')
                    f.write(str(traceback.format_exc()))


    def findHotPosts(self):
        conn = sqlite3.connect('Posts'+re.sub('([a-zA-Z])', lambda x: x.groups()[0].upper(), self.subSettings[0], 1)+'.db')
        subreddit = reddit.subreddit(self.subSettings[0])
        top = False
        hot = True
        new = False
        limitVal = self.subSettings[5]
        while True:
            try:
                post = 0
                # then get 50 posts from trending of the subreddit
                for submission in subreddit.hot(limit=limitVal):
                    while True:
                        if not self.q.empty():
                            try:
                                x = self.q.queue[0]
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
                                    new,
                                    self.subSettings,
                                )
                                if result != [['delete', -1, -1, -1]] and (result == [] or submission.created_utc != result[0][2]):
                                    database.addPost(
                                        conn,
                                        submission.created_utc,
                                        submission.url,
                                        submission.media,
                                        submission.permalink,
                                        submission.selftext,
                                        submission.author,
                                        submission.score,
                                        submission.title,
                                        top,
                                        hot,
                                        new,
                                    )
                                    print('{} --> Added {}'.format(post,
                                                                submission.permalink))
                                with self.q.mutex:
                                    self.q.queue.clear()
                                self.q.put('doneRunningHot')
                                break

            except Exception as e:
                print(traceback.format_exc())
                if '503' in str(e):
                    print('503 from server')
                else:
                    f = open('errs.txt', 'a')
                    f.write(str(traceback.format_exc()))


    def findNewPosts(self):
        conn = sqlite3.connect('Posts'+re.sub('([a-zA-Z])', lambda x: x.groups()[0].upper(), self.subSettings[0], 1)+'.db')
        subreddit = reddit.subreddit(self.subSettings[0])
        top = False
        hot = False
        new = True
        limitVal = self.subSettings[6]
        while True:
            try:
                post = 0
                # then get 1000 posts from new of the subreddit
                for submission in subreddit.new(limit=limitVal):
                    while True:
                        if not self.q.empty():
                            try:
                                x = self.q.queue[0]
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
                                    new,
                                    self.subSettings,
                                )
                                if result != [['delete', -1, -1, -1]] and (result == [] or submission.created_utc != result[0][2]):
                                    database.addPost(
                                        conn,
                                        submission.created_utc,
                                        submission.url,
                                        submission.media,
                                        submission.permalink,
                                        submission.selftext,
                                        submission.author,
                                        submission.score,
                                        submission.title,
                                        top,
                                        hot,
                                        new,
                                    )
                                    print('{} --> Added {}'.format(post,
                                                                submission.permalink))
                                if result != [] and result != [['delete', -1, -1, -1]]:
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
                                        '\n*Beep Boop* I am a bot | [Source](https://github.com/xXAligatorXx/repostChecker) | Contact u/XXAligatorXx for inquiries | The bot will delete its message at -2 score'
                                    doThis = True
                                    while doThis:
                                        try:
                                            submission.reply(fullText)
                                            doThis = False
                                        except:
                                            doThis = True
                                with self.q.mutex:
                                    self.q.queue.clear()
                                self.q.put('doneRunningNew')
                                break
                limitVal = 10
            except Exception as e:
                print(traceback.format_exc())
                if '503' in str(e):
                    print('503 from server')
                else:
                    f = open('errs.txt', 'a')
                    f.write(str(traceback.format_exc()))

for i in config.subSettings:
    conn = sqlite3.connect('Posts'+re.sub('([a-zA-Z])', lambda x: x.groups()[0].upper(), i, 1)+'.db')
    database.initDatabase(conn)
    thread = findPosts(i)
    if i[1] is not None or i[2] is not None or i[3] is not None:
        deleteOldThread = Thread(target=database.deleteOldFromDatabase, args=(conn, i))
        deleteOldThread.start()
    thread.start()
    thread.join()
    if deleteOldThread is not None:
        deleteOldThread.join()

# self.q = Queue()
deleteThread = Thread(target=deleteComment)
# findTopThread = Thread(target=findPosts.findTopPosts, args=(5,))
# findHotThread = Thread(target=findHotPosts, args=(self.q,))
# findNewThread = Thread(target=findNewPosts, args=(self.q,))

deleteThread.start()
# findTopThread.start()
# findHotThread.start()
# findNewThread.start()

deleteThread.join()
# findTopThread.join()
# findHotThread.join()
# findNewThread.join()