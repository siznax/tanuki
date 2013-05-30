Demo:

    [tanuki.siznax.net](http://tanuki.siznax.net/)

Config:

    TITLE      = ANYTHING_YOU_WANT
    DATABASE   = $HOME"/code/tanuki/tanuki.db"
    DEBUG      = True
    SECRET_KEY = COMPLEX_RANDOM_STRING
    USERNAME   = REAL_USERNAME
    PASSWORD   = REAL_PASSWORD
    STYLESHEET = ANYTHING_YOU_WANT

Usage:

    cd ~/code
    fork or clone http://github.com/siznax/tanuki
    cd tanuki
    sqlite3 tanuki.db < schema.sql
    export TANUKI_CONFIG=`pwd`"/CONFIG"
    python views.py

Tanuki (raccoon) icon used with permission of 
[artrelatedblog.wordpress.com](http://artrelatedblog.wordpress.com/2012/08/06/new-pixel-art-avatar/).

