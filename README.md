Tanuki allows you to take private, media rich notes inside your web
browser. It was built for taking personal notes kept offline, but you
could easily deploy it online as a blog. Try the demo to see what it's
like. 

* Demo: [tanuki.siznax.net](http://tanuki.siznax.net/)
* Help: [tanuki.siznax.net/help](http://tanuki.siznax.net/help)


## Installation

Install tanuki

```shell
$ cd ~/sw   
$ git clone https://github.com/siznax/tanuki.git
```

Install dependencies:

```shell
$ mkvirtualenv flask    
(flask)$ pip install flask    
(flask)$ pip install markdown    
(flask)$ pip install lxml
```

Create a config file (e.g. <tt>~/sw/tanuki/CONFIG</tt>) and add (you could do more here):

```shell
TITLE = "tanuki"    
```

Add the following to your bashrc:

```shell
TANUKI_CONFIG=$HOME/sw/tanuki/CONFIG
```

Create a database from the schema provided:

```shell
$ sqlite3 tanuki.db < schema.sql
```

(optional) Put database in cloud to share on all your devices:

```shell
$ mv tanuki.db ~/Dropbox/tanuki.db    
$ ln -s ~/Dropbox/tanuki.db .
```

Create a flask app script outside of tanuki module (e.g. ~/sw/tanuki.py):

```python
from tanuki import app
app.config.from_envvar('TANUKI_CONFIG', silent=False)
app.run(debug=True, port=5005)
```

Startup tanuki

```shell
$ workon flask
(flask)$ python ~/sw/tanuki.py
```


Tanuki (raccoon) icon courtesy of
[artrelatedblog](http://artrelatedblog.wordpress.com/2012/08/06/new-pixel-art-avatar/).


@siznax
