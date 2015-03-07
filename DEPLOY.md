DEPLOY
======

```root
# lsb_release -a
No LSB modules are available.
Distributor ID:	Ubuntu
Description:	Ubuntu 14.04 LTS
Release:	14.04
Codename:	trusty
```


Apache2 on Ubuntu
-----------------

```root
$ su -
# apt-get install apache2 libapache2-mod-wsgi
# apt-get install python-dev python-lxml
# apt-get install libxml2-dev libxslt-dev libncurses5-dev zlib1g-dev
# apt-get install nodejs nodejs-dev npm
# apt-get install python-virtualenv virtualenvwrapper
# npm install -g bower

# mkdir /var/www/tanuki
# cd /var/www/tanuki
# git clone tanuki
# mkvirtualenv /var/www/tanuki/tanuki/env
# source tanuki/env/bin/activate
(env)# pip install -r tanuki/requirements.txt
(env)# cd tanuki
(env)# bower install

# chgrp -R www-data /var/www/tanuki
# chown -R www-data /var/www/tanuki
```


Create WSGIScript
-----------------

/var/www/tanuki/app.wsgi:

```python
activate_this = '/var/www/tanuki/tanuki/env/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

import sys,os
sys.path.insert( 0, '/var/www/tanuki' )
os.chdir( '/var/www/tanuki' )

from tanuki import app as application
```


Create site config
------------------

/etc/apache2/sites-available/tanuki.conf:

```
<VirtualHost *:80>
    ServerName tanuki.siznax.net
    <Directory /var/www/tanuki>
        WSGIProcessGroup tanuki
        WSGIApplicationGroup %{GLOBAL}
        Order deny,allow
        Allow from all
    </Directory>
    WSGIDaemonProcess tanuki user=www-data group=www-data threads=5
    WSGIScriptAlias / /var/www/tanuki/app.wsgi
</VirtualHost>
```


Enable site and reload
----------------------

```root
# a2ensite tanuki
# service apache2 reload
```


@siznax
