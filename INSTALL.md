Install
================================================================

Clone tanuki:

```shell
$ git clone https://github.com/siznax/tanuki.git
```


Install Python dependencies (see [`requirements.txt`](https://github.com/siznax/tanuki/blob/master/requirements.txt)):

```shell
$ mkvirtualenv tanuki
(tanuki)$ pip install -r tanuki/requirements.txt
```


Install [bower](http://bower.io/) (JS/CSS) dependencies (see [`bower.json`](https://github.com/siznax/tanuki/blob/master/bower.json)):

```shell
(tanuki)$ npm install bower
(tanuki)$ cd tanuki
(tanuki)$ bower install
```


Create a database from the schema provided:

```shell
(tanuki)$ sqlite3 tanuki/tanuki.db < tanuki/schema.sql
```


_Optionally, you can put your database in the "cloud" &#x2601; to share
on all your computers, and to have a durable backup. Please keep in
mind, there is nothing in tanuki protecting your database. You can
point to it in `settings.py` as `DATABASE`:

```python
class DefaultConfig:
    DEBUG = True
    DATABASE = "/Users/<your-username>/Dropbox/tanuki.db"
```

_or you can symlink `tanuki/tanuki.db` (the default dbfile) to your Dropbox version:_

```shell
$ ln -s /Users/<your-username>/Dropbox/tanuki.db .
```


Create a startup script outside of the tanuki module (e.g. `tanuki.py`): 

```python
from tanuki import app
app.config.from_envvar('TANUKI_CONFIG', silent=False)
app.run(debug=True, port=5005)
```


Startup
-------

Start the tanuki app in the shell:

```shell
$ workon tanuki
(tanuki)$ python tanuki.py
```

Visit your _tanuki_ in a web browser at: <http://localhost:5001>

Enjoy!
