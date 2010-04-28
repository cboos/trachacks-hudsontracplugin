#!/usr/bin/python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name = 'HudsonTrac',
    version = '0.11.0.3',
    author = "Ronald Tschalär",
    maintainer = "Christian Boos",
    description = "A trac plugin to add hudson build info to the trac timeline",
    license = "BSD",
    keywords = "trac builds hudson",
    # use this to report bugs to 0.11 and 0.12 branches of this plugin:
    url = "http://github.com/cboos/trachacks-hudsontracplugin",
    # original was:
    #url = "http://trac-hacks.org/wiki/HudsonTracPlugin",

    packages = ['HudsonTrac'],
    package_data = {
        'HudsonTrac' : ['htdocs/*.css', 'htdocs/*.gif']
    },
    entry_points = {
        'trac.plugins' : [ 'HudsonTrac = HudsonTrac.HudsonTracPlugin' ]
    }
)
