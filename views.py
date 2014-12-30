__author__ = "siznax"
__version__ = 2014

# from flask import Flask
# app = Flask(__name__)

from flask import request, redirect, url_for
from lib import Tanuki
from tanuki import app


app.config.from_envvar('TANUKI_CONFIG', silent=False)
tanuki = Tanuki(app.config)


@app.before_request
def before_request():
    if '/static' not in request.path:
        tanuki.connect()


@app.teardown_request
def teardown_request(exception):
    if '/static' not in request.path:
        if tanuki.DEBUG:
            print "+ TANUKI closing DB %s" % tanuki.con.total_changes
        tanuki.con.close()


@app.route('/')
def index():
    return tanuki.index()


@app.route('/favicon.ico')
def favicon():
    return app.send_static_file("favicon.ico")


@app.route('/list')
def list():
    return tanuki.list()


@app.route('/new')
def new():
    return tanuki.new()


@app.route('/store', methods=['POST'])
def store():
    return tanuki.upsert(request)


@app.route('/entry/<int:_id>')
def entry(_id):
    return tanuki.singleton(_id)


@app.route('/edit/<int:_id>')
def edit(_id):
    return tanuki.edit(_id)


@app.route('/confirm/<int:_id>')
def confirm(_id):
    return tanuki.confirm(_id)


@app.route('/delete', methods=['POST'])
def delete():
    tanuki.delete(request.form['entry_id'])
    return redirect(url_for('index'))


@app.route('/tags')
def tags():
    return tanuki.tags()


@app.route('/tagged/<tag>')
def tagged(tag):
    return tanuki.tagged(tag, None)


@app.route('/tagged/<tag>/v:<view>')
def tagged_view(tag, view):
    return tanuki.tagged(tag, view)


@app.route('/notag')
def notag():
    return tanuki.notag()


@app.route('/search')
def search():
    return tanuki.search()


@app.route('/found', methods=['GET'])
def found():
    return tanuki.found(request.args['terms'])


@app.route('/help')
def help():
    return tanuki.help()


@app.route('/help/<int:_id>')
def help_entry(_id):
    return tanuki.singleton(_id)


@app.route('/help/edit/<int:_id>')
def help_edit_id(_id):
    return tanuki.edit(_id)


if __name__ == '__main__':
    app.run(debug=True, port=5001)
