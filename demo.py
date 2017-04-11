import tsxyScore
try:
    print(tsxyScore.is_tsxy_stu('1234567890', 'password'))
except ValueError as e:
    print(e)
except RuntimeError as e:
    print(e)
