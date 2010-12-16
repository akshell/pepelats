import os
import sys
import site

old_sys_path = list(sys.path)
site.addsitedir('/akshell/envs/main/lib/python2.5/site-packages')
new_sys_path = []
for item in list(sys.path):
    if item not in old_sys_path:
        new_sys_path.append(item)
        sys.path.remove(item)
sys.path[:0] = new_sys_path

import django.core.handlers.wsgi

sys.stdout = sys.stderr
sys.path.append('/akshell')
os.environ['DJANGO_SETTINGS_MODULE'] = 'chatlanian.settings'
application = django.core.handlers.wsgi.WSGIHandler()
