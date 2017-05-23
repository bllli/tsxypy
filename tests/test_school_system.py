# -*- coding: utf-8 -*-
import unittest
from tsxypy import SchoolSystem
from tests import ss


class SchoolSystemTestCase(unittest.TestCase):
    def setUp(self):
        self.ss = ss

    def tearDown(self):
        pass

    def test_login(self):
        self.assertTrue(self.ss.is_login())
        self.assertTrue(self.ss.get_user_code())

    def test_cookies_login(self):
        ss_cookies = SchoolSystem(stu="no", pwd="no", use_cookies=True)
        self.assertTrue(self.ss.get_user_code() == ss_cookies.get_user_code())

    def test_could_found_wrong_pwd(self):
        ss_wrong_pw = SchoolSystem(stu="wrong", pwd="wrong", use_cookies=False)
        with self.assertRaises(RuntimeError):
            ss_wrong_pw.login()
