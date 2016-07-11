# -*- coding: utf-8 -*-
import re
import Image
import requests
import pytesseract
import execjs
import os

head_login = {
    'Host':'jiaowu.tsc.edu.cn',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0',
    'Referer':'http://jiaowu.tsc.edu.cn/tscjw/cas/login.action',
    'Accept':'image/webp,image/*,*/*;q=0.8',
    'Accept-Encoding':'gzip, deflate, sdch',
    'Accept-Language':'zh-CN,zh;q=0.8',
    'Connection':'keep-alive',
    'Upgrade-Insecure-Requests':'1'
}
head_post = {
    'Host':'jiaowu.tsc.edu.cn',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0',
    'Referer':'http://jiaowu.tsc.edu.cn/tscjw/cas/login.action',
    'Content-Length':'96',
    'Content-Type':'application/x-www-form-urlencoded',
    'Accept':'image/webp,image/*,*/*;q=0.8',
    'Accept-Encoding':'gzip, deflate, sdch',
    'Accept-Language':'zh-CN,zh;q=0.8',
    'Connection':'keep-alive'
}
head_get = {
    'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding':'gzip, deflate',
    'Accept-Language':'zh-CN,zh;q=0.8',
    'Cache-Control':'max-age=0',
    'Connection':'keep-alive',
    'Content-Length':'100',
    'Content-Type':'application/x-www-form-urlencoded',
    'Host':'jiaowu.tsc.edu.cn',
    'Origin':'http://jiaowu.tsc.edu.cn',
    'Referer':'http://jiaowu.tsc.edu.cn/tscjw/student/xscj.stuckcj.jsp?menucode=JW130706',
    'Upgrade-Insecure-Requests':'1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0'
}

class tsxyErr(BaseException):
    pass

class LoginErr(tsxyErr):
    pass

class GetErr(tsxyErr):
    pass

class NothingErr(tsxyErr):
    pass

def login(username, password):
    if not (len(username) ==9 or len(username) == 10):
        raise LoginErr
    if len(password) == 0 or len(password) > 100:
        raise LoginErr
    ##getrand
    cookies = {}
    s = requests.session()
    jpgfile = 'rand' + username + '.jpg'
    geturl = execjs.compile("""
        function refreshImg(){
    				var url = "http://jiaowu.tsc.edu.cn/tscjw/cas/genValidateCode?dateTime="+(new Date());
    				return url;
    			}
        """)
    text = ''
    while (not randOK(text)):
        imgurl = geturl.call('refreshImg')
        img = requests.get(imgurl, headers=head_login)
        cookies = img.cookies
        f = open(jpgfile, 'wb')  # 新浪云sea没有本地写权限 怎么解决啊
        f.write(img.content)
        f.close()  # 必须强制关闭 否则容易出现写后读冲突
        im = Image.open(jpgfile, 'r')
        # print type(im)
        text = pytesseract.image_to_string(im)
    os.remove(jpgfile)#删除验证码图片
    randnumber = text
    #获取经password/验证码混合加密所得的passwd
    passwd = md5passwd(password, randnumber)
    data = {
        'username':username,
        'password':passwd,
        'randnumber':randnumber,
        'isPasswordPolicy':1
    }
    s.post(url='http://jiaowu.tsc.edu.cn/tscjw/cas/logon.action',
               cookies=cookies, data=data, headers=head_post)
    r2 = s.get(url='http://jiaowu.tsc.edu.cn/tscjw/MainFrm.html',
               cookies=cookies,headers = head_login)
    # cookies = r2.cookies
    # print r2.text
    r = re.compile('<p>This.+frames')
    if not r.search(r2.text):
        raise LoginErr
    else:
        print('bindable!')
        return True

def md5passwd(password, randnumber):
    def md5Encode(str):
        import hashlib

        m = hashlib.md5(str.encode(encoding='utf-8'))
        return m.hexdigest()

    passwd = md5Encode(md5Encode(password) + md5Encode(randnumber))

    return passwd

def randOK(text):
    if len(text) != 4:
        return False
    try:
        num = int(text)
    except:
        return False
    if num > 1000 and num < 9999:
        print text + 'Got'
        return True
    return False

def bandable(stuId, password):
    try:
        login(stuId, password)
    except LoginErr:
            try:
                login(stuId, password)
            except LoginErr:
                return False
    return True
