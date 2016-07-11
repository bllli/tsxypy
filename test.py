import ini
host = ini.Config('conf.ini').get('qmail','port')
print type(host)