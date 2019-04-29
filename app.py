# packages that need to be pip installed
import praw
from psaw import PushshiftAPI

# packages that come with python
import traceback
from multiprocessing import Process, Value
from time import sleep

# other files
import config
import database
rows = []
reddit = praw.Reddit(client_id=config.client_id,
                     client_secret=config.client_secret,
                     username=config.username,
                     password=config.password,
                     user_agent=config.user_agent)
api = PushshiftAPI(reddit)


def delete_comment():
    while True:
        try:
            for comment in reddit.redditor('RepostCheckerBot').comments.new(limit=50):
                if comment.score < -1:
                    f = open('fails.txt', 'a')
                    f.write(str(comment.body))
                    comment.delete()

        except Exception as e:
            print(e)
            print(repr(e))
            if '503' in str(e):
                print('503 from server')
            if '504' in str(e):
                print('504 from server')  
            if '401' in str(e):
                print('401 from server')                  
            else:
                f = open('errs.txt', 'a')
                if '{}\n'.format(str(traceback.format_exc())) not in f.read():
                    f.write('{}\n'.format(str(traceback.format_exc())))
        sleep(1800)


# the main function
class FindPosts(Process):
    def __init__(self, sub_settings):
        # Constructor.
        Process.__init__(self)
        self.sub_settings = sub_settings
        self.v = Value('i', 0)

    def run(self):
        Process(target=self.find_top_posts).start()
        self.findNewPosts()

    def find_top_posts(self):
        subreddit = reddit.subreddit(self.sub_settings[0])
        print(self.sub_settings)
        new = False
        first_time = True
        print('Starting searching...')
        while True:
            try:
                post = 0
                # first get 50 posts from the top of the subreddit
                for submission in api.search_submissions(subreddit=subreddit):
                    while True:
                        if (self.v.value != 0) or first_time:
                            try:
                                x = self.v.value
                            except IndexError as e:
                                if 'deque index out of range' not in str(e):
                                    raise IndexError(e)
                            if first_time or (x is not None and x == 2):
                                first_time = False
                                top = True
                                hot = False
                                post += 1
                                print(post)
                                result = database.is_logged(
                                    submission.url,
                                    submission.media,
                                    submission.selftext,
                                    submission.permalink,
                                    submission.created_utc,
                                    top,
                                    hot,
                                    new,
                                    self.sub_settings,
                                    reddit,
                                )

                                if result != [['delete', -1, -1, -1, -1, -1]] and (result == [] or submission.created_utc != result[0][2]):
                                    rows.append(database.add_post(
                                        submission.created_utc,
                                        submission.url,
                                        submission.media,
                                        submission.permalink,
                                        submission.selftext,
                                        submission.author,
                                        submission.title,
                                        top,
                                        hot,
                                        new,
                                        self.sub_settings[0],
                                        self.sub_settings[8]
                                    ))
                                    print('{} --> Added {}'.format(
                                        post,
                                        submission.permalink,
                                    ))
                                self.v.value = 1
                                break

            except Exception as e:
                print(traceback.format_exc())
                if '503' in str(e):
                    print('503 from server')
                if '401' in str(e):
                    print('401 from server')
                else:
                    f = open('errs.txt', 'a')
                    error = str(traceback.format_exc())
                    if error not in f.read():
                        f.write(error)

    def findNewPosts(self):
        subreddit = reddit.subreddit(self.sub_settings[0])
        top = False
        hot = False
        new = True
        limit_val = self.sub_settings[6]
        while True:
            try:
                post = 0
                # then get 1000 posts from new of the subreddit
                for submission in api.search_submissions(subreddit=subreddit, limit=limit_val):
                    while True:
                        if self.v.value != 0:
                            try:
                                x = self.v.value
                            except IndexError as e:
                                if 'deque index out of range' not in str(e):
                                    raise IndexError(e)
                            if x is not None and x == 1:
                                post += 1
                                result = database.is_logged(
                                    submission.url,
                                    submission.media,
                                    submission.selftext,
                                    submission.permalink,
                                    submission.created_utc,
                                    top,
                                    hot,
                                    new,
                                    self.sub_settings,
                                    reddit,
                                )
                                if result != [['delete', -1, -1, -1, -1, -1]] and (result == [] or submission.created_utc != result[0][2]):
                                    rows.append(database.add_post(
                                        submission.created_utc,
                                        submission.url,
                                        submission.media,
                                        submission.permalink,
                                        submission.selftext,
                                        submission.author,
                                        submission.title,
                                        top,
                                        hot,
                                        new,
                                        self.sub_settings[0],
                                        self.sub_settings[8],
                                    ))
                                    print('{} --> Added {}'.format(
                                        post,
                                        submission.permalink,
                                    ))

                                if result != [] and result != [['delete', -1, -1, -1, -1, -1]]:
                                    print('reported')
                                    # report and make a comment
                                    submission.report('REPOST ALERT')
                                    cntr = 0
                                    table = ''
                                    for i in result:
                                        table = '{}{}|[{}](https://reddit.com{})|{}|{}%|{}\n'.format(
                                            table,
                                            str(cntr),
                                            i[5],
                                            i[0],
                                            i[1],
                                            str(i[3]),
                                            i[4],
                                        )
                                        cntr += 1
                                    full_text = 'I have detected that this may be a repost: \n'+ \
                                        '\nNum|Post|Date|Match|Author\n:--:|:--:|:--:|:--:|:--:\n{}'.format(table) + \
                                        '\n*Beep Boop* I am a bot | [Source](https://github.com/xXAligatorXx/repostChecker)' + \
                                        '| Contact u/XXAligatorXx for inquiries | The bot will delete its message at -2 score'
                                    do_this = True
                                    while do_this:
                                        try:
                                            submission.reply(full_text)
                                            do_this = False
                                        except:
                                            do_this = True
                                self.v.value = 2
                                break

                limit_val = 10
            except Exception as e:
                print(traceback.format_exc())
                if '503' in str(e):
                    print('503 from server')
                if '401' in str(e):
                    print('401 from server')
                else:
                    f = open('errs.txt', 'a')
                    error = str(traceback.format_exc())
                    if error not in f.read():
                        f.write(error)

thread_count = 0
threads = []
deleteOldThread = []
for i in config.sub_settings:
    if i is not None:
        database.init_database(i[0], i[8])
        threads.append(FindPosts(i))
        if i[1] is not None or i[2] is not None or i[3] is not None:
            deleteOldThread.append(Process(target=database.delete_old_from_database, args=(i,)))
            deleteOldThread[thread_count].start()
        threads[thread_count].start()
        thread_count += 1

deleteThread = Process(target=delete_comment)

deleteThread.start()

deleteThread.join()
for i in range(0, len(threads)):
    if 'deleteOldThread' in vars():
        deleteOldThread[i].join()
    threads[i].join()
