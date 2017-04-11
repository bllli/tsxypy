from setuptools import setup, find_packages

setup(
    name='tsxyScore',
    version='0.0.1',
    keywords=('Python3', 'TSXY'),
    description='',
    license='MIT License',
    install_requires=['beautifulsoup4>=4.5.3',
                      'bs4>=0.0.1',
                      'Pillow>=4.1.0',
                      'pytesseract>=0.1.6',
                      'requests>=2.13.0'],
    author='bllli',
    author_email='hello@bllli.cn',

    packages=find_packages(),
    platforms='any',
)
