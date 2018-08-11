import praw
import Config
import sqlite3
import datetime
from datetime import timedelta
from calendar import monthrange
from urllib.request import Request, urlopen
from io import BytesIO
import ssl
from PIL import Image
import dhash

reddit = praw.Reddit(client_id=Config.client_id,
                     client_secret=Config.client_secret,
                     username=Config.username,
                     password=Config.password,
                     user_agent=Config.user_agent)

context = ssl._create_unverified_context()
user_agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 5_0 like Mac OS X) AppleWebKit/534.46'

def initDatabase(conn):
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS Posts (Date INT, Content TEXT, Url TEXT, State INTEGER DEFAULT 1);')
    conn.commit()
    c.close()
    print('Create table.')

def isInt(s):
    try: 
        int(s)
        return True
    except:
        return False

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

def isLogged(conn, postImageUrl, postText, date):
    args = None
    result = []
    originalPostDate = []
    finalTimePassed = []
    status = []
    precentageMatched = []
    postsToRemove = []
    delete = False
    cntr = 0
    returnResult = []
    c = conn.cursor()

    now = datetime.datetime.utcnow()
    then = datetime.datetime.fromtimestamp(date)
    timePassed = (now-then).days
    if timePassed > Config.days:
        c.execute('DELETE FROM Posts WHERE Url = ?;', (str(postImageUrl),))
        result = ['delete']
        originalPostDate = [-1]
        finalTimePassed = [-1]
        precentageMatched = [-1]
        status = [-1]
        print('the post is older than needed')
    else:
        args = c.execute('SELECT COUNT(1) FROM Posts WHERE Date = ?;', (str(date),))
        if list(args.fetchone())[0] != 0:
                args = c.execute('SELECT Url, Date FROM Posts WHERE Date = ?;', (str(date),))
                fullResult = list(args.fetchall())
                for i in fullResult:
                    result.append(i[0])
                    originalPostDate.append(i[1])
                    precentageMatched.append(100)        
        else:
            if postText != '':      
                args = c.execute('SELECT COUNT(1) FROM Posts WHERE Content = ?;', (str(postText),))
                if list(args.fetchone())[0] != 0:
                    args = c.execute('SELECT Url, Date FROM Posts WHERE Content = ?;', (str(postText),))
                    fullResult = list(args.fetchall())
                    for i in fullResult:
                        result.append(i[0])
                        originalPostDate.append(i[1])
                        precentageMatched.append(100)        
            if postImageUrl != '':
                args = c.execute('SELECT COUNT(1) FROM Posts WHERE Content = ?;', (str(postImageUrl),))
                if list(args.fetchone())[0] != 0:
                    args = c.execute('SELECT Url, Date FROM Posts WHERE Content = ?;', (str(postImageUrl),))
                    fullResult = list(args.fetchall())
                    for i in fullResult:
                        result.append(i[0])
                        originalPostDate.append(i[1])
                        precentageMatched.append(100)        
                if postImageUrl.endswith('png') or postImageUrl.endswith('jpg'):
                    try:
                        file1 = BytesIO(urlopen(Request(str(postImageUrl), headers={'User-Agent': user_agent}), context = context).read())
                    except:
                        delete = True
                    if not delete:
                        img1 = Image.open(file1)
                        args = c.execute('SELECT COUNT(1) FROM Posts WHERE Content = ?;', (str(dhash.dhash_int(img1)),))
                        if list(args.fetchone())[0] != 0:
                            args = c.execute('SELECT Url, Date FROM Posts WHERE Content = ?;', (str(dhash.dhash_int(img1)),))
                            fullResult = list(args.fetchall())
                            for i in fullResult:
                                result.append(i[0])
                                originalPostDate.append(i[1])
                                precentageMatched.append(100)        
                        args = c.execute('SELECT Content, Url, Date FROM posts;')
                        for hashed in args.fetchall():
                            if hashed[1] not in result:
                                hashedReadable = hashed[0]
                                if isInt(hashedReadable):
                                    hashedDifference = dhash.get_num_bits_different(dhash.dhash_int(img1), int(hashedReadable))
                                    if hashedDifference < Config.threshold:
                                        result.append(hashed[1])
                                        originalPostDate.append(hashed[2])
                                        precentageMatched.append(((20 - hashedDifference)/20)*100)        


    if delete:
        c.execute('DELETE FROM Posts WHERE Url = ?;', (str(postImageUrl),))
        result = ['delete']
        originalPostDate = [-10000]
        finalTimePassed = [-10000]
        print('invalid check so it was ignored')
    for i in result:
        if i != '' and i != 'delete':
            if reddit.submission(url = 'https://reddit.com' + i).selftext == '[deleted]':
                c.execute('DELETE FROM Posts WHERE Url = ?;', (str(i),))
                postsToRemove.append([i, originalPostDate[cntr]])
                print('deleted ' + i)
            if reddit.submission(url = 'https://reddit.com' + i).selftext == '[removed]':
                status.append('deleted')
            else:
                status.append('not deleted')
        cntr += 1
            
    for i in postsToRemove:
        result.remove(i[0])
        originalPostDate.remove(i[1])
    
    c.close()
    for i in originalPostDate:
        then = datetime.datetime.fromtimestamp(i)
        timePassed = monthDelta(then, now)
        fullText = (str(timePassed) + ' months ago')
        if timePassed < 1:
            timePassed = (now-then).days
            fullText = (str(timePassed) + ' days ago')
        if timePassed < 1:
            timePassed = (now-then).total_seconds()//3600
            fullText = (str(timePassed) + ' hours ago')
        if timePassed < 1:
            timePassed = (now-then).total_seconds()//60
            fullText = (str(timePassed) + ' minutes ago')
        if timePassed < 1:
            timePassed = (now-then).total_seconds()
            fullText = (str(timePassed) + ' seconds ago')
        finalTimePassed.append(fullText)
    cntr = 0
    for i in result:
        returnResult.append([i, finalTimePassed[cntr], originalPostDate[cntr], precentageMatched[cntr], status[cntr]])
        cntr += 1
    print('Found? {}'.format(returnResult))

    return returnResult
    
def addPost(conn, date, postContentUrl, postUrl, postText):
    c = conn.cursor()
    if postText != '':
        content = postText
    else:
        if postContentUrl.endswith('png') or postContentUrl.endswith('jpg'):
            file1 = BytesIO(urlopen(Request(str(postContentUrl), headers={'User-Agent': user_agent}), context = context).read())
            img1 = Image.open(file1)
            content = dhash.dhash_int(img1)
        else:
            content = postContentUrl
    c.execute('INSERT INTO Posts (Date, Content, Url) VALUES (?, ?, ?);', (int(date), str(content), str(postUrl),))
    conn.commit()
    c.close()
    print('Added new post - {}'.format(str(date)))

def getAll(conn):
    c = conn.cursor()
    args = c.execute('SELECT Content FROM posts;')
    result = [x[0] for x in args.fetchall()]
    c.close()
    return result
