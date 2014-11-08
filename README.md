Tanuki allows you to take private, media rich notes inside your web
browser. It was built for taking personal notes kept offline, but you
could easily deploy it online as a blog. Try the demo to see what it's
like. 

* Demo: [tanuki.siznax.net](http://tanuki.siznax.net/)
* Help: [tanuki.siznax.net/help](http://tanuki.siznax.net/help)


## Configuration

1. install tanuki

    $ cd ~/sw   
    $ git clone https://github.com/siznax/tanuki.git

1. install dependencies

    $ mkvirtualenv flask    
    (flask)$ pip install flask    
    (flask)$ pip install markdown    
    (flask)$ pip install lxml

2. create a config file (e.g. {{~/sw/tanuki/CONFIG}}) and add:

    TITLE = "tanuki"    

3. add the following to your bashrc:

    TANUKI_CONFIG=$HOME/sw/tanuki/CONFIG

4. create a database from the schema provided:

    $ sqlite3 tanuki.db < schema.sql

5. (optional) put database in cloud to share on all your devices:

    $ mv tanuki.db ~/Dropbox/tanuki.db    
    $ ln -s ~/Dropbox/tanuki.db .

6. create a flask app script outside of tanuki module (e.g. ~/sw/tanuki.py):

    from tanuki import app
    app.config.from_envvar('TANUKI_CONFIG', silent=False)
    app.run(debug=True, port=5005)

6. startup tanuki

    $ workon flask
    (flask)$ python ~/sw/tanuki.py


Tanuki (raccoon) icon courtesy of
[artrelatedblog](http://artrelatedblog.wordpress.com/2012/08/06/new-pixel-art-avatar/).


@siznax