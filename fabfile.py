# (c) 2010 by Anton Korenyushkin

import os
import os.path

from fabric.api import *
from sphinx.application import Sphinx


def build_face():
    src_path = os.path.abspath('face')
    Sphinx(
        src_path,
        src_path,
        'build/face/dirhtml',
        'build/face/doctrees',
        'dirhtml').build()


def _prepare_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path)


def get_docs():
    if os.path.isdir('repos/docs'):
        local('cd repos/docs; git pull')
    else:
        _prepare_dir('repos')
        local('git clone git://github.com/akshell/docs.git repos/docs')


def build_docs(version):
    local('cd repos/docs; git checkout origin/' + version)
    src_path = os.path.abspath('repos/docs')
    build_path = 'build/docs' + version
    Sphinx(
        src_path,
        src_path,
        build_path + '/dirhtml',
        build_path + '/doctrees',
        'dirhtml',
        {
            'html_theme_path': [os.path.abspath('.')],
            'html_theme': 'theme',
            'html_theme_options': {'bars': 'true'},
        }).build()
