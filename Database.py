import sqlite3
import datetime

def initDatabase(conn):
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS Posts (Date INT, Content TEXT, Url TEXT, State INTEGER DEFAULT 1);")
    conn.commit()
    c.close()
    print("Create table.")
    
def isLogged(conn, postImageUrl, postText, date):
    result = ""
    args = None
    c = conn.cursor()
    if postText != "":
        print(postText)
        args = c.execute("SELECT Url FROM Posts WHERE Content = ?;", (str(postText),))
        result = list(args.fetchone())[0]
    elif postImageUrl != "":
        args = c.execute("SELECT Url FROM Posts WHERE Content = ?;", (str(postImageUrl),))
        result = list(args.fetchone())[0]
    now = int(datetime.datetime.timestamp(datetime.datetime.today()))
    then = int(date)
    delta = now - then
    print(delta)
    if delta>15780000:
        if postUrl != "":
            c.execute("DELETE FROM Posts WHERE Content = ?;", (str(postImageUrl),))
        elif postText != "":
            c.execute("DELETE FROM Posts WHERE Content = ?;", (str(postText),))
        result = ""
    c.close()
    print("Found? {}".format(result))
    return result

def addUser(conn, date, postImageUrl, postUrl, postText):
    c = conn.cursor()
    if postText != "":
        c.execute("INSERT INTO Posts (Date, Content, Url) VALUES (?, ?, ?);", (str(date), str(postText), str(postUrl),))
    elif postImageUrl != "":
        c.execute("INSERT INTO Posts (Date, Content, Url) VALUES (?, ?, ?);", (str(date), str(postImageUrl), str(postUrl),))
    conn.commit()
    c.close()
    print("Added new post - {}".format(str(date)))

def getAll(conn):
    c = conn.cursor()
    args = c.execute("SELECT Content FROM posts;")
    result = [x[0] for x in args.fetchall()]
    c.close()
    return result