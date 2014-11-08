Tanuki was built for taking personal notes kept offline, but you could
easily deploy it online as a blog. Try the demo to see what it's like.

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

2. create and specify config file

    $HOME/sw/tanuki/CONFIG:    
    TITLE = "tanuki"

    $BASHRC:    
    TANUKI_CONFIG=$HOME/sw/tanuki/CONFIG

3. create and specify database

    $ sqlite3 tanuki.db < schema.sql

4. (optional) put database in cloud

    $ mv tanuki.db ~/Dropbox/tanuki.db    
    $ ln -s ~/Dropbox/tanuki.db .

5. create run file

    $ cd ~/sw    
    $ emacs tanuki.py:    

    from tanuki import app
    app.config.from_envvar('TANUKI_CONFIG', silent=False)
    app.run(debug=True, port=5005)

6. startup tanuki

    $ python tanuki.py


Tanuki (raccoon) icon courtesy of
[artrelatedblog](http://artrelatedblog.wordpress.com/2012/08/06/new-pixel-art-avatar/).

----
@siznax