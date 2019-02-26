from setuptools import setup
from setuptools import find_packages
import os
import glob

setup(
    name='Static',
    description='Simple template system for generating static sites',
    long_description='',
    author='Sheldon McGrandle',
    author_email='developer@8cylinder.com',
    url='https://github.com/8cylinder/static',
    version='0.1',
    packages=find_packages(where='src'),
    package_dir={'': 'static'},
    py_modules=[
        os.path.splitext(os.path.basename(path))[0]
        for path in glob.glob('src/*.py')],
    install_requires=[
        'Click',
    ],
    entry_points='''
        [console_scripts]
        static=cli:static
    ''',
)

## build source dist and wheel:
# python3 setup.py sdist bdist_wheel
## upload to pypi:
# twine upload dist/*
## install for dev:
# pip install --editable .

# pyinstaller tvol.spec

# future windows builds:
# python3 setup.py bdist_wininst
# python3 setup.py register sdist bdist_wininst upload
