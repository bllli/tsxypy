# -*- coding: utf-8 -*-
class TsxyException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class WrongPasswordException(TsxyException):
    pass


class NetException(TsxyException):
    pass


class WrongUserCodeException(TsxyException):
    pass


class ScoreException(TsxyException):
    pass


class ScheduleException(TsxyException):
    pass


class NoneScheduleException(ScheduleException):
    pass


class WrongScheduleException(ScheduleException):
    pass
