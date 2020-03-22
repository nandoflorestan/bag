#!/usr/bin/env python3

"""Installer for the "bag" Python package."""

# http://peak.telecommunity.com/DevCenter/setuptools#developer-s-guide
# from distutils.core import setup
from codecs import open
from setuptools import setup, find_packages

with open('README.rst', encoding='utf-8') as f:
    long_description = f.read()

dependencies = ['polib', 'argh']

setup(
    url='https://github.com/nandoflorestan/bag',
    name="bag",
    author='Nando Florestan',
    version='3.0.0',
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
    classifiers=[  # https://pypi.org/pypi?:action=list_classifiers
        "Development Status :: 5 - Production/Stable",
        'Environment :: Console',
        "Environment :: Other Environment",
        "Intended Audience :: Developers",
        'License :: OSI Approved :: MIT License',
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
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
