Usage:

    cd ~/code
    fork or clone http://github.com/siznax/tanuki
    cd tanuki
    sqlite3 tanuki.db < schema.sql
    emacs CONFIG
        DATABASE = $HOME"/code/tanuki/tanuki.db"
        DEBUG = True
        SECRET_KEY = COMPLEX_RANDOM_STRING
        USERNAME = 'admin'
        PASSWORD = 'default'
        WRITE_HOST = 'localhost:5001'
        STYLESHEET = '/static/light.css'
    python views.py

Recommended:

    (python) virtualenv

Screens:

![](http://archive.org/download/siznax-screens/tanuki1.png)

![](http://archive.org/download/siznax-screens/tanuki2.png)

![](http://archive.org/download/siznax-screens/tanuki3.png)

![](http://archive.org/download/siznax-screens/tanuki4.png)

![](http://archive.org/download/siznax-screens/tanuki5.png)

Tanuki (raccoon) icon used with permission of 
[artrelatedblog.wordpress.com](http://artrelatedblog.wordpress.com/2012/08/06/new-pixel-art-avatar/).

