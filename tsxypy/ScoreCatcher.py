# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
from tsxypy.SchoolSystem import SchoolSystem
from tsxypy.Exception import WrongUserCodeException
import bs4


class ScoreCatcher(SchoolSystem):
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
            raise WrongUserCodeException('given user_code:%s' % user_code)

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
                '课程': next_elem.send(None).split(']')[1],
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
