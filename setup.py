#!/usr/bin/env python
# -*- coding: utf-8 -*-

# http://peak.telecommunity.com/DevCenter/setuptools#developer-s-guide
# from distutils.core import setup
from codecs import open
from sys import version_info
from setuptools import setup, find_packages

with open('README.rst', encoding='utf-8') as f:
    long_description = f.read()

dependencies = ['nine>=0.3.4', 'polib', 'argh']
if version_info[:2] < (3, 4):
    dependencies.append('pathlib')
if version_info[:2] == (2, 6):
    dependencies.append('ordereddict')

setup(
    url='https://github.com/nandoflorestan/bag',
    name="bag",
    author='Nando Florestan',
    version='1.1.1.dev1',
    license='MIT',
    # https://setuptools.readthedocs.io/en/latest/setuptools.html#using-find-packages
    packages=find_packages(exclude=["tests.*", 'tests']),
    include_package_data=True,
    author_email="nandoflorestan@gmail.com",
    description="A library for several purposes, including javascript i18n "
                "and stuff for the Pyramid web framework.",
    long_description=long_description,
    zip_safe=False,
    test_suite='tests',
    install_requires=dependencies,
    keywords=["python", 'pyramid', 'sqlalchemy', 'HTML', 'CSV',
                'translation', 'i18n', 'internationalization', 'file hash',
                'encoding', 'codecs', 'text', 'console'],
    classifiers=[  # http://pypi.python.org/pypi?:action=list_classifiers
        "Development Status :: 5 - Production/Stable",
        'Environment :: Console',
        "Environment :: Other Environment",
        "Intended Audience :: Developers",
        'License :: OSI Approved :: MIT License',
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        'Programming Language :: Python :: Implementation :: CPython',
        "Framework :: Pyramid",
        'Topic :: Database',
        "Topic :: Internet :: WWW/HTTP",
        'Topic :: Internet :: WWW/HTTP :: WSGI',
        'Topic :: Multimedia :: Graphics :: Graphics Conversion',
        "Topic :: Software Development :: Libraries :: Python Modules",
        'Topic :: Text Processing :: General',
    ],
    entry_points='''
[babel.extractors]
jquery_templates = bag.web.transecma:extract_jquery_templates

[console_scripts]
po2json = bag.web.transecma:po2json_command
reorder_po = bag.reorder_po:command
check_rst = bag.check_rst:command
delete_old_branches = bag.git.delete_old_branches:command
''',
)
