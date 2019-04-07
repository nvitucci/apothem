#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = 'Nicola Vitucci'
SITENAME = 'APOTHEM'
SITESUBTITLE = 'Apache Project(s) of the month'
SITEURL = ''

PATH = 'content'

TIMEZONE = 'Europe/London'
DEFAULT_LANG = 'en'

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# Blogroll
LINKS = (('projects.apache.org', 'https://projects.apache.org'),)

ICONS = [
    ('github', 'https://github.com/nvitucci/apothem'),
    ('twitter', 'https://twitter.com/nvitucci'),
]

DEFAULT_PAGINATION = 4

# Uncomment following line if you want document-relative URLs when developing
#RELATIVE_URLS = True

THEME_TEMPLATES_OVERRIDES = ['templates']

STATIC_PATHS = ['images', 'extra/CNAME']
EXTRA_PATH_METADATA = {'extra/CNAME': {'path': 'CNAME'},}

# Theme-related settings
THEME = 'alchemy'

USE_FOLDER_AS_CATEGORY = True
DISPLAY_PAGES_ON_MENU = True
MAIN_MENU = True

SITEIMAGE = '/images/profile.svg width=180'
HIDE_AUTHORS = True