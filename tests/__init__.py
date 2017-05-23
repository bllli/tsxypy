# -*- coding: utf-8 -*-
from tsxypy import SchoolSystem
from tsxypy.Config import Config

if '1234567890' in Config.student_id:
    raise ValueError("默认学号, 请添加环境变量")

ss = SchoolSystem(stu=Config.student_id, pwd=Config.password, use_cookies=False)
ss.login()
