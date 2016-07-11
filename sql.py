# -*- coding: utf-8 -*-
import sqlite3
import time
ISOTIMEFORMAT='%Y-%m-%d %X'

class SqlErr(Exception):
    pass
class SelectErr(SqlErr):
    pass

def init():
    import ini
    def iniGet(tag):
        return ini.Config('conf.ini').get('sql', tag)
    global _db
    _db = iniGet('db')

init()#初始化

def getUserCode(stuId):
    conn = sqlite3.connect(_db)
    try:
        a = conn.execute("SELECT userCode FROM userCodes WHERE stuId = '%s'" % (stuId))
        for line in a:
            return(line[0])
    except:
        conn.close()
        return 'SelectErr'
    conn.close()

def getUserCodeFromWxId(wxId):
    conn = sqlite3.connect(_db)
    try:
        a = conn.execute("SELECT userCode FROM binds WHERE wxID = '%s'" % (wxId))
        for line in a:
            return (line[0])
    except:
        conn.close()
        return 'SelectErr'
    conn.close()

def getwxIDListFromUserCode(userCode):
    conn = sqlite3.connect(_db)
    try:
        a = conn.execute("SELECT wxID FROM binds WHERE userCode = '%s'" % (userCode))
        list = []
        for line in a:
            list.append(line[0])
        conn.close()
        return list
    except:
        conn.close()
        return 'SelectErr'

def bind(wxId, stuId):
    userCode = getUserCode(stuId)
    conn = sqlite3.connect(_db)
    try:
        # 微信ID唯一 所以一个微信号只能绑定一个学号
        conn.execute("INSERT INTO binds (wxID, userCode, data) VALUES ('%s', '%s', '%s')" % (wxId, userCode, time.strftime(ISOTIMEFORMAT, time.localtime(time.time()))))
        conn.commit()
    except:
        conn.rollback()
        if conn.execute("SELECT * FROM binds WHERE wxID = '%s'" % (wxId)):
            return '你好像已经绑定了～请直接发送‘查询’查询成绩～'
        return '绑定失败'
    conn.close()
    return '绑定成功!\n请您及时修改教务系统密码'


def bindmail(wxID, stuEmail):
    conn = sqlite3.connect(_db)
    userCode = getUserCodeFromWxId(wxID)
    if userCode == None:
        return 'Error 请先绑定学号！'

    try:# 根据信息添加记录
        conn.execute("INSERT INTO mail (wxID, userCode, email, data) VALUES ('%s', '%s', '%s', '%s')" % (
            wxID, userCode, stuEmail, time.strftime(ISOTIMEFORMAT, time.localtime(time.time()))))
        conn.commit()
    except sqlite3.IntegrityError:# 重复 更新
        conn.execute("UPDATE mail SET email = '%s' ,data = '%s' WHERE wxID = '%s'" % (
            stuEmail, time.strftime(ISOTIMEFORMAT, time.localtime(time.time())), wxID))
        conn.commit()
        return "OK 绑定邮箱更新为"+stuEmail
    except sqlite3.OperationalError:# 没库 建立新表|为兼容线上没有新表的服务器
        conn.execute("CREATE TABLE mail(wxID TEXT,email TEXT,userCode TEXT,data TEXT);")
        conn.execute("CREATE UNIQUE INDEX mail_wxID_uindex ON mail (wxID);")
        try:
            conn.commit()
        except:
            conn.rollback()

        conn.commit()
        return 'Error 服务器蜜汁错误！请重试！'
    conn.close()
    return 'OK 绑定成功！'

if __name__ == "__main__":
    print(bindmail('121', "1913142145@qq.com"))
    print(getUserCode('4140206140'))
    print('sqltest start SUCCESS!')