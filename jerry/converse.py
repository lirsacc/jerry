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


def start_conversation(user_id, db):
    print("STARTING CONVERSATION WITH", user_id)
    conv = Conversation(user_id)
    inserted = r.table('conversations').insert(conv.to_dict()).run(db)
    conv_uuid = inserted["generated_keys"][0]
    send_message(user_id, text=messages.WELCOME)
    send_message(user_id, text=conv.next())
    save_conversation(conv_uuid, conv)


def save_conversation(conv_uuid, conv):
    # Update timestamp and save value
    conv.access()
    (r.table('conversations')
     .filter(r.row['id'] == conv_uuid)
     .update(conv.to_dict()))


def handle(msg, db):
    sender_id = msg['sender']['id']

    # Ignore ACK msgs from FB for now
    if 'delivery' in msg:
        return

    print("HANDLING")
    pprint(msg)
    print()

    user = _db.one(r.table('users').filter(r.row['id'] == sender_id).run(db))
    if user is None:
        print("NEW USER")
        r.table('users').insert({"id": sender_id}).run(db)
        start_conversation(sender_id, db)

    else:
        print("FOUND USER")

        if 'message' in msg:
            text = msg['message']['text']
            if text == 'help':
                pass
            elif 'go to' in text:
                pass

        conv = _db.first(r.table('conversations')
                         .filter(r.row['user_id'] == sender_id)
                         .run(db))
        if conv:
            print("FOUND CONV")
            conv_uuid = conv['id']
            conv = Conversation.from_dict(conv)
            next_msg = conv.next()
            print("NEXT MESSAGE", next_msg)
            # Conversation is not expecting input, send next prompt
            if next_msg is not None:
                send_message(sender_id, text=next_msg)
                return
            else:
                # Handle messages as we are expecting something
                if 'message' in msg:
                    handle_message(msg, db, conv.handler())

                if 'postback' in msg:
                    handle_postback(msg, db, conv.handler())

            save_conversation(conv_uuid, conv)

        else:
            print("NEW CONV")
            start_conversation(sender_id, db)


def handle_message(msg, db, handler):
    pass


def handle_postback(msg, db, handler):
    pass
