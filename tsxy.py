# -*- coding: utf-8 -*-
import re
import Image
import requests
import pytesseract
import execjs
global s
s = requests.session()
global cookies
cookies = {}
# {'JSESSIONID': 'F4CA271C29C3F19EE4B2C1F100082BA0','_gscbrs_1818056902': '1','_gscs_1818056902' : '6674883443huuj65|pv:1','_gscu_1818056902': '65435551ufem9e13'}
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

def init():
    import ini
    def iniGet(tag):
        return ini.Config('conf.ini').get('tsxy', tag)
    global _stu
    _stu = iniGet('stu')
    global _pwd
    _pwd = iniGet('pwd')

init()#初始化

def login(username =_stu, password = _pwd):
    if not (len(username) ==9 or len(username) == 10):
        raise LoginErr
    if len(password) == 0 or len(password) > 100:
        raise LoginErr
    global cookies
    randnumber = getrand()
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
        print '模拟登陆成功!'

def getHtml(userCode ,type = 'all'):
    data_all = {
        'sjxz' : 'sjxz1',
        'ysyx': 'yscj',
        'userCode': userCode,
        'xn1': '2016',
        'ysyxS': 'on',
        'sjxzS': 'on',
        'menucode_current': ''
    }
    data_new = {
        'sjxz': 'sjxz3',
        'ysyx': 'yscj',
        'userCode': userCode,
        'xn': '2015',
        'xn1': '2016',
        'xq': '1',
        'ysyxS': 'on',
        'sjxzS': 'on',
        'menucode_current': ''
    }
    if type == 'all':
        data = data_all
    else:
        data = data_new
    r = s.post(url='http://jiaowu.tsc.edu.cn/tscjw/student/xscj.stuckcj_data.jsp',
               data=data, headers=head_get,
               cookies=cookies)
    #print r.text
    if not re.compile(r'<div pagetitle="pagetitle" style="width:256mm;font-size:20px;font-weight:bold;" align="center">').search(r.text):
        raise GetErr
    return r.text

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

def getrand():
    global cookies
    geturl = execjs.compile("""
    function refreshImg(){
				var url = "http://jiaowu.tsc.edu.cn/tscjw/cas/genValidateCode?dateTime="+(new Date());
				return url;
			}
    """)
    text=''
    while(not randOK(text)):
        imgurl = geturl.call('refreshImg')
        img = requests.get(imgurl, headers=head_login)
        cookies = img.cookies
        f = open('randimg.jpg', 'wb') # 新浪云sea没有本地写权限 怎么解决啊
        f.write(img.content)
        f.close()  # 必须强制关闭 否则容易出现写后读冲突
        im = Image.open('randimg.jpg', 'r')
        # print type(im)
        text = pytesseract.image_to_string(im)
    return text

def html_to_userId(userCode):
    html = getHtml(userCode).encode('utf-8')
    #print html
    r1 = re.compile(r'<div style="float:left;.+>(.+)</div>')
    all1 = r1.findall(html)
    r2 = re.compile(r'<td>\[\d+\](.+)</td>')
    r3 = re.compile(r'<td style="text-align: right;">(\d\d\d?\.\d?)</td>')
    all2 = r2.findall(html)
    all3 = r3.findall(html)
    if all1 == []:
        raise NothingErr
    """
    for line in all1:
        print line
    for line in zip(all2, all3):
        print line[0] + ',' + line[1]
    """

    stufaculty = all1[0][15:]
    stuclass = all1[1][15:]

    lenId = 9 - len(all1[2])  # 兼容各式各样的学号
    stuId = all1[2][lenId:]

    stuname = all1[3][9:]

    print stuId + ',' + userCode + 'in!'
    import csv
    global f
    writer = csv.writer(f)
    writer.writerow(
        (userCode, stuId, stufaculty, stuclass, stuname)
    )

def userId_to_file():
    global f
    f = open('peoples.csv', 'a')
    login()
    count = 0
    nothinggot = 0
    idint = 200900000000
    while(nothinggot < 100):
        try:
            html_to_userId(str(idint))
            nothinggot = 0 #不出错就会..
        except NothingErr:
            print nothinggot
            nothinggot += 1
        except GetErr:
            try:
                login()
            except LoginErr:
                try:
                    login()
                except LoginErr:
                    try:
                        login()
                    except LoginErr:
                        print '登录失败 无力回天！'
        finally:
            print('---',count,'---')
        if count % 100 == 0: #一百个保存一下
            f.close()
            f = open('peoples.csv', 'a')
        idint += 1
        count += 1

def find_UserCode(stuId, scoreType):
    pass
    # TODO:
    # 连接数据库
    # 查询表,获取stuId
    #   -->失败 提示绑定
    #   -->成功 try getHtml(userCode)
    #  except 提示用户绑定

def band(stuId, password):
    try:
        login(stuId, password)
    except LoginErr:
        try:
            login(stuId, password)
        except LoginErr:
            try:
                login(stuId, password)
            except LoginErr:
                # TODO: 记录到数据库/登录失败记录
                pass
    finally:
        return

def webget(userCode, type):
    try:
        html = getHtml(userCode, type)
    except GetErr:
        try:
            login()
        except LoginErr:
            try:
                login()
            except LoginErr:
                try:
                    login()
                except LoginErr:
                    return 'err'
        try:
            html = getHtml(userCode, type)
        except:
            return 'err'

    scores = re.compile(r'<tr>.+?>(\d+)<.+?](.+?)</td>.+?right;">\d+.+?</td>.+?right;">(.+?)</td>.+?center.+?</tr>', re.S)
    allScore = ""
    for line in scores.findall(html):
        for word in line:
            allScore = allScore + word + ' '
        allScore = allScore + '\n'
    return allScore

try:
    login()
except LoginErr:
    try:
        login()
    except LoginErr:
        try:
            login()
        except LoginErr:
            print('麻溜的重启')

print(webget('201400000309','new'))# uwsig控制台看到了这个打印出的信息, 说明tsxy.py启动成功
#print getHtml('201400000309')
# http://jiaowu.tsc.edu.cn/tscjw/jw/common/showYearTerm.action
# userId_to_file()