#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name = 'mgrok',
    version = '0.1',
    author = 'Adam Georgiou',
    author_email = 'me@adamgeorgiou.com',
    description = ('Utility to grok concerts'),
    packages=find_packages('src'),
    package_dir = {'':'src'},
    install_requires = [
        'python-dateutil', # iso (+timezone) date parse
        'pytz',            # timezones
        'requests',        # nice http requests
        'scrapy',          # html scraping
        ],
)
