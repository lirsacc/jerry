import logging
from pprint import pprint

import requests
import rethinkdb as r

from jerry.config import load_conf
import jerry.messages as messages
from jerry.conversation import Conversation
import jerry.db as _db

logger = logging.getLogger(__name__)
cfg = load_conf()

MSG_URL = ('https://graph.facebook.com/v2.6/me/messages?access_token=%s'
           % cfg['PAGE_ACCESS_TOKEN'])


def send_message(recipient_id, text=None, payload=None):
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
    if req.status_code != 200:
        logger.warning("Failed to send message %s" % req.text)


def handle(msg, db):
    sender_id = msg['sender']['id']

    print("HANDLING")
    pprint(msg)

    user = _db.one(r.table('users').filter(r.row['id'] == sender_id).run(db))
    if user is None:
        r.table('users').insert({
            "id": sender_id
        }).run(db)
        conv = Conversation()
        r.table('conversations').insert(conv.to_dict()).run(db)
        send_message(sender_id, text=messages.WELCOME)

    else:
        conv = _db.first(
            r.table('conversations')
            .filter(r.row['user_id'] == sender_id)
            .run(db)
        )
        if conv:
            conv = Conversation.from_dict(conv)
            send_message(sender_id, text='Hey, I know you!')
        else:
            send_message(sender_id, text=messages.WELCOME)

    if 'message' in msg:
        handle_message(msg, db)

    if 'postback' in msg:
        handle_postback(msg, db)


def handle_message(msg, db):
    pass


def handle_postback(msg, db):
    pass
