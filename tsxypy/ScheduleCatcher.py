# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import json
import sys
import bs4

from tsxypy.SchoolSystem import SchoolSystem
from tsxypy.Config import Config
from tsxypy.Tools import week_info_to_week_list, translate
from tsxypy.Exception import NoneScheduleException, NetException, WrongScheduleException


class ScheduleCatcher(SchoolSystem):
    """
    课程表 目前只抓取教务系统中的课程表
    爬取全校教学安排表-班级课表
    通过下拉列表获取学校结构及班级代码, 通过班级代码获取课程信息
    """
    def __init__(self):
        SchoolSystem.__init__(self, stu=Config.student_id, pwd=Config.password, use_cookies=True)

    def _get_drop_lists(self, data, err_info):
        url = 'http://jiaowu.tsc.edu.cn/tscjw/frame/droplist/getDropLists.action'
        r = self._session.post(url=url, data=data, headers=self.headers)
        if r.status_code == 200:
            return json.loads(r.text)
        else:
            raise NetException(err_info)

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

    def get_schedule(self, class_code, school_year, semester):
        """
        获取课程表
        班级课表 格式一
        课程表table的id确认上课时间(第几周第几节课), 解析单元格内字符串来获取课程信息.
        注意字符串中是以全角字符空格分隔信息项的, 而具体有多少个信息项是不确定的.
        我在本函数的课程字符串处理中描述了几种情况, 但体育课和网选课实在没有通用的逻辑...
        所以我只解析体育课的上课时间, 并直接放弃解析含有网选课的单元格
        但是这样的代码无法应对一个上课时间含有网选课和其他课的情况.
        -决定放弃爬该接口, 此处代码留到下个版本再删-
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
            raise NetException("课表获取失败!")
        courses = []
        soup = bs4.BeautifulSoup(r.text, 'html.parser')
        class_info = []
        raw_class_info = soup.find('div', {'group': 'group'})
        if not raw_class_info:
            raise NoneScheduleException("没有课表!")
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
                    'week': week_info_to_week_list(week, parity),
                    'week_raw': week,
                    'parity': parity,
                    'which_room': which_room,
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

    def get_school_json(self):
        """
        用来获取班级代码与班级名称的对应关系
        按现在抓取的数据分析来看, 各个年级的院系部代码和专业代码都是不变的.
        但为稳妥起见(以防抽风改成不一致), 仍按照教务系统原有的从年份开始设计json.
        学校-年份-系别(院系部)-专业-班级.
        classes = {'name': '14计本1', 'code': '2014020601'}
        specialty = {'name': '计算机专业与技术', 'code': '4001', 'classes': [c1, c2...]}
        department = {'name': '计算机专业与技术系', 'code': '40', 'specialties': [s1, s2...]}
        school_year = {'year': '2014', 'departments': [department1, department2...]}
        school = {'school_years': [school_year1, school_year2...]}
        差不多就是这样
        :return: 
        """
        for school_area in self.get_school_area():
            print("%s %s" % (school_area['code'], school_area['name']))
        school_years = []
        for year in ['2013', '2014', '2015', '2016']:
            print(year)
            yxbs = self.get_yxb(year)
            if not yxbs:
                continue
            departments = []
            for yxb in yxbs:
                print("%s %s" % (yxb['code'], yxb['name']))

                specialtys = self.get_specialty(year, yxb['code'])
                if not specialtys:
                    continue
                specialties_json = []
                for specialty in specialtys:
                    print("--%s %s" % (specialty['code'], specialty['name']))
                    _classes = self.get_class(year, yxb['code'], specialty['code'])
                    _classes_json = []
                    for _class in _classes:
                        print("----%s %s" % (_class['code'], _class['name']))
                        _class_json = {
                            'name': _class['name'].split(']')[1],
                            'code': _class['code'],
                        }
                        _classes_json.append(_class_json)
                    specialty_json = {
                        'name': specialty['name'].split(']')[1],
                        'code': specialty['code'],
                        'classes': _classes_json,
                    }
                    specialties_json.append(specialty_json)
                department = {
                    'name': yxb['name'].split(']')[1],
                    'code': yxb['code'],
                    'specialties': specialties_json,
                }
                departments.append(department)
            school_year = {
                'year': year,
                'departments': departments,
            }
            school_years.append(school_year)
        return {
            'school_years': school_years,
        }

    def get_schedule_form_two(self, class_code, school_year, semester):
        """
        获取课程表
        班级课表 格式二
        很开心的发现竟然还有一个格式二的接口可以爬
        
        :param class_code: 班级代码
        :param school_year: 学年起始 四位数字 *注意不能是字符串* 如:2016-2017学年 应传入2016
        :param semester: '0': 上半学期 或 '1': 下半学期
        :return: 课程dict
        """
        url = 'http://jiaowu.tsc.edu.cn/tscjw/kbbp/dykb.bjkb_data.jsp'
        data = {
            'hidBJDM': class_code,  # 班级代码
            'hidCXLX': 'fbj',  # 意思差不多是"分班级"
            'xn': str(school_year),  # 学年 2016-2017学年
            'xn1': str(school_year + 1),
            'xq_m': semester,  # 学期 0为上学期; 1为下学期
            'selGS': '2',
            'radioa': '5',
        }
        r = self._session.post(url=url, data=data, headers=self.headers)
        if not r.status_code == 200:
            raise NetException("课表获取失败!")
        courses = []
        soup = bs4.BeautifulSoup(r.text, 'html.parser')
        class_info = []
        raw_class_info = soup.find('div', {'group': 'group'})
        if not raw_class_info:
            raise NoneScheduleException("没有课表!")
        for s in raw_class_info.stripped_strings:
            class_info.append(s)
        raw_course_tables = soup.find_all('table')
        upper = []
        courses = []
        for table in raw_course_tables:
            for tr in table.find_all('tr'):
                # print('--------')
                if tr.td.string == '课程' or (tr.td.string is not None and '网选' in tr.td.string):
                    # 筛去网选课和
                    continue
                single_course_info = []
                for td in tr.find_all('td'):
                    # 课程 学分 总学时 讲授学时 实验学时 实践学时 其它学时 考核方式 课程类别 教师 上课班号 上课人数 周次 单双周 节次 地点
                    # print(td.string)

                    single_course_info.append(td.string)

                if single_course_info[0] is None:
                    # 补全表格
                    if len(upper) != len(single_course_info):
                        raise WrongScheduleException('课表表单项不同, 无法解析:%s vs %s' % (upper, single_course_info))
                    item_at = 0
                    for one in single_course_info:
                        if one is None:
                            single_course_info[item_at] = upper[item_at]
                        item_at += 1
                else:
                    # print("Set upper success")
                    upper = list(single_course_info)
                # print(single_course_info)
                course_when = single_course_info[14]
                c = course_when.split('[')[1].strip(']')  # 上课节次
                when_code_dict = {
                    '1-2节': [1],
                    '3-4节': [2],
                    '5-6节': [3],
                    '7-8节': [4],
                    '9-10节': [5],
                    # 一大节变两小节
                    '1-4节': [1, 2],
                    '5-8节': [3, 4],
                }
                try:
                    course_times = when_code_dict[c]
                except KeyError:
                    raise WrongScheduleException('无法识别部分课程!节次代码错误!')
                for course_time in course_times:
                    when_code_dict_week = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7}
                    try:
                        when_code_week = when_code_dict_week[course_when.split('[')[0]]
                    except KeyError:
                        raise WrongScheduleException('无法识别部分课程!周次代码错误!')
                    course_dict = {
                        'when_code': '0%d%d' % (when_code_week, course_time),
                        'nickname': translate(single_course_info[0]),
                        'name': single_course_info[0].split(']')[-1],
                        'worth': single_course_info[1],
                        'teacher': single_course_info[9].split(']')[-1],
                        'week': week_info_to_week_list(single_course_info[12], single_course_info[13]),
                        'week_raw': single_course_info[12],
                        'parity': single_course_info[13],
                        'which_room': single_course_info[15],
                        'where': None,
                    }
                    courses.append(course_dict)
        return {
            'department': class_info[1],
            'grade': None,
            'major': class_info[2],
            'class_name': class_info[3],
            'class_code': class_code,
            'school_year': str(school_year),
            'semester': semester,
            'courses': courses,
        }


if __name__ == '__main__':
    sc = ScheduleCatcher()
    print(json.dumps(sc.get_schedule_form_two('2014020601', 2016, '1')))
