from flask import Flask
app = Flask(__name__)
app.config.from_envvar('TANUKI_CONFIG', silent=False)
app.debug = app.config["DEBUG"]

import tanuki.views

# this package wants something external to run app
# see http://flask.pocoo.org/docs/patterns/packages/
