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


class Syllabus(Student):
    """
    课程表 目前只抓取教务系统中的课程表
    """
    def __init__(self):
        super(Syllabus, self).__init__(stu=Config.student_id, pwd=Config.password, use_cookies=True)

    def _get_drop_lists(self, data, err_info):
        url = 'http://jiaowu.tsc.edu.cn/tscjw/frame/droplist/getDropLists.action'
        r = self._session.post(url=url, data=data, headers=self.headers)
        if r.status_code == 200:
            return json.loads(r.text)
        else:
            raise RuntimeError(err_info)

    def get_school_area(self):
        data = {
            'comboBoxName': 'MsSchoolArea',
        }
        return self._get_drop_lists(data, '获取校区信息失败!')

    def get_yxb(self, grade):
        """
        获取院系部信息
        :param grade: 年级 四位数字 string 如 '2014' 
        :return: 院系部信息列表 list
        """
        data = {
            'comboBoxName': 'MsYXB',
            'paramValue': 'nj=%s' % grade,
        }
        return self._get_drop_lists(data, '获取院系部信息失败!')

    def get_specialty(self, grade, department):
        data = {
            'comboBoxName': 'MsYXB_Specialty',
            'paramValue': 'nj=%s&dwh=%s' % (grade, department),
        }
        return self._get_drop_lists(data, '获取专业信息失败!')

    def get_class(self, grade, department, major):
        data = {
            'comboBoxName': 'MsYXB_Specialty_Class',
            'paramValue': 'nj=%s&dwh=%s&zydm=%s' % (grade, department, major),
        }
        return self._get_drop_lists(data, '获取班级信息失败!')

    def get_syllabus(self, class_code, school_year, semester):
        """
        获取课程表
        :param class_code: 班级代码
        :param school_year: 学年起始 四位数字 *注意不能是字符串* 如:2016-2017学年 应传入2016
        :param semester: '0': 上半学期 或 '1': 下半学期
        :return: 课程dict
        """
        url = 'http://jiaowu.tsc.edu.cn/tscjw/kbbp/dykb.GS1.jsp?kblx=bjkb'
        data = {
            'hidBJDM': class_code,  # 班级代码
            'hidCXLX': 'fbj',  # 意思差不多是"分班级"
            'xn': str(school_year),  # 学年 2016-2017学年
            'xn1': str(school_year + 1),
            'xq_m': semester,  # 学期 0为上学期; 1为下学期
        }
        r = self._session.post(url=url, data=data, headers=self.headers)
        if not r.status_code == 200:
            raise RuntimeError("课表获取失败!")
        courses = []
        soup = bs4.BeautifulSoup(r.text, 'html.parser')
        class_info = []
        raw_class_info = soup.find('div', {'group': 'group'})
        if not raw_class_info:
            raise RuntimeError("没有课表!")
        for s in raw_class_info.stripped_strings:
            class_info.append(s.split('：')[-1])
        # 获取课程表前的班级信息 按顺序分别是 系别/年级/专业/班级
        for div in soup.find_all('div', 'div1'):
            # 遍历课程信息
            if not len(div.get_text().strip()) > 0:
                # 过滤无课程的表格中的块
                continue
            # print(div['id'])
            # id 是三位数字组成的字符串 第一位为0 第二位是周次 第三位是节次 如:012意味着周一的第二节课
            course_strs = div.stripped_strings
            if '体育' in div.get_text():
                course_strs = ['体育课']
            elif '网选' in div.get_text():
                # 网选课你是来捣乱的吧? 负分滚粗
                continue
            for course_str in course_strs:
                course = '%s' % course_str
                if not len(course) > 0:
                    continue
                # print(course)
                # 课程字符串处理
                # 课程名称 学分 教师 周次 [单双周] 节次 [上课教室 上课校区]
                # 目前来看有这样几种情况
                # 1. len(course.split(' ')) == 8 包含单双周信息及上课校区教室
                # 2. len(course.split(' ')) == 7 不包含单双周信息,但包含上课校区教室
                # 3. len(course.split(' ')) == 6 包含单双周信息,但不包含上课校区教室
                # 4. len(course.split(' ')) == 5 不包含单双周信息,也不包含上课校区教室
                # p.s. 没校区教室的一般都是实验课
                # 5. '体育' in course 时...就写个课程名和上课周次/节次就好了
                # 体育课男女生分开上课,有时时间地点都不同, 就写个课程名和上课周次/节次就好了
                # 其他: 抛弃, 打log
                splited = course.split('\xa0')  # 这是中文空格???真是醉了
                name, worth, teacher, week, parity, when, which_room, where = [None] * 8
                if len(splited) == 8:
                    name, worth, teacher, week, parity, when, which_room, where = splited
                elif len(splited) == 7:
                    name, worth, teacher, week, when, which_room, where = splited
                elif len(splited) == 6:
                    name, worth, teacher, week, parity, when = splited
                elif len(splited) == 5:
                    name, worth, teacher, week, when = splited
                elif '体育' in course:
                    name = splited[0]
                else:
                    print(course)
                    print(len(splited))
                    print(splited)
                    continue
                course_dict = {
                    'when_code': div['id'],
                    'name': name,
                    'worth': worth,
                    'teacher': teacher,
                    'week': week,
                    'parity': parity,
                    'which_room':which_room,
                    'where': where,
                }
                # print(course_dict)
                courses.append(course_dict)
        return {
            'department': class_info[0],
            'grade': class_info[1],
            'major': class_info[2],
            'class_name': class_info[3],
            'class_code': class_code,
            'school_year': str(school_year),
            'semester': semester,
            'courses': courses,
        }

    def print_all(self):
        """
        用来获取班级代码与班级名称的对应关系
        :return: 
        """
        for school_area in self.get_school_area():
            print("%s %s" % (school_area['code'], school_area['name']))

        for year in ['2013', '2014', '2015', '2016']:
            print(year)
            yxbs = self.get_yxb(year)
            if not yxbs:
                continue
            for yxb in yxbs:
                print("%s %s" % (yxb['code'], yxb['name']))
                specialtys = self.get_specialty(year, yxb['code'])
                if not specialtys:
                    continue
                for specialty in specialtys:
                    print("--%s %s" % (specialty['code'], specialty['name']))
                    _classs = self.get_class(year, yxb['code'], specialty['code'])
                    for _class in _classs:
                        print("----%s %s" % (_class['code'], _class['name']))


if __name__ == "__main__":
    # http://jiaowu.tsc.edu.cn/tscjw/jw/common/showYearTerm.action
    # li = Student(stu=Config.student_id, pwd=Config.password, use_cookies=False)
    # li.login()
    # userCode = li.get_user_code()
    # print(userCode)
    # print(li.get_user_score_json(userCode))
    li = Syllabus()
    li.login()
    # li.print_all()

    print(json.dumps(li.get_syllabus('2015020601', 2016, '1')))
