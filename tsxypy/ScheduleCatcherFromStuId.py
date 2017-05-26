# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import bs4

from tsxypy.SchoolSystem import SchoolSystem
from tsxypy.Config import Config
from tsxypy.Exception import NetException, NoneScheduleException, WrongScheduleException
from tsxypy.Tools import week_info_to_week_list, translate


class ScheduleCatcherFromStuId(SchoolSystem):
    """
    爬取全校教学安排表-学生课表
    通过学号获取课程信息
    """
    def __init__(self):
        SchoolSystem.__init__(self, stu=Config.student_id, pwd=Config.password, use_cookies=True)

    def get_schedule(self, stu_id, school_year, semester):
        """
        获取课程表
        :param stu_id: 学号
        :param school_year: 当前学年
        :param semester: 学期 '0'上学期; '1'下学期
        :return: 
        """
        url = "http://jiaowu.tsc.edu.cn/tscjw/kbbp/dykb.xskb_data.jsp"
        data = {
            "xn": str(school_year),  # 今年
            "xn1": str(school_year + 1),  # 明年 意为今年到明年的课表
            'xq_m': semester,
            'txtXH': stu_id
        }
        r = self._session.post(url=url, data=data, headers=self.headers)
        if not r.status_code == 200:
            raise NetException("课表获取失败!")
        soup = bs4.BeautifulSoup(r.text.strip(), 'html.parser')
        # 个人信息处理
        # 0 学号 1 姓名 2 班级 3 课程门数
        person_info = []
        raw_person_info = soup.find('div', {'group': 'group'})
        if not raw_person_info:
            raise NoneScheduleException("没有课表!")
        for s in raw_person_info.stripped_strings:
            person_info.append(s.split('：')[-1])
        # 检测
        if person_info[0] != stu_id:
            raise WrongScheduleException('获取到的课表信息不符')

        # 课程信息处理
        table = soup.find("tbody")
        if table is None:
            raise NoneScheduleException("没有课表!")

        last_course_name = 'error'
        courses = []
        for single_course_raw_info in table.find_all('tr'):
            single_course_info = []  # 用于保存一条课程信息
            info_flag = 0
            for line in single_course_raw_info.children:
                # 课程名 老师 班号(没用) 周 单双 上课时间 上课地点
                # 0: [20080038]C#程序设计A
                # 1: 张铁军
                # 2: 001
                # 3: 1-7
                # 4: (单双周)
                # 5: 四[7 - 8节]
                # 6: A305
                if line.name != 'td':
                    continue
                # print('%d: %s' % (info_flag, line.string.strip()))
                info = line.string.strip()  # info 为标签内的信息
                if info_flag == 0:  # ‘课程名’列
                    if len(info) == 0:
                        # 一堂课每周有多节时 html表格中的课程名只写第一个 接下来的课程信息中，课程名会被会省略
                        # 所以如果info_flag为0 即课程名一列为空时, 将课程名设置为上一个课程名
                        info = last_course_name
                    else:
                        info = info.split(']')[-1]  # 去除无用的课程代号
                        last_course_name = info
                elif info_flag == 4:  # '单双周' 列
                    if info == '':  # 空白的代表不论单双周都上课
                        info = None
                    elif info == '单':
                        info = '单周'
                    elif info == '双':
                        info = '双周'
                info = info if info is None or len(info) != 0 else None
                single_course_info.append(info)
                info_flag += 1
            if len(single_course_info) != 7:
                raise WrongScheduleException("课程表有误!")
            course_when = single_course_info[5]  # 未整理的时间 存在一上课就上一上午的情况
            # print(course_when)
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
                    'name': single_course_info[0],
                    'worth': None,
                    'teacher': single_course_info[1],
                    'week': week_info_to_week_list(single_course_info[3], single_course_info[4]),
                    'week_raw': single_course_info[3],
                    'parity': single_course_info[4],
                    'which_room': single_course_info[6],
                    'where': None,
                }
                courses.append(course_dict)
        return {
            'department': None,
            'grade': None,
            'major': None,
            'class_name': person_info[2],
            'class_code': None,
            'school_year': str(school_year),
            'semester': semester,
            'courses': courses,
        }

if __name__ == '__main__':
    import json
    sct = ScheduleCatcherFromStuId()
    print(json.dumps(sct.get_schedule('4154001131', 2016, '1')))
