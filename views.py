"""
tanuki views
"""
__author__ = "siznax"
__version__ = 2012

from flask import Flask,render_template,request,redirect,url_for

# app = Flask(__name__)
from tanuki import app
app.config.from_envvar('TANUKI_CONFIG', silent=False)

from lib import Tanuki
tanuki = Tanuki( app.config )

@app.route('/favicon.ico')
def favicon():
    return app.send_static_file("favicon.ico")

@app.route('/',defaults={'mask':'umask'})
@app.route('/<mask>')
def index( mask ):
    tanuki.umask( mask )
    return tanuki.index()

@app.route('/help')
def help():
    return tanuki.help()

@app.route('/help/<int:_id>')
def help_entry( _id ):
    return tanuki.singleton( _id )

@app.route('/help/edit/<int:_id>')
def help_edit( _id ):
    return tanuki.edit( _id )

@app.route('/page/<int:page>')
def pager(page):
    if page==0:
        return redirect( url_for('index') )
    return tanuki.stream( page )

@app.route('/list')
def list():
    tanuki.umask( 'umask' )
    return tanuki.list()

@app.route('/tags')
def tags():
    tanuki.umask( 'umask' )
    return tanuki.tags()

@app.route('/tags/')
def tags_redirect():
    return redirect( url_for( 'tags' ) )

@app.route('/tags/<mask>')
def tags_mask( mask ):
    tanuki.umask( mask )
    return tanuki.tags()

@app.route('/tagged/<tag>')
def tagged_tag( tag ):
    return tanuki.tagged( tag,None )

# this seems lame
@app.route('/tagged/<tag>/')
def tagged_tag_redirect( tag ):
    return redirect( url_for( 'tagged_tag', tag=tag ) )

@app.route('/tagged/<tag>/p:<mask>')
def tagged_mask( tag, mask ):
    tanuki.umask( mask )
    return tanuki.tagged( tag,None )

@app.route('/tagged/<tag>/v:<view>')
def tagged_view( tag, view ):
    return tanuki.tagged( tag, view )

@app.route('/tagged/<tag>/p:<mask>/v:<view>')
def tagged_mask_view( tag, mask, view ):
    tanuki.umask( mask )
    return tanuki.tagged( tag, view )

@app.route('/notag',defaults={'mask':'umask'})
@app.route('/notag/<mask>')
def notag( mask ):
    tanuki.umask( mask )
    return tanuki.notag()

@app.route('/entry/<int:_id>')
def entry(_id):
    return tanuki.singleton( _id )

@app.route('/dated/<date>')
def dated(date):
    return tanuki.dated( date )

@app.route('/search')
def search():
    return tanuki.search()

@app.route('/matched', methods=['GET'] )
def matched():
    return tanuki.matched( request.args['terms'] )

@app.route('/new')
def new():
    return tanuki.new()

@app.route('/store', methods=['POST'])
def store():
    return tanuki.upsert( request )

@app.route('/edit/<_id>')
def edit(_id):
    return tanuki.edit( _id )

@app.route('/confirm/<_id>')
def confirm(_id):
    return tanuki.confirm( _id )

@app.route('/delete', methods=['POST'])
def delete():
    tanuki.delete( request.form['entry_id'] )
    return redirect(url_for('index'))

@app.before_request
def before_request():
    if '/static' not in request.path:
        tanuki.connect()

@app.teardown_request
def teardown_request(exception):
    if '/static' not in request.path:
        if tanuki.DEBUG:
            print "+ TANUKI closing DB %s" % ( tanuki.con.total_changes )
        tanuki.con.close()


if __name__ == '__main__':
    app.run(debug=True, port=5001)
