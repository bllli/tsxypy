# tsxyScore
tsxyScore是一个青果教务系统非官方查分Web API
## package
####pytesseract
####PIL Image
####execjs
####requests
## usage
####start
  uwsig --http :9001 -w webapi
####post
#####post url
  http:120.0.0.1:9001/weix/
#####post data
  -  POST/接受数据
    - do 键
        - query
        - bind
    - do 为 query 时
        - wxID 键 任意字符串,不重复
        - type 键 all/new 全部/最新
    - do 为 bind 时
        - stu 学号
        - password 密码
        - wxID 任意字符串,不重复
    - do 为 root
        - stu
        - type

