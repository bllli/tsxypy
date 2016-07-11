# -*- coding: utf-8 -*-
import smtplib
from email.mime.text import MIMEText

def init():
    import ini
    def iniGet(tag):
        return ini.Config('conf.ini').get('qmail', tag)
    global _user
    global _pwd
    global host
    global port
    _user = iniGet('user')
    _pwd = iniGet('passwd')
    host = iniGet('host')
    port = int(iniGet('port'))

init()#初始化

def sendMail(to, msg):
    s = smtplib.SMTP_SSL(host, port)
    s.login(_user, _pwd)  # 登陆服务器
    s.sendmail(_user, to, msg.as_string())  # 发送邮件
    s.close()

def sendTextMail(to, text, subject):
    _to = to
    # 使用MIMEText构造符合smtp协议的header及body
    msg = MIMEText(text)
    msg["Subject"] = subject
    msg["From"] = _user
    msg["To"] = _to
    # s = smtplib.SMTP("smtp.qq.com", timeout=30)  # 连接smtp邮件服务器,端口默认是25
    sendMail(_to, msg)

def sentHtmlMail(to, html, subject):
    _to = to
    mail_msg = html
    message = MIMEText(mail_msg, 'html', 'utf-8')
    message['From'] = _user
    message['To'] = _to
    message['Subject'] = subject
    sendMail(_to, message)

def mailToStu(stuMail ,userCode, type="new"):
    import tsxy
    html = tsxy.getHtml(userCode,type)
    sentHtmlMail(stuMail, html,"您的最新成绩 - 唐院社团联合会")

def toAdmin(title,msg):
    sendTextMail(to=_user, text=msg, subject=title)

if __name__ == "__main__":
    # 单独模块测试
    toAdmin('tsxyScore', 'EMail Test SUCCESS')
