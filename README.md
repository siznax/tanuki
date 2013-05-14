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
    export TANUKI_CONFIG=`pwd`"/CONFIG"
    python views.py

Recommended:

    (python) virtualenv

Screens:

<div id=tanuki_screens>
<table border=0>
<tr>
<td><a target=blank href="http://archive.org/download/siznax-screens/tanuki006.png"><img src="http://archive.org/download/siznax-screens/tanuki006.png" width="240"></a></td>
<td><a target=blank href="http://archive.org/download/siznax-screens/tanuki007.png"><img src="http://archive.org/download/siznax-screens/tanuki007.png" width="240"></a></td>
<td><a target=blank href="http://archive.org/download/siznax-screens/tanuki008.png"><img src="http://archive.org/download/siznax-screens/tanuki008.png" width="240"></a></td>
<tr>
<td><a target=blank href="http://archive.org/download/siznax-screens/tanuki009.png"><img src="http://archive.org/download/siznax-screens/tanuki009.png" width="240"></a></td>
<td><a target=blank href="http://archive.org/download/siznax-screens/tanuki010.png"><img src="http://archive.org/download/siznax-screens/tanuki010.png" width="240"></a></td>
<td><a target=blank href="http://archive.org/download/siznax-screens/tanuki011.png"><img src="http://archive.org/download/siznax-screens/tanuki011.png" width="240"></a></td>
<tr>
<td><a target=blank href="http://archive.org/download/siznax-screens/tanuki012.png"><img src="http://archive.org/download/siznax-screens/tanuki012.png" width="240"></a></td>
<td><a target=blank href="http://archive.org/download/siznax-screens/tanuki013.png"><img src="http://archive.org/download/siznax-screens/tanuki013.png" width="240"></a></td>
</table>
</div>

<style>#tanuki_screens table,#tanuki_screens tr,#tanuki_screens td { border:none;background:none; }</style>

Tanuki (raccoon) icon used with permission of 
[artrelatedblog.wordpress.com](http://artrelatedblog.wordpress.com/2012/08/06/new-pixel-art-avatar/).

