import os

from flask import request, redirect, url_for
from flask.ext.bower import Bower
from lib import Tanuki
from tanuki import app, settings

__author__ = "siznax"
__date__ = "Jan 2015"

app.config.from_object(settings.DefaultConfig)
if '/var/www/' in os.getcwd():
    app.config.from_object(settings.ProductionConfig)

Bower(app)
applib = Tanuki(app.config)


@app.before_request
def before_request():
    if '/static' not in request.path:
        applib.db_connect()
        applib.get_status()


@app.teardown_request
def teardown_request(exception):
    if '/static' not in request.path:
        applib.db_disconnect()


@app.route('/')
def index():
    return applib.render_index()


@app.route('/favicon.ico')
def favicon():
    return app.send_static_file("favicon.ico")


@app.route('/list')
def list():
    return applib.render_list()


@app.route('/updates')
def updates():
    return applib.render_list_by_updated()


@app.route('/new')
def new():
    return applib.render_new_form()


@app.route('/capture')
def capture():
    return applib.render_capture_form()


@app.route('/edit_capture', methods=['POST'])
def edit_capture():
    return applib.render_edit_capture_form(
        request.form['endpoint'],
        request.form['stype'],
        request.form['selector'])


@app.route('/store', methods=['POST'])
def store():
    return applib.upsert(request)


@app.route('/entry/<int:_id>')
def entry(_id):
    return applib.render_entry(_id)


@app.route('/edit/<int:_id>')
def edit(_id):
    return applib.render_edit_form(_id)


@app.route('/delete/<int:_id>')
def delete_form(_id):
    return applib.render_delete_form(_id)


@app.route('/delete', methods=['POST'])
def delete_entry():
    applib.delete_entry(request.form['entry_id'])
    return redirect(url_for('index'))


@app.route('/tags')
def show_tags():
    return applib.render_tags()


@app.route('/tagged/<tag>')
def show_tagged(tag):
    return applib.render_tagged(tag, None)


@app.route('/gallery/<tag>')
def show_tagged_gallery(tag):
    return applib.render_tagged_gallery(tag)


@app.route('/notag')
def notag():
    return applib.render_notags()


@app.route('/search')
def search():
    return applib.render_search_form()


@app.route('/found', methods=['GET'])
def found():
    return applib.render_search_results(request.args['terms'])


@app.route('/help')
def help():
    return applib.render_help()


@app.route('/help/<int:_id>')
def help_entry(_id):
    return applib.render_entry(_id)


@app.route('/help/edit/<int:_id>')
def help_edit_id(_id):
    return applib.render_edit_form(_id)


if __name__ == '__main__':
    app.run(debug=True, port=5001)
