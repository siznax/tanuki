Tanuki allows you to take private, media rich notes inside your web
browser. It was built for taking personal notes kept offline, but you
could easily deploy it as a blog.

* Demo: [tanuki.siznax.net](http://tanuki.siznax.net/)
* Help: [tanuki.siznax.net/help](http://tanuki.siznax.net/help)
* Dependencies:
[python](https://python.org),
[flask](http://flask.pocoo.org/),
[sqlite](http://www.sqlite.org/),
[markdown](http://daringfireball.net/projects/markdown/),
[lxml](http://lxml.de/)
* Recommended:
[virtualenvwrapper](http://virtualenvwrapper.readthedocs.org/), 
[dropbox](https://www.dropbox.com/)

## Installation

Install dependencies:

```shell
$ mkvirtualenv flask    
(flask)$ pip install flask    
(flask)$ pip install markdown    
(flask)$ pip install lxml
```

Clone tanuki:

```shell
$ cd ~/sw   
$ git clone https://github.com/siznax/tanuki.git
```

Create a config file (e.g. <tt>~/sw/tanuki/CONFIG</tt>) and (at least) add:

```shell
TITLE = "tanuki"    
```

Point to your new config file in your shell config (e.g. <tt>.bashrc</tt>):

```shell
export TANUKI_CONFIG=$HOME/sw/tanuki/CONFIG
```

Create a database from the schema provided:

```shell
$ sqlite3 tanuki.db < schema.sql
```

Optionally, you can put your database in a "cloud" &#x2601; to share on all your computers, and to have a durable backup. Please keep in mind, there is nothing in tanuki protecting your database.

```shell
$ mv tanuki.db ~/Dropbox/tanuki.db    
$ ln -s ~/Dropbox/tanuki.db .
```

Create a flask app script outside of the tanuki module (e.g. <tt>~/sw/tanuki.py</tt>):

```python
from tanuki import app
app.config.from_envvar('TANUKI_CONFIG', silent=False)
app.run(debug=True, port=5005)
```

### Startup

Start the tanuki app in the shell:

```shell
$ workon flask
(flask)$ python ~/sw/tanuki.py
```

Visit your tanuki in a web browser at: <http://localhost:5001>

You can try the demo to see what it's like to take notes in [tanuki.siznax.net](http://tanuki.siznax.net/)

If you want to run tanuki as a WSGI module on your web server, see the tips at [tanuki.siznax.net/help](http://tanuki.siznax.net/help)

#### Thanks

Tanuki (raccoon) icon courtesy of
[artrelatedblog](http://artrelatedblog.wordpress.com/2012/08/06/new-pixel-art-avatar/).
