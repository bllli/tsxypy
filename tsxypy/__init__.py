# -*- coding: utf-8 -*-
import json
from tsxypy.config import Config
from tsxypy.SchoolSystem import SchoolSystem
from tsxypy.ScoreCatcher import ScoreCatcher
from tsxypy.ScheduleCatcher import ScheduleCatcher


def is_tsxy_stu(stu, pwd):
    """
    确认账号密码是否能够登入教务系统
    登入失败时会抛出错误
    :param stu: 学号
    :param pwd: 密码
    :return: 用户识别码 user_code
    """
    try:
        int(stu)
    except ValueError:
        raise ValueError('学号应该是一个十位数或是九位数.')
    if len(stu) not in [9, 10]:
        raise ValueError('学号应该是一个十位数或是九位数.')
    stu = SchoolSystem(stu=stu, pwd=pwd, use_cookies=False)
    stu.login()
    return stu.get_user_code()


def get_user_info_by_user_code(user_code):
    """
    通过教务系统获取用户的身份信息
    :param user_code: 用户代码 在教务系统中用于定义唯一用户 
    :return: 用户信息字典 
    """
    stu = ScoreCatcher(stu=Config.student_id, pwd=Config.password)
    stu.login()
    if user_code:
        stu_info = stu.get_user_score_json(user_code)
    else:
        stu_user_code = stu.get_user_code()
        stu_info = stu.get_user_score_json(stu_user_code)
    return json.dumps(stu_info)


def get_user_info_by_password(stu, pwd):
    """
    通过学号密码获取用户信息
    :param stu: 学号
    :param pwd: 密码
    :return: 用户信息字典
    """
    user_code = is_tsxy_stu(stu, pwd)
    return json.dumps(get_user_info_by_user_code(user_code))
