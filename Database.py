# packages that need to be pip installed
import praw
from PIL import Image
import dhash

# other files
import Config

# packages that come with python
import sqlite3
import datetime
from datetime import timedelta
from calendar import monthrange
from urllib.request import Request, urlopen
from io import BytesIO
import ssl

reddit = praw.Reddit(client_id=Config.client_id,
                     client_secret=Config.client_secret,
                     username=Config.username,
                     password=Config.password,
                     user_agent=Config.user_agent)

context = ssl._create_unverified_context()
user_agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 5_0 like Mac OS X) AppleWebKit/534.46'

# initializes the database
def initDatabase(conn):
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS Posts (Date INT, Content TEXT, Url TEXT, State INTEGER DEFAULT 1);")
    conn.commit()
    c.close()
    print("Create table.")

# checks if a value is an integer or not
def isInt(s):
    try: 
        int(s)
        return True
    except:
        return False

# figures out how many months have passed since the post that was found
def monthDelta(d1, d2):
    delta = 0
    while True:
        mdays = monthrange(d1.year, d1.month)[1]
        d1 += timedelta(days=mdays)
        if d1 <= d2:
            delta += 1
        else:
            break
    return delta

# checks if post is in the database
def isLogged(conn, postImageUrl, postText, date):
    result = ""
    args = None
    originalPostDate = None
    c = conn.cursor()

    # checks text posts
    if postText != "":
        args = c.execute("SELECT COUNT(1) FROM Posts WHERE Content = ?;", (str(postText),))
        if list(args.fetchone())[0] != 0:
            args = c.execute("SELECT Url, Date FROM Posts WHERE Content = ?;", (str(postText),))
            fullResult = list(args.fetchone())
            result = fullResult[0]
            originalPostDate = fullResult[1]
        
    # checks images
    elif postImageUrl != "":

        # checks image url(this would check other urls too)
        args = c.execute("SELECT COUNT(1) FROM Posts WHERE Content = ?;", (str(postImageUrl),))
        if list(args.fetchone())[0] != 0:
            args = c.execute("SELECT Url, Date FROM Posts WHERE Content = ?;", (str(postImageUrl),))
            fullResult = list(args.fetchone())
            result = fullResult[0]
            originalPostDate = fullResult[1]

        # checks via hash
        elif postImageUrl.endswith('png') or postImageUrl.endswith('jpg'):
            file1 = BytesIO(urlopen(Request(str(postImageUrl), headers={'User-Agent': user_agent}), context = context).read())
            img1 = Image.open(file1)

            # checks hash
            args = c.execute("SELECT COUNT(1) FROM Posts WHERE Content = ?;", (str(dhash.dhash_int(img1)),))
            if list(args.fetchone())[0] != 0:
                args = c.execute("SELECT Url FROM Posts WHERE Content = ?;", (str(dhash.dhash_int(img1)),))
                result = list(args.fetchone())[0]

            # checks if there is a close hash
            else:
                args = c.execute("SELECT Content, Url, Date FROM posts;")
                for hashed in args.fetchall():
                    hashedReadable = hashed[0]
                    if isInt(hashedReadable):
                        hashedDifference = dhash.get_num_bits_different(dhash.dhash_int(img1), int(hashedReadable))
                        print(hashedDifference)
                        if hashedDifference < 10:
                            result = hashed[1]
                            originalPostDate = hashed[2]

    # checks if post is more than 6 months old or has been removed.
    now = datetime.datetime.utcnow()
    then = datetime.datetime.fromtimestamp(date)
    timePassed = monthdelta(then, now)
    if result != "":
        if timePassed > 6 or reddit.submission(url = "https://reddit.com" + result).selftext == "[deleted]" or reddit.submission(url = "https://reddit.com" + result).selftext == "[removed]":
            c.execute("DELETE FROM Posts WHERE Url = ?;", (str(result),))
            result = ""
            print('deleted')
    c.close()
    print("Found? {}".format(result))

    # gives how long it has been since original post
    if originalPostDate != None:
        then = datetime.datetime.fromtimestamp(originalPostDate)
        timePassed = monthdelta(then, now)
        
    # returns results
    if timePassed >= 1:
        return result, str(timePassed) + ' months ago'
    elif (now-then).days >= 1:
        return result, str((now-then).days) + ' days ago'
    elif (now-then).seconds//3600 >= 1:
        return result, str((now-then).seconds//3600) + ' hours ago'
    elif (now-then).seconds//60 >= 1:
        return result, str((now-then).seconds//60) + ' minutes ago'
    else:
        return result, str((now-then).seconds) + ' seconds ago'
    
# adds a post
def addPost(conn, date, postContentUrl, postUrl, postText):
    c = conn.cursor()
    if postText != "":
        content = postText
    else:
        if postContentUrl.endswith('png') or postContentUrl.endswith('jpg'):
            file1 = BytesIO(urlopen(Request(str(postContentUrl), headers={'User-Agent': user_agent}), context = context).read())
            img1 = Image.open(file1)
            content = dhash.dhash_int(img1)
        else:
            content = postContentUrl
    c.execute("INSERT INTO Posts (Date, Content, Url) VALUES (?, ?, ?);", (int(date), str(content), str(postUrl),))
    conn.commit()
    c.close()
    print("Added new post - {}".format(str(date)))

# gets everything in the database(only useful for testing)
def getAll(conn):
    c = conn.cursor()
    args = c.execute("SELECT Content FROM posts;")
    result = [x[0] for x in args.fetchall()]
    c.close()
    return result
