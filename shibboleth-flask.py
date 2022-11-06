'''
Shibboleth Web Interface
(c) J Chaim Reus 2022

run using:
export FLASK_APP=server && export FLASK_ENV=development && flask --app shibboleth-flask run

or

python shibboleth-flask.py

The website should run at localhost:3000
'''

import sys
import os
import json
from pathlib import Path
import numpy as np
import flask
from werkzeug.utils import secure_filename
from datetime import datetime

app = flask.Flask(__name__)

SERVE_HOST = '0.0.0.0'

# Serve Static Files
@app.route("/<path:name>")
def fetch_static(name):
    return flask.send_from_directory(
        "static/", name, as_attachment=False
    )

#create our "home" route using the "index.html" page
@app.route('/', methods = ['GET'])
def home():
    #return render_template('index.html', names=["The Voice of Authority","The Voice of Reason"], wishes=["I love you...","What is love?"], message="Test Message..")
    return flask.render_template('index.html', names=["",""], wishes=["",""], message="")


# Set a post method to send text data updates.
@app.route('/', methods = ['POST'])
def recv_text():
    print("recv_text() with", flask.request.json)

    res = flask.request.json
    txt = res['text']
    cmd = res['cmd']
    print(f"Got '{txt}'")
    # Synthesize & Play Audio

    return flask.jsonify({'response': "Success!", 'received': txt})


if __name__ == '__main__':
    app.run(port=3000, debug=True, host=SERVE_HOST, ssl_context='adhoc')
