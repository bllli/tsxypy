# -*- coding: utf-8 -*-
from sql import getUserCode
from sql import getUserCodeFromWxId
from sql import bind
from sql import bindmail
import sql
from bindable import bandable
from tsxy import webget
from mail import mailToStu
import urllib
import web
urls = (
    '/weix/(.*)', 'hello'
)

app = web.application(urls, globals())

class hello:
    def GET(self, t):
        return 'POST it please.'
    def POST(self, t):
        data = postDatatoDict(web.data())
        # 获取POST中的 do键值对
        try:
            do = data['do']
        except KeyError:
            return 'Stupid Err!'
        # 绑定功能
        if do == 'bind':
            try:
                stuId = data['stu']
            except KeyError:
                return 'Stupid Err!'
            try:
                passwd = data['password']
            except KeyError:
                return 'Stupid Err!'
            try:
                wxId = data['wxID']
            except KeyError:
                return 'Stupid Err!'
            if bandable(stuId, passwd):
                return bind(wxId, stuId)
            else:
                return '账号密码有误,请确认。'
        # 查询功能
        elif do == 'query':
            try:
                wxId = data['wxID']
            except KeyError:
                return 'Stupid Err!'

            try:
                type = data['type']
            except KeyError:
                return 'Stupid Err!'
            # 执行查询
            userCode = getUserCodeFromWxId(wxId) # 数据库中查询学号对应的UserCode
            # 查询函数出错，返回SelectErr，没查询到则返回None
            if not(userCode == 'SelectErr' or userCode == None):
                return webget(userCode, type)
            else:
                return '请发送“绑定+学号+教务系统密码”进行绑定\n绑定仅仅为了确认您的身份，以防您的隐私泄露\n服务器不会保存您的密码\n为确保账号安全，绑定后请尽快修改您的密码'
        # 绑定邮箱
        elif do == 'mail':
            try:
                wxId = data['wxID']
            except KeyError:
                return 'Stupid Err!'
            try:
                email = data['stuEmail']
            except KeyError:
                return 'Stupid Err!'
            try:
                type = data['type']
            except KeyError:
                return 'Stupid Err!'
            # 储存到数据库
            msg = bindmail(wxId, email)
            if msg[0:2] == 'OK':
                # 发一封邮件压压惊
                mailToStu(email, getUserCodeFromWxId(wxId), type)
                return '邮件服务开通成功，稍后您将收到一封您所有成绩的邮件。'
            else:
                return msg
        # 管理员查询命令
        elif do == 'root':
            """
            if not wxId in sqltest.getwxIDListFromUserCode('201400000407'):
                return '???'
            """
            try:
                stuId = data['stu']
            except KeyError:
                return 'Stupid Err!'
            try:
                type = data['type']
            except KeyError:
                return 'Stupid Err!'
            # 执行查询
            userCode = getUserCode(stuId)  # 数据库中查询学号对应的UserCode
            # 查询函数出错，返回SelectErr，没查询到则返回None
            if not (userCode == 'SelectErr' or userCode == None):
                return webget(userCode, type)
            else:
                return '你丫是不是写错参数了？'
        elif do == 'test':
            return "测试成功！"
        return data

def postDatatoDict(data):
    dict = {}
    data = data.split('&')
    for line in data:
        s = line.split('=')
        dict[urllib.unquote(s[0])] = urllib.unquote(s[1])
    return dict

application = app.wsgifunc()