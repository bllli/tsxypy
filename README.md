# tsxyScore
tsxyScore是一个基于Python3的唐山学院教务系统爬虫

只做好"获取教务系统的信息"这一件事
## QA
Q: 如果唐山学院的教务系统升级了, 那这个包是不是完全不能用了?  
A: 对!啊!
# Usage
## 安装
```bash
git clone https://github.com/bllli/tsxyScore
cd tsxyScore
python3 setup.py install
```
## 使用
### 导入包
```Python
import tsxyScore
```
### 学号密码验证
```Python
tsxyScore.is_tsxy_stu('1234567890', 'password')
```
# 说明
用到的包有几个坑, 等我 ~~自己安装~~ 有空的时候再单独写一下

## 找不到tesseract
安装好后，直接使用会提示错误 `FileNotFoundError: [Errno 2] No such file or directory: 'tesseract'`  
Ubuntu中使用`sudo apt-get install tesseract-ocr`安装即可
