# -*- coding: utf-8 -*-
import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    student_id = os.environ.get('student_id') or '1234567890'
    password = os.environ.get('password') or 'password'
    cookies_file = os.environ.get('cookies_file') or 'cookies'
