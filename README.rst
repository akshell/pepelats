================
Akshell Deployer
================

Bootstrapping Plan
==================

* backup the linode;
* apt-get update;
* apt-get upgrade;
* create the akshell user via adduser --home /akshell akshell;
* add him to sudoers via visudo;
* set up his .ssh/;
* add his public SSH key to github;
* remove sys.path.append('/ak') from /usr/lib/python2.5/sitecustomize.py;
* write new replace.py into /usr/local/bin/replace;
* make it executable;
* run in pepelats: fab -R com bootstrap;
* run in old chatlanian: fab -R combat chatlanian send replace.
