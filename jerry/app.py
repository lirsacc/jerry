import datetime as dt
import logging

from flask import Flask, request, g, abort

import json

import rethinkdb as r

from jerry.config import load_conf
from jerry.converse import handle
import jerry.db as db

conn = db.connection()

logger = logging.getLogger(__name__)

app = Flask(__name__)
cfg = load_conf()

NAKED_JERRY_URL = (
    'https://upload.wikimedia.org/wikipedia/en/2/2f/Jerry_Mouse.png')


@app.before_request
def before_request():
    try:
        g.db = db.connection()
    except r.errors.RqlDriverError:
        abort(503, "No database connection could be established.")


@app.teardown_request
def teardown_request(exception):
    try:
        g.db.close()
    except AttributeError:
        pass


@app.route("/")
def hello():
    return "Hello World!"


@app.route('/webhook', methods=['GET'])
def webhook_get():
    hub_challenge = request.args.get('hub.challenge', None)
    hub_token = request.args.get('hub.verify_token', None)
    if hub_token == cfg['SECURITY_TOKEN']:
        return hub_challenge, 200


@app.route('/webhook', methods=['POST'])
def webhook_post():
    data = json.loads(request.data.decode('utf-8'))
    entries = data['entry']
    if not entries:
        return "", 200

    for entry in entries:
        id_ = entry['id']
        seen = r.table('seen_entries').get(id_).run(g.db)
        if seen:
            logger.warning('Duplicate receive for entry %s' % id_)

        messages = entry['messaging']
        for msg in messages:
            handle(msg, g.db)

        seen = r.table('seen_entries').insert({
            'id': id_,
            'time': dt.datetime.now(r.make_timezone("00:00"))
        }).run(g.db)

    return "", 200


if __name__ == '__main__':
    app.debug = True
    app.run(port=4242)
