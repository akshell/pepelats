# (c) 2010-2011 by Anton Korenyushkin

import os
import os.path
import tempfile

from fabric.api import *
from sphinx.application import Sphinx


env.roledefs = {
    'com': ['akshell@akshell.com'],
    'test': ['akshell@akshell.test'],
}


_REPOS = {
    'docs': 'git://github.com/akshell/docs.git',
    'patsak': 'git@github.com:korenyushkin/patsak.git',
    'ecilop': 'git@github.com:korenyushkin/ecilop.git',
    'cappuccino': 'git@github.com:korenyushkin/cappuccino.git',
    'bespin': 'git@github.com:korenyushkin/bespin.git',
    'kappa': 'git@github.com:korenyushkin/kappa.git',
}


def update(name):
    path = 'repos/' + name
    if os.path.isdir(path):
        local('cd %s && git %s' % (path, 'fetch' if name == 'docs' else 'pull'))
    else:
        os.makedirs(path)
        local('git clone %s %s' % (_REPOS[name], path))


def _build_face():
    local('rm -rf build/face') # Sphinx recompiles face slowly
    src_path = os.path.abspath('face')
    Sphinx(
        src_path,
        src_path,
        'build/face/dirhtml',
        'build/face/doctrees',
        'dirhtml').build()
    local('cp face/index.html build/face/dirhtml/')


def _build_docs(version):
    local('cd repos/docs && git checkout origin/' + version)
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
            'html_theme_options': {'navigation': 'true'},
        }).build()


def _build_patsak():
    local('cd repos/patsak && scons patsak')


def _build_ecilop():
    local('cd repos/ecilop && make ecilop')


def _build_kappa():
    local('cd repos/cappuccino && jake release')
    local('rm -rf repos/kappa/Frameworks')
    local('mv repos/cappuccino/Build/Release repos/kappa/Frameworks')
    local('cd repos/kappa && jake Flattened')
    local('cd repos/bespin && python dryice.py -j compressors/compiler.jar manifest.json')
    local('mv repos/bespin/build repos/kappa/Build/Flattened/Resources/Bespin')


def build(name, *args):
    globals()['_build_' + name](*args)


def _send_face():
    local('rsync -zr build/face/dirhtml/ %s:static' % env.host_string)


def _send_docs(version):
    local('rsync -zr --del build/docs%s/dirhtml/ %s:static/docs/%s' % (version, env.host_string, version))


def _send_patsak():
    local('rsync -z repos/patsak/exe/common/patsak %s:bin/patsak' % env.host_string)
    local('rsync -zr --del repos/patsak/lib/ %s:lib' % env.host_string)


def _send_ecilop():
    local('rsync -z repos/ecilop/ecilop %s:bin/ecilop' % env.host_string)


def _send_kappa():
    local('rsync -zr repos/kappa/Build/Flattened/ %s:static/kappa/next' % env.host_string)
    run('cd static/kappa && next=$(expr $(readlink curr) + 1) && mv next $next && rm curr && ln -s $next curr')


def _send_etc():
    local('rsync -zr etc/ %s:etc' % env.host_string)
    local('rsync -z repos/patsak/patsak.sql %s:etc/patsak.sql' % env.host_string)
    if env.host != 'akshell.com':
        run(r'sed -i -e "s/akshell\(.*\)com/%s/g" etc/*' % env.host.replace('.', r'\1'))


def send(name, *args):
    globals()['_send_' + name](*args)


def refresh(name):
    if name == 'ecilop':
        run('killall ecilop')
    elif name == 'chatlanian':
        run('touch etc/wsgi.py')
    else:
        sudo('/etc/init.d/%s reload' % name)


def deploy(name, *args):
    if name == 'chatlanian':
        run('cd chatlanian && git pull')
        refresh('chatlanian')
        return
    if name == 'kappa':
        update('cappuccino')
        update('bespin')
    if name != 'face':
        update(name)
    build(name, *args)
    send(name, *args)
    if name in ('ecilop', 'patsak'):
        refresh('ecilop')
    elif name == 'kappa':
        refresh('chatlanian')


def bootstrap():
    sudo('apt-get -y install libpq-dev curl libcurl3-dev libexpat-dev')

    run('''
mkdir work
cd work
wget http://kernel.org/pub/software/scm/git/git-1.7.3.4.tar.bz2
tar -xjf git-1.7.3.4.tar.bz2
rm git-1.7.3.4.tar.bz2
cd git-1.7.3.4
export NO_TCLTK=1
./configure
make
''')
    sudo('cd work/git-1.7.3.4 && make install')
    run('git config --global core.askpass true')

    sudo('''
curl http://repo.varnish-cache.org/debian/GPG-key.txt | apt-key add -

cat <<EOF >>/etc/apt/sources.list
deb http://repo.varnish-cache.org/debian/ lenny varnish-2.1
deb http://backports.debian.org/debian-backports lenny-backports main
EOF

cat <<EOF >/etc/apt/preferences
Package: *
Pin: release a=lenny-backports
Pin-Priority: 200
EOF

apt-get update
''')

    sudo('apt-get -y install varnish')
    sudo('apt-get -y -t lenny-backports install nginx git-core')
    sudo('pip install virtualenv virtualenvwrapper')
    run('''
mkdir envs

cat <<EOF >.bashrc
export HISTCONTROL=ignoreboth
export HISTSIZE=10000
export HISTFILESIZE=20000
export PS1='\e[0;%dm\u@\H:\w\e[0m$ '
export WORKON_HOME=~/envs
source /usr/bin/virtualenvwrapper.sh
alias ls='ls --color=auto'
EOF

cat <<EOF >.inputrc
"\ep": history-search-backward
"\en": history-search-forward
EOF
''' % (31 if env.host == 'akshell.com' else 32))

    run('mkdir -p static/docs static/kappa bin; ln -s 0 static/kappa/curr')
    deploy('face')
    deploy('docs', '0.1')
    deploy('docs', '0.2')
    deploy('docs', '0.3')
    deploy('kappa')
    deploy('patsak')
    deploy('ecilop')
    _send_etc()

    run('ssh-keyscan -t rsa github.com >> .ssh/known_hosts')
    run('git clone git@github.com:korenyushkin/chatlanian.git')
    sudo('sudo -u postgres createuser -s akshell')
    run('createdb akshell')

    run('''
mkvirtualenv --no-site-packages main
pip install argparse django django-piston django-sentry dulwich psycopg2 simplejson
cd chatlanian
./manage.py syncdb --noinput
echo "import paths; paths.create_paths()" | ./manage.py shell
''')

    sudo('chatlanian/gen_drafts.sh akshell drafts 10000 10500 && ln -s 10000 drafts/curr')

    run('''
psql ak -c "COPY auth_user TO STDOUT" | psql -c "COPY auth_user FROM STDIN"
psql -c "UPDATE auth_user SET username = replace(username, ' ', '-')"
workon main
cat <<EOF | chatlanian/manage.py shell
from django.contrib.auth.models import User
from managers import create_dev
for user in User.objects.all():
    create_dev(user.username)

EOF
''')

    run('''
psql ak -c "COPY (SELECT name FROM main_app) TO STDOUT" |
while read name; do
    touch data/domains/$name.%s
done
chmod -R 777 data/domains
''' % env.host)

    sudo('''
echo "ec:23:respawn:/usr/bin/sudo -u akshell /akshell/bin/ecilop -c /akshell/etc/ecilop.conf" >> /etc/inittab
telinit q

ln -s /akshell/etc/nginx.conf /etc/nginx/sites-available/%(host)s
ln -s /etc/nginx/sites-available/%(host)s /etc/nginx/sites-enabled/%(host)s
rm /etc/nginx/sites-enabled/default
ln -sf /akshell/etc/apache.conf /etc/apache2/sites-available/%(host)s
ln -sf /akshell/etc/varnish.vcl /etc/varnish/default.vcl

cat <<EOF >/etc/apache2/ports.conf
NameVirtualHost *:8000
Listen 127.0.0.1:8000
EOF

/etc/init.d/apache2 restart
/etc/init.d/varnish restart
/etc/init.d/nginx restart
''' % {'host': env.host})
