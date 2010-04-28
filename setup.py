#!/usr/bin/python
# -*- coding: utf-8 -*-

from setuptools import setup

extra = {}

try:
    import babel
    extra['message_extractors'] = {
        'HudsonTrac': [
            ('*.py', 'python', None),
        ],
    }
except ImportError:
    pass
                
setup(
    name = 'HudsonTrac',
    version = '0.12.0.4',
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
        'HudsonTrac' : ['htdocs/*.css', 'htdocs/*.gif',
                        'locale/*.*', 'locale/*/LC_MESSAGES/*.*'],
    },
    entry_points = {
        'trac.plugins' : [ 'HudsonTrac = HudsonTrac.HudsonTracPlugin' ]
    },
    **extra
)
