# tsxypy
tsxypy是一个基于Python的非官方唐山学院教务系统api

只做好"获取教务系统的信息"这一件事

尽力适配Python2.7 + Python3

# Usage
## 安装
### 下载/安装
```bash
git clone https://github.com/bllli/tsxyScore
cd tsxyScore
sudo pip install -r requirements.txt
python setup.py install
```
### 添加环境变量
Linux: `$ vim ~/.bashrc` 文件尾部追加
```
export STU_ID=0000000000
export STU_PWD=yourpassword
```
Windows:

![尴尬而不失礼貌的微笑](http://wx2.sinaimg.cn/large/005XSXmNgy1fdven80q9wj30k00j4q4i.jpg)
## 使用
### 学号密码验证
```Python
import tsxyScore
tsxyScore.is_tsxy_stu('1234567890', 'password')
```
# 说明
用到的包有几个坑, 等我 ~~自己安装~~ 有空的时候再单独写一下

## 找不到tesseract
安装好后，直接使用会提示错误 `FileNotFoundError: [Errno 2] No such file or directory: 'tesseract'`  
Ubuntu中使用`sudo apt-get install tesseract-ocr`安装即可

# 测试
```
python -m unittest discover -s /path/to/tsxyScore/tests -v -f
```

# QA
Q: 如果唐山学院的教务系统升级了, 那这个包是不是完全不能用了?  
A: 对啊

Q:不会用怎么办?  
A:还真有别人用?
