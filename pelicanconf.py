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
FEED_ALL_ATOM = 'feeds/all.atom.xml'
CATEGORY_FEED_ATOM = 'feeds/{slug}.atom.xml'
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# Blogroll
LINKS = (('projects.apache.org', 'https://projects.apache.org'),)

ICONS = [
    ('github', 'https://github.com/nvitucci/apothem'),
    ('twitter', 'https://twitter.com/nvitucci'),
    ('rss', FEED_ALL_ATOM),
]

DEFAULT_PAGINATION = 4

# Uncomment following line if you want document-relative URLs when developing
#RELATIVE_URLS = True

THEME_TEMPLATES_OVERRIDES = ['templates']

STATIC_PATHS = ['images', 'extra/CNAME', 'extra/robots.txt', 'extra/favicon.ico']
EXTRA_PATH_METADATA = {
    'extra/CNAME': {'path': 'CNAME'},
    'extra/robots.txt': {'path': 'robots.txt'},
    'extra/favicon.ico': {'path': 'favicon.ico'},
}

# Default value is ['index', 'tags', 'categories', 'authors', 'archives']
DIRECT_TEMPLATES = ['index', 'tags', 'categories', 'authors', 'archives', 'sitemap']
SITEMAP_SAVE_AS = 'sitemap.xml'

# Theme-related settings
THEME = 'alchemy'

USE_FOLDER_AS_CATEGORY = True
DISPLAY_PAGES_ON_MENU = True
MAIN_MENU = True

SITEIMAGE = '/images/profile.svg width=180'
HIDE_AUTHORS = True
