Install
================================================================

Clone tanuki:

```shell
$ git clone https://github.com/siznax/tanuki.git
```

You may need to install some of the following packages:

```root
$ su -
# apt-get install python-virtualenv virtualenvwrapper
# apt-get install python-dev python-lxml sqlite3
# apt-get install libxml2-dev libxslt-dev libncurses5-dev zlib1g-dev
# apt-get install nodejs nodejs-dev npm
```


Install Python dependencies (see [`requirements.txt`](https://github.com/siznax/tanuki/blob/master/requirements.txt)):

```shell
$ mkvirtualenv tanuki
(tanuki)$ pip install -r tanuki/requirements.txt
```


Install [bower](http://bower.io/) (JS/CSS) dependencies (see [`bower.json`](https://github.com/siznax/tanuki/blob/master/bower.json)):

```shell
(tanuki)$ npm install -g bower
(tanuki)$ cd tanuki
(tanuki)$ bower install
```


Create a database from the schema provided:

```shell
(tanuki)$ sqlite3 tanuki.db < schema.sql
```


_Optionally, you can put your database in the "cloud" &#x2601; to share
on all your computers, and to have a durable backup. Please keep in
mind, there is nothing in tanuki protecting your database. You can
point to it in `settings.py` as `DATABASE`:_

```python
class DefaultConfig:
    DEBUG = True
    DATABASE = "/Users/<your-username>/Dropbox/tanuki.db"
```

_or you can symlink `tanuki/tanuki.db` (the default dbfile) to your Dropbox version:_

```shell
(tanuki)$ ln -s /Users/<your-username>/Dropbox/tanuki.db .
```


Create a startup script outside of the tanuki module (e.g. `~/Code/tanuki.py`): 

```python
from tanuki import app
from tanuki import settings
app.config.from_object(settings.DefaultConfig)
app.run(port=5001)
```


Startup
-------

Start the tanuki app in the shell:

```shell
$ workon tanuki
(tanuki)$ python tanuki.py
 * Running on http://127.0.0.1:5001/
```

Visit your _tanuki_ in a web browser at: <http://localhost:5001>

Enjoy!
