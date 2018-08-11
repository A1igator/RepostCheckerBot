# packages that need to be pip installed
import praw

# packages that come with python
import sqlite3
import random 

# other files
import Config
import Database

reddit = praw.Reddit(client_id=Config.client_id,
                     client_secret=Config.client_secret,
                     username=Config.username,
                     password=Config.password,
                     user_agent=Config.user_agent)

subreddit = reddit.subreddit(Config.subreddit)

conn = sqlite3.connect('Posts'+Config.subreddit+'.db')

c = conn.cursor()

# the main function
def findPosts():
    print('Starting searching...')
    post = 0
    # first get 1000 posts from the top of the subreddit
    for submission in subreddit.top('all', limit=1000):
        post += 1
        print('{} --> Starting new submission {}'.format(post, submission.id))
        result = Database.isLogged(conn, submission.url, submission.selftext, submission.created_utc)
        if result != [['delete',-1,-1,-1,-1]] and (result == [] or submission.created_utc != result[0][2]):
            Database.addPost(conn, submission.created_utc, submission.url, submission.permalink, submission.selftext)
            print('Added {}'.format(submission.permalink))
    post = 0
    # then get 10000 posts from new of the subreddit
    for submission in subreddit.new(limit=1000):
        post += 1
        print('{} --> Starting new submission {}'.format(post, submission.id))
        result = Database.isLogged(conn, submission.url, submission.selftext, submission.created_utc)
        if result != [['delete',-1,-1,-1,-1]] and (result == [] or submission.created_utc != result[0][2]):
            Database.addPost(conn, submission.created_utc, submission.url, submission.permalink, submission.selftext)
            print('Added {}'.format(submission.permalink))
    post = 0
    # then check posts as they come in
    for submission in subreddit.stream.submissions():
        ignoreImage = False
        post += 1
        print('{} --> Starting new submission {}'.format(post, submission.id))
        result = Database.isLogged(conn, submission.url, submission.selftext, submission.created_utc)
        if result != [['delete',-1,-1,-1,-1]] and (result == [] or submission.created_utc != result[0][2]):
            Database.addPost(conn, submission.created_utc, submission.url, submission.permalink, submission.selftext)
            print('Added {}'.format(submission.permalink))
        if result != [] and result != [['delete',-1,-1,-1,-1]] and post > 1:
                print('reported')
                # report and make a comment
                submission.report('REPOST ALERT')
                cntr = 0
                table = ''
                for i in result:
                    table = table + str(cntr) + '|[post](https://reddit.com' + i[0] + ')|' + i[1] + '|' + str(i[3]) + '%|' + i[4] + '\n'
                    cntr += 1
                fullText = 'I have detected that this may be a repost: \n\nNum|Post|Date|Match|Status\n:--:|:--:|:--:|:--:|:--:\n' + table + '\n*Beep Boop* I am a bot | [Source](https://github.com/xXAligatorXx/repostChecker) | Contact u/XXAligatorXx for inquiries.'
                doThis = True
                while doThis:
                    try:
                        submission.reply(fullText)
                        doThis = False
                    except:
                        doThis = True


Database.initDatabase(conn)
findPosts()
print(Database.getAll(conn))
