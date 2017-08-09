# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
from tsxypy.SchoolSystem import SchoolSystem
from tsxypy.Config import Config
from tsxypy.Tools import this_school_year, this_semester
from tsxypy.Exception import WrongUserCodeException, NetException, ScoreException
import bs4


class ScoreCatcher(SchoolSystem):
    def __init__(self):
        SchoolSystem.__init__(self, stu=Config.student_id, pwd=Config.password, use_cookies=True)

    def get_score(self, stu_id, user_code, score_type="new"):
        """
        获取给定用户的成绩信息
        :param stu_id: 学号 string
        :param user_code: 用户代码 string
        :param score_type: 类型 最新 new/ 所有 all string
        :return:
        """
        data_all = {
            'sjxz': 'sjxz1',
            'ysyx': 'yscj',
            'userCode': user_code,
            'xn1': "9999",
        }
        # 每个学期的不一样 懒得改
        data_new = {
            'sjxz': 'sjxz3',
            'ysyx': 'yscj',
            'userCode': user_code,
            'xn': str(this_school_year()),
            'xn1': str(this_school_year()+1),
            'xq': str(this_semester()),
        }
        data = data_all if score_type == 'all' else data_new
        r = self._session.post(url=self._url_score, data=data, headers=self.headers)
        if not r.status_code == 200:
            raise NetException("课表获取失败!")
        if '没有检索到记录' in r.text:
            raise ScoreException("还没出成绩呢")
        soup = bs4.BeautifulSoup(r.text.strip(), 'html.parser')
        person_info = []
        raw_person_info = soup.find('div', {'group': 'group'})
        if not raw_person_info:
            raise ScoreException("课表有误!没有个人信息.")
        for s in raw_person_info.stripped_strings:
            person_info.append(s.split('：')[-1])
        # 检测
        if person_info[2] != stu_id:
            raise WrongUserCodeException('获取到的课表信息不符')

        tables = soup.find_all('table')
        score_tables = []
        last_title = ''
        for index, table in enumerate(tables):
            # print("%d------------------------------" % index)
            if index % 2 == 0:  # 是标题
                title = table.text.strip().split('：')[-1]
                # print("title: %s END" % title)
                last_title = title
            else:  # 是课表
                scores_in_table = []
                for tr in table.tbody.find_all('tr'):
                    single_score = []
                    for td in tr.find_all('td'):
                        single_score.append(td.text.strip())
                        # print(td)
                        # print(td.text.strip())
                    single_score_dict = {
                        'id': single_score[0],
                        'name': single_score[1].split(']')[-1],
                        'worth': single_score[2],
                        'type': single_score[3],
                        'quale': single_score[4],
                        'exam_method': single_score[5],
                        'get_method': single_score[6],
                        'score': single_score[7],
                        'ps': single_score[8]
                    }
                    scores_in_table.append(single_score_dict)
                semester_score = {
                    'semester': last_title,
                    'scores': scores_in_table
                }
                score_tables.append(semester_score)
        return {
            'stu_id': stu_id,
            'user_code': user_code,
            'department': person_info[0],
            'major': person_info[1],
            'score_tables': score_tables,
        }


if __name__ == '__main__':
    sc = ScoreCatcher()
    import json
    print(json.dumps(sc.get_score(stu_id="4140206139", user_code="201400000407", score_type="all")))
