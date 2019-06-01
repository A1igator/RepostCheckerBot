# packages that come with python
from datetime import timedelta, datetime
from calendar import monthrange
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from io import BytesIO
import ssl
import sqlite3
from re import sub
import traceback

# packages that need to be pip installed
from PIL import Image
import dhash
from difflib import SequenceMatcher
from pytesseract import image_to_string
import av

from setInterval import setInterval

context = ssl._create_unverified_context()
user_agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 5_0 like Mac OS X) AppleWebKit/534.46'


def init_database(subreddit, is_text_in_image):
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
        'CREATE TABLE IF NOT EXISTS Posts (Date INT, Content TEXT, ImageText TEXT, Url TEXT, Location TEXT, Author TEXT, Title TEXT);',
    )
    conn.commit()
    c.close()
    print('Create table.')


def canonical(s):
    return ''.join([c for c in s if not c.isspace()])


def is_int(s):
    try:
        int(s)
        return True
    except:
        return False



def month_delta(d1, d2):
    delta = 0
    while True:
        mdays = monthrange(d1.year, d1.month)[1]
        d1 += timedelta(days=mdays)
        if d1 <= d2:
            delta += 1
        else:
            break
    return delta


def hash_img(conn, img_url, url):
    img_hash = 'invalid'
    try:
        f = BytesIO(
            urlopen(
                Request(
                    str(img_url),
                    headers={
                        'User-Agent': user_agent
                    },
                ),
                context=context,
            ).read(),
        )
        img = Image.open(f)
        img_hash = dhash.dhash_int(img)
    except HTTPError:
        c = conn.cursor()
        c.execute(
            'DELETE FROM Posts WHERE Url = ?;',
            (
                str(url),
            ),
        )
        conn.commit()
        c.close()
    except:
        f = open('dedLink.txt', 'a')
        f.write('{}\n{}\n'.format(str(traceback.format_exc()), img_url))
        c = conn.cursor()
        c.execute(
            'DELETE FROM Posts WHERE Url = ?;',
            (
                str(url),
            ),
        )
        conn.commit()
        c.close()
    return img_hash


def extract_text(img_url, url):
    img_text = 'invalid'
    try:
        f = BytesIO(
            urlopen(
                Request(
                    str(img_url),
                    headers={
                        'User-Agent': user_agent
                    },
                ),
                context=context,
            ).read(),
        )
        img = Image.open(f)
        img_text = image_to_string(img).replace('\n', '').replace('\r', '').replace(' ', '')
    except Exception as e:
        if e.__class__.__name__ != 'HTTPError':
            f = open('tesseractErrs.txt', 'a')
            f.write('{}\n{}\n'.format(str(traceback.format_exc()), img_url))
    return img_text


def hash_vid(conn, vid_url, url):
    vid_hash = ''
    try:
        container = av.open(vid_url['reddit_video']['fallback_url'])
        for frame in container.decode(video=0):
            vid_hash = '{}{} '.format(vid_hash, str(dhash.dhash_int(frame.to_image())))
    except Exception as e:
        if '403' in str(e):
            c = conn.cursor()
            c.execute(
                'DELETE FROM Posts WHERE Url = ?;',
                (
                    str(url),
                ),
            )
            conn.commit()
            c.close()
        else:
            f = open('dedLink.txt', 'a')
            f.write('{}\n{}\n'.format(str(traceback.format_exc()), vid_url))
            c = conn.cursor()
            c.execute(
                'DELETE FROM Posts WHERE Url = ?;',
                (
                    str(url),
                ),
            )
            conn.commit()
            c.close()
        vid_hash = 'invalid'
    return vid_hash


def hash_gif(conn, gif_url, url):
    gif_hash = ''
    nframes = 0
    try:
        f = BytesIO(
                urlopen(
                    Request(
                        str(gif_url),
                        headers={'User-Agent': user_agent},
                    ),
                    context=context,
                ).read(),
            )
        frame = Image.open(f)
        while frame:
            dhash.dhash_int(frame)
            gif_hash = '{}{} '.format(gif_hash, str(dhash.dhash_int(frame)))
            nframes += 1
            try:
                frame.seek(nframes)
            except EOFError:
                break
    except HTTPError:
        c = conn.cursor()
        c.execute(
            'DELETE FROM Posts WHERE Url = ?;',
            (
                str(url),
            ),
        )
        conn.commit()
        c.close()
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
        gif_hash = 'invalid'
    return gif_hash


def hash_vid_difference(original_hash, new_hash):
    cntr = 0
    original_hash_list = original_hash.split()
    new_hash_list = new_hash.split()
    frame_differences = []
    min_differences = []
    for i in original_hash_list:
        for j in new_hash_list:
            frame_differences.append(dhash.get_num_bits_different(int(i), int(j)))
            cntr += 1
        min_differences.append(min(frame_differences))
        frame_differences = []
    return sum(min_differences)/len(min_differences)


def add_to_found(post, precentage, result, original_post_date, precentage_matched, author, title):
    result.append(post[0])
    original_post_date.append(post[1])
    author.append(post[2])
    title.append(post[3])
    precentage_matched.append(precentage)


def update_database(conn, url, update_val):
    c = conn.cursor()
    c.execute(
        'UPDATE Posts SET Location = ? WHERE Url = ?;',
        (
            str(update_val),
            str(url),
        ),
    )
    conn.commit()
    c.close()


def delete_old_from_database(sub_settings, s):
    conn = sqlite3.connect(
            'Posts{}.db'.format(
                sub(
                    '([a-zA-Z])',
                    lambda x: x.groups()[0].upper(),
                    sub_settings[0],
                    1,
                    )
                )
            )
    c = conn.cursor()
    delete_old_loop(sub_settings, c, conn)

@setInterval(5)
def delete_old_loop(sub_settings, c, conn):
    args = c.execute(
        'SELECT Date, Location FROM Posts;'
    )
    now = datetime.utcnow()
    for x in args.fetchall():
        then = datetime.fromtimestamp(x[0])
        time_passed = (now - then).days
        if sub_settings[1] is not None and time_passed > sub_settings[1] and x[1] == 'top' or sub_settings[
            2] is not None and time_passed > sub_settings[2] and x[1] == 'hot' or sub_settings[
            3] is not None and time_passed > sub_settings[3] and x[1] == 'new':
            c.execute(
                'DELETE FROM Posts WHERE Date = ?;',
                (
                    int(x[0]),
                ),
            )
            conn.commit()
            print('deleted an old post')


def is_logged(content_url, media, text, url, date, top, hot, new, sub_settings, reddit):
    result = []
    original_post_date = []
    final_time_passed = []
    percentage_matched = []
    author = []
    title = []
    args = None
    posts_to_remove = []
    cntr = 0
    return_result = []

    conn = sqlite3.connect(
            'Posts{}.db'.format(
                sub(
                    '([a-zA-Z])',
                    lambda x: x.groups()[0].upper(),
                    sub_settings[0],
                    1,
                )
            )
        )
    c = conn.cursor()

    now = datetime.utcnow()
    then = datetime.fromtimestamp(date)
    time_passed = (now-then).days

    # ignore post if too old
    if sub_settings[1] is not None and time_passed > sub_settings[1] and top or sub_settings[2] is not None and time_passed > sub_settings[2] and hot or sub_settings[3] is not None and time_passed > sub_settings[3] and new:
        result = ['delete']
        original_post_date = [-1]
        final_time_passed = [-1]
        percentage_matched = [-1]
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
            full_result = list(args.fetchall())

            # make sure the post is in the right category
            for i in full_result:
                if i[0] != 'top' and top and (sub_settings[1] is None or (time_passed < sub_settings[1] and (sub_settings[2] is None or sub_settings[1] > sub_settings[2]) and (sub_settings[3] is None or sub_settings[1] > sub_settings[3]))):
                    update_database(conn, url, 'top')
                if i[0] != 'hot' and hot and (sub_settings[2] is None or (time_passed < sub_settings[2] and (sub_settings[1] is None or sub_settings[2] > sub_settings[1]) and (sub_settings[3] is None or sub_settings[2] > sub_settings[3]))):
                    update_database(conn, url, 'hot')
                if i[0] != 'new' and new and (sub_settings[3] is None or (time_passed < sub_settings[3] and (sub_settings[2] is None or sub_settings[3] > sub_settings[2]) and (sub_settings[1] is None or sub_settings[3] > sub_settings[1]))):
                    update_database(conn, url, 'new')

            # ignore post
            result = ['delete']
            original_post_date = [-1]
            final_time_passed = [-1]
            percentage_matched = [-1]
            author = [-1]
            title = [-1]

        # check if post is a repost
        else:

            # check for text
            if text != '&#x200B;' and text != '' and text != '[removed]' and text != '[deleted]':
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
                    full_result = list(args.fetchall())
                    for i in full_result:
                        add_to_found(
                            i,
                            100,
                            result,
                            original_post_date,
                            percentage_matched,
                            author,
                            title,
                        )
                    args = c.execute(
                        'SELECT Url, Date, Author, Title, Content FROM posts;',
                    )
                    for texts in args.fetchall():
                        if texts[0] not in result:
                            text_var = texts[4]
                            difference = SequenceMatcher(None, text_var, text).ratio()
                            if 10 - (difference * 10) < sub_settings[7]:
                                add_to_found(
                                    texts,
                                    difference * 100,
                                    result,
                                    original_post_date,
                                    percentage_matched,
                                    author,
                                    title,
                                )

            # check for v.reddit
            elif media is not None and ('oembed' not in media or 'provider_name' not in media['oembed'] or (media['oembed']['provider_name'] != 'gfycat' and media['oembed']['provider_name'] != 'YouTube' and media['oembed']['provider_name'] != 'Imgur')):
                vid_hash = hash_vid(conn, media, url)
                if vid_hash == 'invalid':
                    result = ['delete']
                    original_post_date = [-1]
                    final_time_passed = [-1]
                    percentage_matched = [-1]
                    author = [-1]
                    title = [-1]
                if is_int(vid_hash.replace(' ', '')):
                    args = c.execute(
                        'SELECT COUNT(1) FROM Posts WHERE Content = ?;',
                        (
                            str(vid_hash),
                        ),
                    )
                    if list(args.fetchone())[0] != 0:
                        args = c.execute(
                            'SELECT Url, Date, Author, Title FROM Posts WHERE Content = ?;',
                            (
                                str(vid_hash),
                            ),g
                        )
                        full_result = list(args.fetchall())
                        for i in full_result:
                            add_to_found(
                                i,
                                100,
                                result,
                                original_post_date,
                                percentage_matched,
                                author,
                                title
                            )
                    args = c.execute(
                        'SELECT Url, Date, Author, Title Content FROM posts;',
                    )
                    for hashed in args.fetchall():
                        if hashed[0] not in result:
                            hashed_readable = hashed[2]
                            if is_int(hashed_readable.replace(' ', '')):
                                hashed_difference = hash_vid_difference(
                                    hashed_readable, vid_hash)
                                if hashed_difference < sub_settings[7]:
                                    add_to_found(
                                        hashed,
                                        ((sub_settings[7] - hashed_difference)/sub_settings[7])*100,
                                        result,
                                        original_post_date,
                                        percentage_matched,
                                        author,
                                        title,
                                    )

            # check for image or gif
            elif content_url != '':
                args = c.execute(
                    'SELECT COUNT(1) FROM Posts WHERE Content = ?;',
                    (
                        str(content_url).replace(
                            '&feature=youtu.be',
                            '',
                        ),
                    ),
                )
                if list(args.fetchone())[0] != 0:
                    args = c.execute(
                        'SELECT Url, Date, Author, Title FROM Posts WHERE Content = ?;',
                        (
                            str(content_url).replace(
                                '&feature=youtu.be',
                                '',
                            ),
                        ),
                    )
                    full_result = list(args.fetchall())
                    for i in full_result:
                        add_to_found(
                            i,
                            100,
                            result,
                            original_post_date,
                            percentage_matched,
                            author,
                            title,
                        )

                # check for gif
                if 'gif' in content_url and not (content_url.endswith('gifv') or 'gifs' in content_url):
                    gifHash = hash_gif(conn, content_url, url)
                    if gifHash == 'invalid':
                        result = ['delete']
                        original_post_date = [-1]
                        final_time_passed = [-1]
                        percentage_matched = [-1]
                        author = [-1]
                        title = [-1]
                    if is_int(gifHash.replace(' ', '')):
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
                            full_result = list(args.fetchall())
                            for i in full_result:
                                add_to_found(
                                    i,
                                    100,
                                    result,
                                    original_post_date,
                                    percentage_matched,
                                    author,
                                    title,
                                )
                        args = c.execute(
                            'SELECT Url, Date, Author, Title, Content FROM posts;'
                        )
                        for hashed in args.fetchall():
                            if hashed[0] not in result:
                                hashed_readable = hashed[2]
                                if is_int(hashed_readable.replace(' ', '')):
                                    hashed_difference = hash_vid_difference(
                                        hashed_readable, gifHash)
                                    if hashed_difference < sub_settings[7]:
                                        add_to_found(
                                            hashed,
                                            ((sub_settings[7] - hashed_difference)/sub_settings[7])*100,
                                            result,
                                            original_post_date,
                                            percentage_matched,
                                            author,
                                            title,
                                        )

                # check for image
                elif 'png' in content_url or 'jpg' in content_url:
                    imgHash = hash_img(conn, content_url, url)
                    if imgHash == 'invalid':
                        result = ['delete']
                        original_post_date = [-1]
                        final_time_passed = [-1]
                        percentage_matched = [-1]
                        author = [-1]
                        title = [-1]
                    elif is_int(imgHash):
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
                            full_result = list(args.fetchall())
                            for i in full_result:
                                add_to_found(
                                    i,
                                    100,
                                    result,
                                    original_post_date,
                                    percentage_matched,
                                    author,
                                    title,
                                )
                        args = c.execute(
                            'SELECT Url, Date, Author, Title, Content FROM posts;'
                        )
                        for hashed in args.fetchall():
                            if hashed[0] not in result:
                                hashed_readable = hashed[2]
                                if is_int(hashed_readable):
                                    hashed_difference = dhash.get_num_bits_different(
                                        imgHash, int(hashed_readable))
                                    if hashed_difference < sub_settings[7]:
                                        add_to_found(
                                            hashed,
                                            ((sub_settings[7] - hashed_difference)/sub_settings[7])*100,
                                            result,
                                            original_post_date,
                                            percentage_matched,
                                            author,
                                            title,
                                        )
                    if sub_settings[8]:
                        img_text = extract_text(content_url, url)
                        if img_text != 'invalid' and img_text != '':
                            args = c.execute(
                                'SELECT COUNT(1) FROM Posts WHERE Content = ?;',
                                (
                                    str(img_text),
                                ),
                            )
                            if list(args.fetchone())[0] != 0:
                                args = c.execute(
                                    'SELECT Url, Date, Author, Title FROM Posts WHERE Content = ?;',
                                    (
                                        str(img_text),
                                    ),
                                )
                                full_result = list(args.fetchall())
                                for i in full_result:
                                    add_to_found(
                                        i,
                                        100,
                                        result,
                                        original_post_date,
                                        percentage_matched,
                                        author,
                                        title,
                                    )
                            args = c.execute(
                                'SELECT Url, Date, Author, Title, ImageText FROM posts;'
                            )
                            for texts in args.fetchall():
                                if texts[0] not in result and texts[4] != '':
                                    text_var = texts[4]
                                    difference = SequenceMatcher(None, text_var, img_text).ratio()
                                    if 10 - (difference * 10) < sub_settings[7]:
                                        add_to_found(
                                            texts,
                                            difference * 100,
                                            result,
                                            original_post_date,
                                            percentage_matched,
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
                posts_to_remove.append([
                    i,
                    original_post_date[cntr],
                    percentage_matched[cntr],
                    author[cntr],
                    title[cntr],
                ])
                print('deleted {}'.format(i))
        cntr += 1

    c.close()

    for i in posts_to_remove:
        result.remove(i[0])
        original_post_date.remove(i[1])
        percentage_matched.remove(i[2])
        author.remove(i[3])
        title.remove(i[4])

    for i in original_post_date:
        then = datetime.fromtimestamp(i)
        time_passed = month_delta(then, now)
        full_text = ('{} months ago'.format(str(time_passed)))
        if time_passed < 1:
            time_passed = (now-then).days
            full_text = ('{} days ago'.format(str(time_passed)))
        if time_passed < 1:
            time_passed = (now-then).total_seconds()//3600
            full_text = ('{} hours ago'.format(str(time_passed)))
        if time_passed < 1:
            time_passed = (now-then).total_seconds()//60
            full_text = ('{} minutes ago'.format(str(time_passed)))
        if time_passed < 1:
            time_passed = (now-then).total_seconds()
            full_text = ('{} seconds ago'.format(str(time_passed)))
        final_time_passed.append(full_text)

    cntr = 0
    for i in result:
        return_result.append([
            i,
            final_time_passed[cntr],
            original_post_date[cntr],
            percentage_matched[cntr],
            author[cntr],
            title[cntr],
        ])
        cntr += 1

    if return_result != [['delete', -1, -1, -1, -1, -1]]:
        print('Found? {}'.format(return_result))

    return return_result


def add_post(date, contentUrl, media, url, text, author, title, top, hot, new, subreddit, is_text_in_image):
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
    img_text = ''
    if text != '&#x200B;' and text != '' and text != '[removed]' and text != '[deleted]':
        content = text
    else:
        if media is not None and ('oembed' not in media or 'provider_name' not in media['oembed'] or (media['oembed']['provider_name'] != 'gfycat' and media['oembed']['provider_name'] != 'YouTube' and media['oembed']['provider_name'] != 'Imgur')):
            vidHash = hash_vid(conn, media, url)
            if is_int(vidHash.replace(' ', '')):
                content = vidHash
            else:
                content = contentUrl
        elif 'gif' in contentUrl and not (contentUrl.endswith('gifv') or 'gifs' in contentUrl):
            gif_hash = hash_gif(conn, contentUrl, url)
            if is_int(gif_hash.replace(' ', '')):
                content = gif_hash
            else:
                content = contentUrl
        elif 'png' in contentUrl or 'jpg' in contentUrl:
            img_hash = hash_img(conn, contentUrl, url)
            if is_int(img_hash):
                content = img_hash
            else:
                content = contentUrl
            if is_text_in_image:
                img_text = extract_text(contentUrl, url)
                if img_text == 'invalid':
                    img_text = ''
        else:
            content = contentUrl
    if top:
        location_var = 'top'
    elif hot:
        location_var = 'hot'
    else:
        location_var = 'new'
    c.execute(
        'INSERT INTO Posts (Date, Content, ImageText, Url, Location, Author, Title) VALUES (?, ?, ?, ?, ?, ?, ?);',
        (
                int(date),
                str(content),
                str(img_text),
                str(url),
                str(location_var),
                str(author),
                str(title),
        ),
    )
    conn.commit()
    c.close()
    print('Added new post - {}'.format(str(url)))
    return int(date), str(content), str(url), str(location_var), str(author), str(title)
