#!/usr/bin/python
# -*- coding: utf-8 -*-

from setuptools import setup

extra = {}

from trac.util.dist import get_l10n_js_cmdclass
cmdclass = get_l10n_js_cmdclass()
if cmdclass:
    extra['cmdclass'] = cmdclass
    extra['message_extractors'] = {
        'HudsonTrac': [
            ('*.py', 'python', None),
            ('templates/*.html', 'genshi', None),
        ],
    }

setup(
    name = 'HudsonTrac',
    version = '0.12.0.6',
    author = "Ronald Tschalär",
    description = "Trac Plugin which adds Hudson build events to the timeline",
    maintainer = "Christian Boos",
    license = "BSD",
    keywords = "trac builds hudson",
    # use this to report bugs to 0.11 and 0.12 branches of this plugin:
    url = "http://github.com/cboos/trachacks-hudsontracplugin",
    # original was:
    #url = "http://trac-hacks.org/wiki/HudsonTracPlugin",

    packages = ['HudsonTrac'],
    package_data = {
        'HudsonTrac': [
            'htdocs/*.css', 'htdocs/*.gif', 'htdocs/*.js',
            'templates/*.html',
            'locale/*/LC_MESSAGES/*.mo', 'htdocs/hudsontrac/*.js',
        ],
    },
    entry_points = {
        'trac.plugins' : [ 'HudsonTrac = HudsonTrac.HudsonTracPlugin' ]
    },
    **extra
)
