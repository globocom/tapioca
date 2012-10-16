#!/usr/bin/python
# -*- coding: utf-8 -*-

from glob import glob
from setuptools import setup

__version__ = '0.1.10'


setup(
    name = 'tapioca',
    version = __version__,
    description = "Tapioca is a small and flexible micro-framework on top of "\
            "Tornado. It provides a simpler way to create RESTful API's.",
    long_description = """
        Tapioca is a small and flexible micro-framework on top of Tornado.
        It provides a simpler way to create RESTful API's.
    """,
    keywords = 'restful rest api tornado',
    author = 'globo.com',
    author_email = 'lambda@corp.globo.com',
    url = 'https://github.com/globocom/tapioca',
    license = 'MIT',
    classifiers = ['Development Status :: 4 - Beta',
                 'Intended Audience :: Developers',
                 'License :: OSI Approved :: MIT License',
                 'Natural Language :: English',
                 'Operating System :: MacOS',
                 'Operating System :: POSIX :: Linux',
                 'Programming Language :: Python :: 2.6',
    ],
    packages = ['tapioca'],
    package_dir = {"tapioca": "tapioca"},
    include_package_data = True,
    data_files = [('templates', [
        'tapioca/templates/base.html',
        'tapioca/templates/tapioca/resource.html',
    ])],
    install_requires=[
      "tornado>=2.4",
      "mimeparse>=0.1.3"
    ]
)
