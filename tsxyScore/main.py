# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
import re
import sys
import pytesseract
import requests
import bs4

from datetime import datetime
from PIL import Image
import json

from tsxyScore.config import Config
from tsxyScore.tools import md5password, rand_ok, save_cookies, load_cookies


GMT_FORMAT = '%a %b %d %Y %H:%M:%S GMT+0800 (CST)'
# 这是校园网验证码页面url需要的日期格式 感谢 http://ju.outofmemory.cn/entry/1078
if sys.version_info.major == 3:
    unicode = str
else:
    bytes = str


class Student(object):
    def __init__(self, stu, pwd, use_cookies=True):
        self._session = requests.session()
        base_url = 'http://jiaowu.tsc.edu.cn/tscjw%s'
        self._url_login = base_url % '/cas/logon.action'
        self._url_main = base_url % '/MainFrm.html'
        self._url_score = base_url % '/student/xscj.stuckcj_data.jsp'
        self._url_rand_img = base_url % "/cas/genValidateCode?dateTime=%s"

        self._stu = stu
        self._pwd = pwd

        self.headers = {
            'Host': 'jiaowu.tsc.edu.cn',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0',
            'Referer': 'http://jiaowu.tsc.edu.cn/tscjw/cas/login.action',
            'Connection': 'keep-alive',
        }
        if use_cookies:
            self.cookies_login()

    def login(self):
        """
        模拟登陆 保留cookies及session以保存登陆状态
        :return:无返回值
        """
        def get_rand():
            """
            获取验证码值 / 同时获取验证码页面的 cookies 到 self._cookies
            :return: 识别出的验证码
            """
            text = ''
            while not rand_ok(text):
                img_url = self._url_rand_img % str(datetime.now().strftime(GMT_FORMAT))
                img = self._session.get(img_url, headers=self.headers)
                self._cookies = img.cookies  # 以后的模拟登录需要这个cookies
                # 无须使用本地写权限/不会留下多余的验证码文件
                # thank to http://stackoverflow.com/questions/31064981/python3-error-initial-value-must-be-str-or-none
                from io import BytesIO
                im = Image.open(BytesIO(img.content))
                text = pytesseract.image_to_string(im)  # 识别图像
            return text

        rand_number = get_rand()
        password = md5password(self._pwd, rand_number)
        # 登陆提交的信息
        data = {
            'username': self._stu,
            'password': password,
            'randnumber': rand_number,
            'isPasswordPolicy': 1
        }
        r = self._session.post(url=self._url_login, data=data, headers=self.headers)
        # 200 成功
        # 401 验证码有误
        # 402 账号或密码有误
        response = json.loads(r.content.decode('utf-8'))
        status = response['status']
        if status == '401':
            self.login()
        elif status == '402':
            raise RuntimeError('402, 账号或密码错误')

    def cookies_login(self):
        """
        安全登陆:不断加载文件cookies/模拟登陆,直到登陆成功为止
        :return:
        """
        while True:
            cookies = load_cookies()
            if cookies is not None:
                self._session.cookies.update(cookies)
                if self.is_login():
                    return
                else:
                    self.login()
                    save_cookies(self._session.cookies)
            else:
                self.login()
                save_cookies(self._session.cookies)
                if self.is_login():
                    return

    def get_user_code(self):
        """
        登陆状态下可以获取登录账户的UserCode
        获取不到说明没有登陆
        :return: 返回获取到的UserCode
        """
        url = 'http://jiaowu.tsc.edu.cn/tscjw/jw/common/showYearTerm.action'
        t = self._session.get(url=url, headers=self.headers)
        r = re.compile('"userCode":"(.+?)"')
        user_code = r.search(t.text).groups()[0]
        return user_code if user_code != 'kingo.guest' else None

    def is_login(self):
        # 获取主页HTML 判断是否成功登陆
        r2 = self._session.get(url=self._url_main, headers=self.headers)
        # 正则表达式 判断抓取的页面是否有登陆成功时会出现的值.对 就是这么丑 :)
        r = re.compile('<p>This.+frames')
        return True if r.search(r2.text) else False

    def get_score_html_page(self, user_code, score_type="new"):
        """
        提交表单获取分数页面HTML代码
        :param user_code: 用户代码
        :param score_type: 类型 最新 new/ 所有 all
        :return:
        """
        data_all = {
            'sjxz': 'sjxz1',
            'ysyx': 'yscj',
            'userCode': user_code,
            'xn1': '2016',
            'ysyxS': 'on',
            'sjxzS': 'on',
            'menucode_current': ''
        }
        # 每个学期的不一样 懒得改
        data_new = {
            'sjxz': 'sjxz3',
            'ysyx': 'yscj',
            'userCode': user_code,
            'xn': '2015',
            'xn1': '2016',
            'xq': '1',
            'ysyxS': 'on',
            'sjxzS': 'on',
            'menucode_current': ''
        }
        data = data_all if score_type == 'all' else data_new
        r = self._session.post(url=self._url_score, data=data, headers=self.headers)
        # print(r.url)
        if 'login.action' in r.url:
            # 响应的url中含有logon时, 可以认为未登陆成功
            self.login()
            return self.get_score_html_page(user_code, score_type)
        return r.text

    def get_user_score_json(self, user_code, score_type='all'):
        """
        获取整理过的分数数据
        """
        html = self.get_score_html_page(user_code, score_type)
        soup = bs4.BeautifulSoup(html, 'html.parser')
        try:
            department = soup.find_all('div')[3].string.split(u'：')[1]
            grade = soup.find_all('div')[4].string.split(u'：')[1]
            stu_id = soup.find_all('div')[5].string.split(u'：')[1]
            stu_name = soup.find_all('div')[6].string.split(u'：')[1]
        except IndexError:
            raise RuntimeError('user_code error')

        def yield_elem(trs):
            for td in trs:
                if td.string == '\n':
                    continue
                yield td.string

        all_course = []
        for tr in soup.find_all('tr'):
            if len(tr) < 19:  # 分数表的tr对象len一定不小于19, 筛去不符合条件的行
                continue
            next_elem = yield_elem(tr)
            course_id = next_elem.send(None)
            if course_id == '序号':
                continue
            single_course = {
                '序号': course_id,
                '课程': next_elem.send(None),
                '学分': next_elem.send(None),
                '类别': next_elem.send(None),
                '修读性质': next_elem.send(None),
                '考核方式': next_elem.send(None),
                '取得方式': next_elem.send(None),
                '成绩': next_elem.send(None),
                '备注': next_elem.send(None),
            }
            all_course.append(single_course)
        return {
            'student_name': stu_name,
            'student_id': stu_id,
            'department': department,
            'grade': grade,
            'scores': all_course,
        }


if __name__ == "__main__":
    # http://jiaowu.tsc.edu.cn/tscjw/jw/common/showYearTerm.action
    li = Student(stu=Config.student_id, pwd=Config.password, use_cookies=False)
    li.login()
    userCode = li.get_user_code()
    print(userCode)
    print(li.get_user_score_json(userCode))
