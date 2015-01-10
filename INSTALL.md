Install tanuki!
================================================================

Clone tanuki:

```shell
$ git clone https://github.com/siznax/tanuki.git
```


Install python dependencies:

```shell
$ mkvirtualenv tanuki tanuki/env
(tanuki)$ pip install -r requirements.txt
```


Install web dependencies (Bower TBD):

    tanuki/static/
      |
      '-> jquery.js
      '-> octicons/
      '-> prettify/
      '-> prettify/sunburst.css

```shell
$ curl -o tanuki/static/jquery <jquery-latest-min.js>

# octicons <https://octicons.github.com>
#    1. Download octicons
#    2. mv octicons tanuki/static/
#       You want {{tanuki/static/octicons/*.*}}

# google-code-prettify <https://code.google.com/p/google-code-prettify/>
#    1. Download minified JS and CSS and extract into /tmp
#    2. mv /tmp/google-code-prettify tanuki/static/prettify
#       You want {{tanuki/static/prettify/*.*}}
#    3. curl -o <sunburst-skin> tanuki/static/prettify
        You want {{tanuki/static/prettify/sunburst.css}}
```


Create a config file (e.g. <tt>tanuki/config</tt>) and (at least) add:

```shell
TITLE = "tanuki"
```

Add <tt>TANUKI_CONFIG</tt> to your environment (e.g. bash):

```shell
export TANUKI_CONFIG=tanuki/config
```


Create a database from the schema provided:

```shell
$ sqlite3 tanuki/tanuki.db < tanuki/schema.sql
```


_Optionally, you can put your database in a "cloud" &#x2601; to share
on all your computers, and to have a durable backup. Please keep in
mind, there is nothing in tanuki protecting your database. You can
point to it in your config file as {{DATABASE}}, or you can symlink
{{tanuki/tanuki.db}} (the default dbfile) to your Dropbox version:

```shell
$ mv tanuki/tanuki.db ~/Dropbox/tanuki.db    
$ ln -s ~/Dropbox/tanuki.db tanuki/tanuki.db
```


Create a flask app script outside of the tanuki module
(e.g. <tt>tanuki.py</tt>): 

```python
from tanuki import app
app.config.from_envvar('TANUKI_CONFIG', silent=False)
app.run(debug=True, port=5005)
```


## Startup

Start the tanuki app in the shell:

```shell
$ workon tanuki
(tanuki)$ python ~/sw/tanuki.py
```

Visit your tanuki in a web browser at: <http://localhost:5001>

You can try the demo to see what it's like to take notes in
[tanuki.siznax.net](http://tanuki.siznax.net/)

If you want to run tanuki as a WSGI module on your web server, see the
tips at [tanuki.siznax.net/help](http://tanuki.siznax.net/help)
