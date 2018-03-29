# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
import re
import bs4
import sys
import json
import requests
import pytesseract

from datetime import datetime
from PIL import Image

from tsxypy.Config import Config
from tsxypy.Tools import md5password, rand_ok, save_cookies, load_cookies, gen_login_params
from tsxypy.Exception import WrongPasswordException


class SchoolSystem:
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
            'Referer': 'http://jiaowu.tsc.edu.cn/tscjw/cas/login.action',
            'Host': 'jiaowu.tsc.edu.cn',
            'Origin': 'http://jiaowu.tsc.edu.cn',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
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
                GMT_FORMAT = '%a %b %d %Y %H:%M:%S GMT+0800 (CST)'
                # 这是校园网验证码页面url需要的日期格式 感谢 http://ju.outofmemory.cn/entry/1078
                img_url = self._url_rand_img % str(datetime.now().strftime(GMT_FORMAT))
                img = self._session.get(img_url, headers=self.headers)
                self._cookies = img.cookies  # 以后的模拟登录需要这个cookies
                # 无须使用本地写权限/不会留下多余的验证码文件
                # thank to http://stackoverflow.com/questions/31064981/python3-error-initial-value-must-be-str-or-none
                from io import BytesIO
                byteImgIO = BytesIO(img.content)
                byteImgIO.seek(0)
                im = Image.open(byteImgIO)
                # thanks to http://stackoverflow.com/questions/31077366/pil-cannot-identify-image-file-for-io-bytesio-object
                text = pytesseract.image_to_string(im)  # 识别图像
            return text

        rand_number = get_rand()
        # 登陆提交的信息
        params = gen_login_params(self._stu, self._pwd, self._session.cookies.get('JSESSIONID'), rand_number)
        r = self._session.get(url=self._url_login, params=params, headers=self.headers)
        # 200 成功
        # 401 验证码有误
        # 402 账号或密码有误
        # 5000
        response = json.loads(r.content.decode('utf-8'))
        status = response['status']
        if status == '402':
            raise WrongPasswordException('402, 账号或密码错误')
        elif status != '200':
            self.login()
        save_cookies(self._session.cookies)

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


if __name__ == "__main__":
    # http://jiaowu.tsc.edu.cn/tscjw/jw/common/showYearTerm.action
    # li = Student(stu=Config.student_id, pwd=Config.password, use_cookies=False)
    # li.login()
    # userCode = li.get_user_code()
    # print(userCode)
    # print(li.get_user_score_json(userCode))

    import os
    print(os.environ.get('STU_ID'))
    li = SchoolSystem(stu=Config.student_id, pwd=Config.password)
    li.login()
    print('-------')
    print(li.get_user_code())
    # print(json.dumps(li.get_syllabus('2015020601', 2016, '1')))
