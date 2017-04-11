class MyErr(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
    pass


class LoginErr(MyErr):
    pass


class GetErr(MyErr):
    pass


class NothingErr(GetErr):
    pass
