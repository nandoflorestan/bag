#!/usr/bin/env python
# -*- coding: utf-8 -*-

# http://peak.telecommunity.com/DevCenter/setuptools#developer-s-guide
# from distutils.core import setup
from setuptools import setup, find_packages
import bag

setup(
    url = bag.__url__,
    name = "bag",
    author = bag.__author__,
    version = bag.__version__,
    license = bag.__license__,
    packages = find_packages(),
    include_package_data=True,
    author_email = "nandoflorestan@gmail.com",
    download_url = "http://code.google.com/p/bag/downloads/list",
    description = "A library for many purposes",
    zip_safe = False,
    test_suite='bag.tests',
    keywords = ["python", 'sqlalchemy', 'text', 'HTML', 'CSV',
                'translation', 'file hash', 'encoding', 'codecs',
                'console'],
    classifiers = [ # http://pypi.python.org/pypi?:action=list_classifiers
        "Development Status :: 5 - Production/Stable",
        'Environment :: Console',
        "Environment :: Other Environment",
        "Intended Audience :: Developers",
        'License :: OSI Approved :: BSD License',
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        'Topic :: Database',
        'Topic :: Multimedia :: Graphics :: Graphics Conversion',
        "Topic :: Software Development :: Libraries :: Python Modules",
        'Topic :: Text Processing :: General',
        ],
    long_description = bag.__long_description__,
)
