# coding=utf-8
import tsxypy
try:
    print(tsxypy.is_tsxy_teacher('t0681', '教师密码'))
    # print(tsxypy.is_tsxy_stu('1234567890', 'password'))
except ValueError as e:
    print(e)
except RuntimeError as e:
    print(e)
