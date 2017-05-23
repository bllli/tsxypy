# -*- coding: utf-8 -*-
import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:

    student_id = os.environ.get('STU_ID') or '1234567890'
    password = os.environ.get('STU_PWD') or 'password'
    cookies_file = os.environ.get('COOKIES_FILE') or 'cookies'
