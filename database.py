# packages that come with python
from datetime import timedelta, datetime
from calendar import monthrange
from urllib.request import Request, urlopen
from io import BytesIO
import ssl
import sqlite3
from re import sub
import traceback

# packages that need to be pip installed
import praw
from PIL import Image
import dhash
from Levenshtein import distance
import av

context = ssl._create_unverified_context()
user_agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 5_0 like Mac OS X) AppleWebKit/534.46'

def initDatabase(subreddit):
    conn = sqlite3.connect(
            'Posts{}.db'.format(
                sub(
                    '([a-zA-Z])',
                    lambda x: x.groups()[0].upper(),
                    subreddit,
                    1,
                    )
                )
            )
    c = conn.cursor()
    c.execute(
        'CREATE TABLE IF NOT EXISTS Posts (Date INT, Content TEXT, Url TEXT, Location TEXT, Author TEXT, Title TEXT);',
    )
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


def hashImg(conn, imgUrl, url):
    imgHash = 'invalid'
    try:
        f = BytesIO(
            urlopen(
                Request(
                    str(imgUrl),
                    headers={
                        'User-Agent': user_agent
                    },
                ),
                context=context,
            ).read(),
        )
        img = Image.open(f)
        imgHash = dhash.dhash_int(img)
    except:
        f = open('dedLink.txt', 'a')
        f.write('{}\n{}\n'.format(str(traceback.format_exc()), url))
        c = conn.cursor()
        c.execute(
            'DELETE FROM Posts WHERE Url = ?;',
            (
                str(url),
            ),
        )
        conn.commit()
        c.close()
    return imgHash

def hashVid(conn, vidUrl, url):
    vidHash = ''
    try:
        container = av.open(vidUrl['reddit_video']['fallback_url'])
        for frame in container.decode(video=0):
            vidHash = '{}{} '.format(vidHash, str(dhash.dhash_int(frame.to_image())))
    except:
        f = open('dedLink.txt', 'a')
        f.write('{}\n{}\n'.format(str(traceback.format_exc()), vidUrl))
        c = conn.cursor()
        c.execute(
            'DELETE FROM Posts WHERE Url = ?;',
            (
                str(url),
            ),
        )
        conn.commit()
        c.close()
        vidHash = 'invalid'
    return vidHash


def hashGif(conn, gifUrl, url):
    gifHash = ''
    nframes = 0
    try:
        f = BytesIO(
                urlopen(
                    Request(
                        str(gifUrl),
                        headers={'User-Agent': user_agent},
                    ),
                    context=context,
                ).read(),
            )
        frame = Image.open(f)
        while frame:
            dhash.dhash_int(frame)
            gifHash = '{}{} '.format(gifHash, str(dhash.dhash_int(frame)))
            nframes += 1
            try:
                frame.seek(nframes)
            except EOFError:
                break
    except:
        f = open('dedLink.txt', 'a')
        f.write('{}\n{}\n'.format(str(traceback.format_exc()), url))
        c = conn.cursor()
        c.execute(
            'DELETE FROM Posts WHERE Url = ?;',
            (
                str(url),
            ),
        )
        conn.commit()
        c.close()
        gifHash = 'invalid'
    return gifHash


def hashVidDifference(originalHash, newHash):
    cntr = 0
    originalHashList = originalHash.split()
    newHashList = newHash.split()
    frameDifferences = []
    minDifferences = []
    for i in originalHashList:
        for j in newHashList:
            frameDifferences.append(dhash.get_num_bits_different(int(i), int(j)))
            cntr += 1
        minDifferences.append(min(frameDifferences))
        frameDifferences = []
    print(sum(minDifferences)/len(minDifferences))
    return sum(minDifferences)/len(minDifferences)

def addToFound(post, precentage, result, originalPostDate, precentageMatched, author, title):
    result.append(post[0])
    originalPostDate.append(post[1])
    author.append(post[2])
    title.append(post[3])
    precentageMatched.append(precentage)

def updateDatabase(conn, url, updateVal):
    c = conn.cursor()
    c.execute(
        'UPDATE Posts SET Location = ? WHERE Url = ?;',
        (
            str(updateVal),
            str(url),
        ),
    )
    conn.commit()
    c.close()

def deleteOldFromDatabase(subSettings):
    conn = sqlite3.connect(
            'Posts{}.db'.format(
                sub(
                    '([a-zA-Z])',
                    lambda x: x.groups()[0].upper(),
                    subSettings[0],
                    1,
                    )
                )
            )
    c = conn.cursor()
    while True:
        args = c.execute(
            'SELECT Date, Location FROM Posts;'
        )
        now = datetime.utcnow()
        for x in args.fetchall():
            then = datetime.fromtimestamp(x[0])
            timePassed = (now-then).days
            if subSettings[1] is not None and timePassed > subSettings[1] and x[1] == 'top' or subSettings[2] is not None and timePassed > subSettings[2] and x[1] == 'hot' or subSettings[3] is not None and timePassed > subSettings[3] and x[1] == 'new':
                c.execute(
                    'DELETE FROM Posts WHERE Date = ?;',
                    (
                        int(x[0]),
                    ),
                )
                conn.commit()
                print('deleted an old post')
    c.close()


def isLogged(contentUrl, media, text, url, date, top, hot, new, subSettings, reddit):
    result = []
    originalPostDate = []
    finalTimePassed = []
    precentageMatched = []
    author = []
    title = []
    args = None
    postsToRemove = []
    cntr = 0
    returnResult = []

    conn = sqlite3.connect(
            'Posts{}.db'.format(
                sub(
                    '([a-zA-Z])',
                    lambda x: x.groups()[0].upper(),
                    subSettings[0],
                    1,
                )
            )
        )
    c = conn.cursor()

    now = datetime.utcnow()
    then = datetime.fromtimestamp(date)
    timePassed = (now-then).days

    # ignore post if too old
    if subSettings[1] is not None and timePassed > subSettings[1] and top or subSettings[2] is not None and timePassed > subSettings[2] and hot or subSettings[3] is not None and timePassed > subSettings[3] and new:
        result = ['delete']
        originalPostDate = [-1]
        finalTimePassed = [-1]
        precentageMatched = [-1]
        author = [-1]
        title = [-1]
    
    else:

        # check if post is already in database
        args = c.execute(
            'SELECT COUNT(1) FROM Posts WHERE Url = ?;',
            (
                str(url),
            ),
        )
        if list(args.fetchone())[0] != 0:
            args = c.execute(
                'SELECT Location FROM Posts WHERE Url = ?;',
                (
                    str(url),
                ),
            )
            fullResult = list(args.fetchall())

            # make sure the post is in the right category
            for i in fullResult:
                if i[0] != 'top' and top and (subSettings[1] is None or (timePassed < subSettings[1] and (subSettings[2] is None or subSettings[1] > subSettings[2]) and (subSettings[3] is None or subSettings[1] > subSettings[3]))):
                        updateDatabase(conn, url, 'top')
                if i[0] != 'hot' and hot and (subSettings[2] is None or (timePassed < subSettings[2] and (subSettings[1] is None or subSettings[2] > subSettings[1]) and (subSettings[3] is None or subSettings[2] > subSettings[3]))):
                        updateDatabase(conn, url, 'hot')
                if i[0] != 'new' and new and (subSettings[3] is None or (timePassed < subSettings[3] and (subSettings[2] is None or subSettings[3] > subSettings[2]) and (subSettings[1] is None or subSettings[3] > subSettings[1]))):
                        updateDatabase(conn, url, 'new')

            # ignore post
            result = ['delete']
            originalPostDate = [-1]
            finalTimePassed = [-1]
            precentageMatched = [-1]
            author = [-1]
            title = [-1]
        
        # check if post is a repost
        else:

            # check for text
            if text != '&#x200B;' and text != '':
                args = c.execute(
                    'SELECT COUNT(1) FROM Posts WHERE Content = ?;',
                    (
                        str(text),
                    ),
                )
                if list(args.fetchone())[0] != 0:
                    args = c.execute(
                        'SELECT Url, Date, Author, Title FROM Posts WHERE Content = ?;',
                        (
                            str(text),
                        ),
                    )
                    fullResult = list(args.fetchall())
                    for i in fullResult:
                        addToFound(
                            i,
                            100,
                            result,
                            originalPostDate,
                            precentageMatched,
                            author,
                            title,
                        )
                    args = c.execute(
                        'SELECT Url, Date, Author, Title, Content FROM posts;',
                    )
                    for texts in args.fetchall():
                        if texts[0] not in result:
                            textVar = texts[2]
                            difference = distance(textVar, text)
                            if difference < subSettings[7]:
                                addToFound(
                                    texts,
                                    ((subSettings[7] - difference)/subSettings[7])*100,
                                    result,
                                    originalPostDate,
                                    precentageMatched,
                                    author,
                                    title,
                                )
            
            # check for v.reddit
            if 'provider_name' != None:
                print('provider_name' in media)
            elif media != None and ('provider_name' not in media or media['provider_name'] != 'gfycat'):
                vidHash = hashVid(conn, media, url)
                if vidHash == 'invalid':
                    result = ['delete']
                    originalPostDate = [-1]
                    finalTimePassed = [-1]
                    precentageMatched = [-1]
                    author = [-1]
                    title = [-1]
                if isInt(vidHash.replace(' ', '')):
                    args = c.execute(
                        'SELECT COUNT(1) FROM Posts WHERE Content = ?;',
                        (
                            str(vidHash),
                        ),
                    )
                    if list(args.fetchone())[0] != 0:
                        args = c.execute(
                            'SELECT Url, Date, Author, Title FROM Posts WHERE Content = ?;',
                            (
                                str(vidHash),
                            ),
                        )
                        fullResult = list(args.fetchall())
                        for i in fullResult:
                            addToFound(
                                i,
                                100,
                                result,
                                originalPostDate,
                                precentageMatched,
                                author,
                                title
                            )
                    args = c.execute(
                        'SELECT Url, Date, Author, Title Content FROM posts;',
                    )
                    for hashed in args.fetchall():
                        if hashed[0] not in result:
                            hashedReadable = hashed[2]
                            if isInt(hashedReadable.replace(' ', '')):
                                hashedDifference = hashVidDifference(
                                    hashedReadable, vidHash)
                                if hashedDifference < subSettings[7]:
                                    addToFound(
                                        hashed,
                                        ((subSettings[7] - hashedDifference)/subSettings[7])*100,
                                        result,
                                        originalPostDate,
                                        precentageMatched,
                                        author,
                                        title,
                                    )

            # check for image or gif
            elif contentUrl != '':
                args = c.execute(
                    'SELECT COUNT(1) FROM Posts WHERE Content = ?;',
                    (
                        str(contentUrl).replace(
                            '&feature=youtu.be',
                            '',
                        ),
                    ),
                )
                if list(args.fetchone())[0] != 0:
                    args = c.execute(
                        'SELECT Url, Date, Author, Title FROM Posts WHERE Content = ?;',
                        (
                            str(contentUrl).replace(
                                '&feature=youtu.be',
                                '',
                            ),
                        ),
                    )
                    fullResult = list(args.fetchall())
                    for i in fullResult:
                        addToFound(
                            i,
                            100,
                            result,
                            originalPostDate,
                            precentageMatched,
                            author,
                            title,
                        )

                # check for gif
                if 'gif' in contentUrl and not (contentUrl.endswith('gifv') or 'gifs' in contentUrl):
                    gifHash = hashGif(conn, contentUrl, url)
                    if gifHash == 'invalid':
                        result = ['delete']
                        originalPostDate = [-1]
                        finalTimePassed = [-1]
                        precentageMatched = [-1]
                        author = [-1]
                        title = [-1]
                    if isInt(gifHash.replace(' ', '')):
                        args = c.execute(
                            'SELECT COUNT(1) FROM Posts WHERE Content = ?;',
                            (
                                str(gifHash),
                            ),
                        )
                        if list(args.fetchone())[0] != 0:
                            args = c.execute(
                                'SELECT Url, Date, Author, Title FROM Posts WHERE Content = ?;',
                                (
                                    str(gifHash),
                                ),
                            )
                            fullResult = list(args.fetchall())
                            for i in fullResult:
                                addToFound(
                                    i,
                                    100,
                                    result,
                                    originalPostDate,
                                    precentageMatched,
                                    author,
                                    title,
                                )
                        args = c.execute(
                            'SELECT Url, Date, Author, Title, Content FROM posts;'
                        )
                        for hashed in args.fetchall():
                            if hashed[0] not in result:
                                hashedReadable = hashed[2]
                                if isInt(hashedReadable.replace(' ', '')):
                                    hashedDifference = hashVidDifference(
                                        hashedReadable, gifHash)
                                    if hashedDifference < subSettings[7]:
                                        addToFound(
                                            hashed,
                                            ((subSettings[7] - hashedDifference)/subSettings[7])*100,
                                            result,
                                            originalPostDate,
                                            precentageMatched,
                                            author,
                                            title,
                                        )
                elif 'png' in contentUrl or 'jpg' in contentUrl:
                    imgHash = hashImg(conn, contentUrl, url)
                    if imgHash == 'invalid':
                        result = ['delete']
                        originalPostDate = [-1]
                        finalTimePassed = [-1]
                        precentageMatched = [-1]
                        author = [-1]
                        title = [-1]
                    if isInt(imgHash):
                        args = c.execute(
                            'SELECT COUNT(1) FROM Posts WHERE Content = ?;',
                            (
                                str(imgHash),
                            ),
                        )
                        if list(args.fetchone())[0] != 0:
                            args = c.execute(
                                'SELECT Url, Date, Author, Title FROM Posts WHERE Content = ?;',
                                (
                                    str(imgHash),
                                ),
                            )
                            fullResult = list(args.fetchall())
                            for i in fullResult:
                                addToFound(
                                    i,
                                    100,
                                    result,
                                    originalPostDate,
                                    precentageMatched,
                                    author,
                                    title,
                                )
                        args = c.execute(
                            'SELECT Url, Date, Author, Title, Content FROM posts;'
                        )
                        for hashed in args.fetchall():
                            if hashed[0] not in result:
                                hashedReadable = hashed[2]
                                if isInt(hashedReadable):
                                    hashedDifference = dhash.get_num_bits_different(
                                        imgHash, int(hashedReadable))
                                    if hashedDifference < subSettings[7]:
                                        addToFound(
                                            hashed,
                                            ((subSettings[7] - hashedDifference)/subSettings[7])*100,
                                            result,
                                            originalPostDate,
                                            precentageMatched,
                                            author,
                                            title,
                                        )

    # delete post if it has been deleted
    for i in result:
        if i != '' and i != 'delete':
            if reddit.submission(url='https://reddit.com{}'.format(i)).selftext == '[deleted]':
                c.execute(
                    'DELETE FROM Posts WHERE Url = ?;',
                    (
                        str(i),
                    ),
                )
                postsToRemove.append([
                    i,
                    originalPostDate[cntr],
                    precentageMatched[cntr],
                    author[cntr],
                    title[cntr],
                ])
                print('deleted {}'.format(i))
        cntr += 1

    c.close()

    for i in postsToRemove:
        result.remove(i[0])
        originalPostDate.remove(i[1])
        precentageMatched.remove(i[2])
        author.remove(i[3])
        title.remove(i[4])

    for i in originalPostDate:
        then = datetime.fromtimestamp(i)
        timePassed = monthDelta(then, now)
        fullText = ('{} months ago'.format(str(timePassed)))
        if timePassed < 1:
            timePassed = (now-then).days
            fullText = ('{} days ago'.format(str(timePassed)))
        if timePassed < 1:
            timePassed = (now-then).total_seconds()//3600
            fullText = ('{} hours ago'.format(str(timePassed)))
        if timePassed < 1:
            timePassed = (now-then).total_seconds()//60
            fullText = ('{} minutes ago'.format(str(timePassed)))
        if timePassed < 1:
            timePassed = (now-then).total_seconds()
            fullText = ('{} seconds ago'.format(str(timePassed)))
        finalTimePassed.append(fullText)
    
    cntr = 0
    for i in result:
        returnResult.append([
            i,
            finalTimePassed[cntr],
            originalPostDate[cntr],
            precentageMatched[cntr],
            author[cntr],
            title[cntr],
        ])
        cntr += 1
    
    if returnResult != [['delete', -1, -1, -1, -1, -1]]:
        print('Found? {}'.format(returnResult))

    return returnResult


def addPost(date, contentUrl, media, url, text, author, title, top, hot, new, subreddit):
    conn = sqlite3.connect(
            'Posts{}.db'.format(
                sub(
                    '([a-zA-Z])',
                    lambda x: x.groups()[0].upper(),
                    subreddit,
                    1,
                )
            )
        )
    c = conn.cursor()
    if text != '&#x200B;' and text != '':
        content = text
    else:
        if media != None:
            vidHash = hashVid(conn, media, url)
            if isInt(vidHash.replace(' ', '')):
                content = vidHash
            else:
                content = contentUrl
        elif 'gif' in contentUrl and not (contentUrl.endswith('gifv') or 'gifs' in contentUrl):
            gifHash = hashGif(conn, contentUrl, url)
            if isInt(gifHash.replace(' ', '')):
                content = gifHash
            else:
                content = contentUrl
        elif 'png' in contentUrl or 'jpg' in contentUrl:
            imgHash = hashImg(conn, contentUrl, url)
            if isInt(imgHash):
                content = imgHash
            else:
                content = contentUrl
        else:
            content = contentUrl
    if top:
        locationVar = 'top'
    elif hot:
        locationVar = 'hot'
    elif new:
        locationVar = 'new'
    c.execute(
        'INSERT INTO Posts (Date, Content, Url, Location, Author, Title) VALUES (?, ?, ?, ?, ?, ?);',
            (
                int(date),
                str(content),
                str(url),
                str(locationVar),
                str(author),
                str(title),
            ),
        )
    conn.commit()
    c.close()
    print('Added new post - {}'.format(str(url)))
