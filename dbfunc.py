import sqlite3
from sqlite3.dbapi2 import connect

DB_path = 'testing.db'
databasePATH = "testing.db"
def connect_db(DB_path):
    db  = sqlite3.connect(DB_path)
    return db

def disconnect_db(db):
    db.close()

def insert_user_pwd(db,user,pwd,domain):
    cur = db.cursor()
    last_id_cur = cur.execute('''select max(id) 
                            from login_inf      
                        ''')
    for i in last_id_cur:
        last_id = i[0]
    last_id = last_id + 1
    
    try :
        cur.execute("insert into login_inf Values ('%d','%s','%s','%s')" %(last_id, user, pwd,domain))
        db.commit()
        return True
    except sqlite3.Error:
        return False

def match_user_pwd(db,user,pwd):
    cur = db.cursor()
    tt = cur.execute("select username,password \
                        from login_inf ")
    for i in tt:
        if i[0] == user and i[1] == pwd:
            return True
    return False

def get_domain(db,user):
    cur = db.cursor()
    tt = cur.execute("select domain \
                      from login_inf \
                      where username = '%s'" %user)
    for i in tt:
        return i[0]

if __name__ == '__main__':
    db = connect_db(DB_path)
    #abc = insert_user_pwd(db,'ro3ot','root')
    abc = get_domain(db,'root')
    print(abc)
    disconnect_db(db)