from flask import Flask
from flask import request

import json
import requests

from jerry.config import load_conf

app = Flask(__name__)

cfg = load_conf()

NAKED_JERRY_URL = (
    'https://upload.wikimedia.org/wikipedia/en/2/2f/Jerry_Mouse.png')

MSG_URL = ('https://graph.facebook.com/v2.6/me/messages?access_token=%s'
           % cfg['PAGE_ACCESS_TOKEN'])


@app.route("/")
def hello():
    return "Hello World!"


@app.route('/webhook', methods=['GET'])
def webhook_get():
    hub_challenge = request.args.get('hub.challenge', None)
    hub_token = request.args.get('hub.verify_token', None)
    if hub_token == cfg['SECURITY_TOKEN']:
        return hub_challenge, 200


def send_message(recipient_id, text=None, payload=None):
    """
    """
    data = {
        'recipient': {
            'id': recipient_id
        },
    }

    assert not (payload is None and text is None)

    if text is not None:
        data['message'] = {
            'text': text
        }
    elif payload is not None:
        data['message'] = payload

    req = requests.post(MSG_URL, json=data)
    req.raise_on_status()


def handle_message(msg):
    sender_id = msg['sender']['id']
    data = msg['message']

    if 'text' in data:
        send_message(sender_id,
                     text='PONG => ' + msg['message']['text'])
    else:
        print(data)
        return

    if 'image' in msg['message']['text'].lower():
        send_message(sender_id, payload={
            'attachment': {
                'type': 'image',
                'payload': {
                    'url': NAKED_JERRY_URL
                }
            }
        })
    else:
        send_message(sender_id, payload={
            'attachment': {
                'type': 'template',
                'payload': {
                    'template_type': 'button',
                    'text': 'Do you want to see me naked ?',
                    'buttons': [{
                        'type': 'postback',
                        'title': 'Hell yeah!',
                        'payload': 'PRON'
                    }, {
                        'type': 'postback',
                        'title': 'Hell no!',
                        'payload': 'PRUDE'
                    }]
                }
            }
        })


def handle_postback(msg):
    sender_id = msg['sender']['id']
    data = msg['postback']['payload']
    if data == 'PRUDE':
        send_message(sender_id, text='Well too bad for you...')
    elif data == 'PRON':
        send_message(sender_id, payload={
            'attachment': {
                'type': 'image',
                'payload': {
                    'url': NAKED_JERRY_URL
                }
            }
        })


@app.route('/webhook', methods=['POST'])
def webhook_post():
    data = json.loads(request.data.decode('utf-8'))
    entries = data['entry']
    if not entries:
        return "", 200

    for entry in entries:
        messages = entry['messaging']
        for msg in messages:

            if 'message' in msg:
                handle_message(msg)

            if 'postback' in msg:
                handle_postback(msg)

    return "OK", 200


if __name__ == '__main__':
    app.debug = True
    app.run(port=4242)
