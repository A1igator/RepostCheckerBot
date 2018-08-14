import praw
import config
import sqlite3
import datetime
from datetime import timedelta
from calendar import monthrange
from urllib.request import Request, urlopen
from io import BytesIO
import ssl
from PIL import Image
import dhash
from hashlib import md5
import av

reddit = praw.Reddit(client_id=config.client_id,
                     client_secret=config.client_secret,
                     username=config.username,
                     password=config.password,
                     user_agent=config.user_agent)

context = ssl._create_unverified_context()
user_agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 5_0 like Mac OS X) AppleWebKit/534.46'

result = []
originalPostDate = []
finalTimePassed = []
precentageMatched = []

def initDatabase(conn):
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS Posts (Date INT, Content TEXT, Url TEXT, State INTEGER DEFAULT 1);')
    conn.commit()
    c.close()
    print('Create table.')

def canonical(s):
    return ''.join([c for c in s if not c.isspace()])

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

def hashImg(imgUrl):
    try:
        f = BytesIO(urlopen(Request(str(imgUrl), headers={'User-Agent': user_agent}), context = context).read())
    except:
        delete(imgUrl)
        print('invalid check so it was ignored')
        return ''
    else:
        img = Image.open(f)
        return dhash.dhash_int(img)

def hashText(txt):
    return md5(txt.encode('utf-8')).hexdigest()

def hashVid(vidUrl):
    hash = ''
    container = av.open(vidUrl)
    for frame in container.decode(video=0):
        dhash.dhash_int(frame.to_image())
        hash += str(dhash.dhash_int(frame.to_image())) + ' '
    return hash

def delete(itemUrl):
    c.execute('DELETE FROM Posts WHERE Url = ?;', (str(itemUrl),))
    ignore()

def ignore():
    result[:] = ['delete']
    originalPostDate[:] = [-1]
    finalTimePassed[:] = [-1]
    precentageMatched[:] = [-1]
      
def addToFound(post, precentage):
    result.append(post[0])
    originalPostDate.append(post[1])
    precentageMatched.append(precentage) 

def isLogged(conn, postContentUrl, postMedia, postText, date):
    result[:] = []
    originalPostDate[:] = []
    finalTimePassed[:] = []
    precentageMatched[:] = []
    args = None
    postsToRemove = []
    delete = False
    cntr = 0
    returnResult = []
    c = conn.cursor()

    now = datetime.datetime.utcnow()
    then = datetime.datetime.fromtimestamp(date)
    timePassed = (now-then).days
    if timePassed > config.days:
        delete(imgUrl)
        print('the post is older than needed')
    else:
        args = c.execute('SELECT COUNT(1) FROM Posts WHERE Date = ?;', (str(date),))
        if list(args.fetchone())[0] != 0:
            ignore()
            print('already done')
        else:
            if postText != '':
                textHash = hashText(postText)
                content = textHash
                args = c.execute('SELECT COUNT(1) FROM Posts WHERE Content = ?;', (str(textHash),))
                if list(args.fetchone())[0] != 0:
                    args = c.execute('SELECT Url, Date FROM Posts WHERE Content = ?;', (str(textHash),))
                    fullResult = list(args.fetchall())
                    for i in fullResult:
                        addToFound(i, 100)
            elif postMedia != None:
                vidHash = hashVid(postMedia['reddit_video']['fallback_url'])
                print(isInt(vidHash.replace(' ', '')))
                if isInt(vidHash.replace(' ', '')):
                    args = c.execute('SELECT COUNT(1) FROM Posts WHERE Content = ?;', (str(vidHash),))
                    if list(args.fetchone())[0] != 0:
                        args = c.execute('SELECT Url, Date FROM Posts WHERE Content = ?;', (str(vidHash),))
                        fullResult = list(args.fetchall())
                        for i in fullResult:
                            addToFound(i, 100)
                    args = c.execute('SELECT Url, Date, Content FROM posts;')
                    for hashed in args.fetchall():
                        if hashed[0] not in result:
                            hashedReadable = hashed[2]
                            print(hashedReadable.split())
                            # if isInt(hashedReadable):
                            #     hashedDifference = dhash.get_num_bits_different(vidHash, int(hashedReadable))
                            #     if hashedDifference < config.threshold:
                            #         addToFound(hashed, ((config.threshold - hashedDifference)/config.threshold)*100)   
            elif postContentUrl != '':
                args = c.execute('SELECT COUNT(1) FROM Posts WHERE Content = ?;', (str(postContentUrl).replace('&feature=youtu.be',''),))
                if list(args.fetchone())[0] != 0:
                    args = c.execute('SELECT Url, Date FROM Posts WHERE Content = ?;', (str(postContentUrl).replace('&feature=youtu.be',''),))
                    fullResult = list(args.fetchall())
                    for i in fullResult:
                        addToFound(i, 100)
                if 'png' in postContentUrl or 'jpg' in postContentUrl or 'gif' in postContentUrl:
                    imgHash = hashImg(postContentUrl)
                    if isInt(imgHash):
                        args = c.execute('SELECT COUNT(1) FROM Posts WHERE Content = ?;', (str(imgHash),))
                        if list(args.fetchone())[0] != 0:
                            args = c.execute('SELECT Url, Date FROM Posts WHERE Content = ?;', (str(imgHash),))
                            fullResult = list(args.fetchall())
                            for i in fullResult:
                                addToFound(i, 100)
                        args = c.execute('SELECT Url, Date, Content FROM posts;')
                        for hashed in args.fetchall():
                            if hashed[0] not in result:
                                hashedReadable = hashed[2]
                                if isInt(hashedReadable):
                                    hashedDifference = dhash.get_num_bits_different(imgHash, int(hashedReadable))
                                    if hashedDifference < config.threshold:
                                        addToFound(hashed, ((config.threshold - hashedDifference)/config.threshold)*100) 

    for i in result:
        if i != '' and i != 'delete':
            if reddit.submission(url = 'https://reddit.com' + i).selftext == '[deleted]':
                c.execute('DELETE FROM Posts WHERE Url = ?;', (str(i),))
                postsToRemove.append([i, originalPostDate[cntr], precentageMatched[cntr]])
                print('deleted ' + i)
        cntr += 1
            
    for i in postsToRemove:
        result.remove(i[0])
        originalPostDate.remove(i[1])
        precentageMatched.remove(i[2])
    
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
        returnResult.append([i, finalTimePassed[cntr], originalPostDate[cntr], precentageMatched[cntr]])
        cntr += 1
    print('Found? {}'.format(returnResult))

    return returnResult
    
def addPost(conn, date, postContentUrl, postMedia, postUrl, postText):
    c = conn.cursor()
    if postText != '':
        content = hashText(postText)
    else:
        if postMedia != None:
            content = hashVid(postMedia['reddit_video']['fallback_url'])
        elif 'png' in postContentUrl or 'jpg' in postContentUrl or 'gif' in postContentUrl:
            imgHash = hashImg(postContentUrl)
            if isInt(imgHash):
                content = imgHash
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
