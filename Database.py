import sqlite3

def initDatabase(conn):
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS Posts (Date INT, Content TEXT, Title TEXT, State INTEGER DEFAULT 1);")
    conn.commit()
    c.close()
    print("Create table.")
    
def isLogged(conn, postUrl, postText):
    c = conn.cursor()
    if postText != "":
        args = c.execute("SELECT COUNT(1) FROM Posts WHERE Content = ?;", (str(postText),))
    elif postUrl != "":
        args = c.execute("SELECT COUNT(1) FROM Posts WHERE Content = ?;", (str(postUrl),))
    result = list(args.fetchone())[0]
    c.close()
    print("Found? {}".format(result))
    return result

def addUser(conn, title, date, postUrl, postText):
    c = conn.cursor()
    if postText != "":
        c.execute("INSERT INTO Posts (Date, Content) VALUES (?, ?);", (str(date), str(postText),))
    elif postUrl != "":
        c.execute("INSERT INTO Posts (Date, Content) VALUES (?, ?);", (str(date), str(postUrl),))
    conn.commit()
    c.close()
    print("Added new post - {}".format(str(date)))

def getAll(conn):
    c = conn.cursor()
    args = c.execute("SELECT Content FROM posts;")
    result = [x[0] for x in args.fetchall()]
    c.close()
    return result