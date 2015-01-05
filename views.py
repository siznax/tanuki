__author__ = "siznax"
__date__ = "Jan 2015"

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
        tanuki.db_connect()
        tanuki.get_status()


@app.teardown_request
def teardown_request(exception):
    if '/static' not in request.path:
        tanuki.db_disconnect()


@app.route('/')
def index():
    return tanuki.render_index()


@app.route('/favicon.ico')
def favicon():
    return app.send_static_file("favicon.ico")


@app.route('/list')
def list():
    return tanuki.render_list()


@app.route('/new')
def new():
    return tanuki.render_new_form()


@app.route('/store', methods=['POST'])
def store():
    return tanuki.upsert(request)


@app.route('/entry/<int:_id>')
def entry(_id):
    return tanuki.render_entry(_id)


@app.route('/edit/<int:_id>')
def edit(_id):
    return tanuki.render_edit_form(_id)


@app.route('/delete/<int:_id>')
def delete_form(_id):
    return tanuki.render_delete_form(_id)


@app.route('/delete', methods=['POST'])
def delete_entry():
    tanuki.delete(request.form['entry_id'])
    return redirect(url_for('index'))


@app.route('/tags')
def tags():
    return tanuki.render_tags()


@app.route('/tagged/<tag>')
def tagged(tag):
    return tanuki.render_tagged(tag, None)


@app.route('/tagged/<tag>/v:<view>')
def tagged_view(tag, view):
    return tanuki.render_tagged(tag, view)


@app.route('/notag')
def notag():
    return tanuki.render_notags()


@app.route('/search')
def search():
    return tanuki.render_search_form()


@app.route('/found', methods=['GET'])
def found():
    return tanuki.render_search_results(request.args['terms'])


@app.route('/help')
def help():
    return tanuki.render_help()


@app.route('/help/<int:_id>')
def help_entry(_id):
    return tanuki.render_entry(_id)


@app.route('/help/edit/<int:_id>')
def help_edit_id(_id):
    return tanuki.render_edit_form(_id)


if __name__ == '__main__':
    app.run(debug=True, port=5001)
