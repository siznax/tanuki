"""
tanuki views
"""
__author__ = "siznax"
__version__ = 2012

from flask import Flask, make_response, render_template, \
    request, redirect, url_for

app = Flask(__name__)
app.config.from_envvar('TANUKI_CONFIG', silent=False)
# print app.config

from lib import Tanuki
tanuki = Tanuki( app.config )

@app.route('/')
def index():
    entries = tanuki.entries()
    if not entries:
        msg = "<h1>Unbelievable. No entries yet.</h1>"
    else:
        msg = "%d entries" % ( len(entries) )
    return render_template( 'index.html', 
                            entries=entries,
                            tag_set=tanuki.tag_set(),
                            msg=msg )

@app.route('/entry/<_id>')
def entry(_id):
    entry = tanuki.entry( _id, True )
    if not entry:
        return redirect( url_for( 'index' ) )
    return render_template('index.html', 
                           entries=[ entry ], 
                           home=tanuki.home() )

@app.route('/dated/<date>')
def dated(date):
    return tanuki.entries_dated( date )

@app.route('/tagged/<tag>')
def tagged(tag):
    return tanuki.entries_tagged( tag )

@app.route('/new')
def new():
    return tanuki.new()

@app.route('/store', methods=['POST'])
def store():
    return tanuki.upsert( request )

@app.route('/edit/<_id>')
def edit(_id):
    tanuki.mode = 'edit' # possibly LAME
    entry = tanuki.entry( _id )
    tanuki.mode = None
    return render_template( 'edit.html', 
                            entry=entry ) 

@app.route('/delete', methods=['POST'])
def delete():
    tanuki.delete( request['entry_id'] )
    return redirect(url_for('index'))

@app.route('/confirm/<_id>')
def confirm(_id):
    return render_template('confirm.html', 
                           entry=tanuki.entry(_id) )


@app.before_request
def before_request():
    tanuki.connect()

@app.teardown_request
def teardown_request(exception):
    tanuki.con.close()


if __name__ == '__main__':
    app.run(debug=True, port=5001)
