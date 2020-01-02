import sys
if sys.version_info < (3, 6):
    sys.exit("Only suppert >= 3.6 Python Version")

import re
import os
from codecs import open
from setuptools import setup, find_packages


here = os.path.abspath(os.path.dirname(__file__))


keywords = [
    "pipe operator",
    "syntax",
]


def get_version():
    with open("bramin/__init__.py") as f:
        for line in f.readlines():
            line = line.strip()
            m = re.match("__version__ ?= ?['\"]([^']+)['\"]", line)
            if m:
                ver = m.group(1)
                return ver
        raise IOError("Version information can not found.")


def get_long_description():
    return ""


def get_install_requires():
    requirements = []
    with open('requirements.txt') as f:
        for line in f:
            requirements.append(line.strip())
    return requirements


setup(
    name='bramin',
    version=get_version(),
    description='',
    long_description=get_long_description(),
    author='nanguage',
    author_email='nanguage@yahoo.com',
    url='https://github.com/Nanguage/bramin',
    keywords=keywords,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    package_dir={'bramin': 'bramin'},
    install_requires=get_install_requires(),
    license='BSD-3-Clause',
    classifiers=[
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
    ]
)
