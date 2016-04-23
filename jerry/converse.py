import logging
from pprint import pprint

import requests
import rethinkdb as r

from jerry.config import load_conf
import jerry.messages as m
from jerry.conversation import Conversation, extract_dest
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

    assert (payload is not None or text is not None) and not (payload and text)

    if text is not None:
        data['message'] = {
            'text': text
        }
    elif payload is not None:
        data['message'] = payload

    req = requests.post(MSG_URL, json=data)
    if req.status_code != 200:
        logger.warning("Failed to send message %s" % req.text)


def start_conversation(user_id, db, destination=None):
    print("STARTING CONVERSATION WITH", user_id)
    conv = Conversation(user_id)
    print("INSERTING")
    pprint(conv.to_dict())
    inserted = r.table('conversations').insert(conv.to_dict()).run(db)
    cid = inserted["generated_keys"][0]
    print(cid)
    print()
    return cid, conv


def save_conversation(cid, conv, db):
    # Update timestamp and save value
    conv.access()
    print("SAVING CONV", cid)
    pprint(conv.to_dict())
    changes = r.table('conversations').get(cid).update(
        conv.to_dict(),
        return_changes=True
    ).run(db)
    pprint(changes)
    print()


def initiate(msg, sender_id, db):
    # Can only initiate with a regular message
    if 'message' not in msg:
        send_message(sender_id, text=m.MISSED)
        return

    print("NEW CONV")
    cid, conv = start_conversation(sender_id, db)

    destination_match = extract_dest(msg['message']['text'])

    if destination_match:
        print("FOUND DEST", destination_match)
        conv.set('destination', destination_match)
        send_message(sender_id, conv.next())
        conv.enslave()
        save_conversation(cid, conv, db)
    else:
        send_message(sender_id, text=m.MISSED)


def handle(msg, db):
    sender_id = msg['sender']['id']

    print('-------------------------------------------------------------------')
    print('-------------------------------------------------------------------')

    # Ignore ACK msgs from FB for now
    if 'delivery' in msg:
        logger.debug('Ignored delivery message: %s' % msg)
        return

    if 'message' in msg and msg['message'].get('text', '') == 'help':
        send_message(sender_id, text=m.HELP)
        return

    print("HANDLING")
    pprint(msg)
    print()

    user = _db.one(r.table('users').filter(r.row['id'] == sender_id).run(db))
    if user is None:
        print("NEW USER")
        r.table('users').insert({"id": sender_id}).run(db)
        initiate(msg, sender_id, db)

    else:
        print("FOUND USER")

        conv = _db.first(r.table('conversations')
                         .filter(r.row['user_id'] == sender_id)
                         .run(db))

        if conv:
            conv = Conversation.from_dict(conv)

        if conv and not conv.get('closed'):
            print("FOUND OLD CONV", conv.get('status'))

            if conv.is_master():
                next_msg = conv.next()
                print("NEXT MESSAGE =>", next_msg)
                if next_msg is not None:
                    send_message(sender_id, text=next_msg)
                    conv.enslave()
            else:  # conv.is_slave()
                # Handle messages as we are expecting something
                if 'message' in msg:
                    yield_ = handle_message(msg, db, conv.handler())

                if 'postback' in msg:
                    yield_ = handle_postback(msg, db, conv.handler())

                conv.free()
                if yield_:
                    next_msg = conv.next()
                    print("NEXT MESSAGE =>", next_msg)
                    if next_msg is not None:
                        send_message(sender_id, text=next_msg)
                        conv.enslave()

            save_conversation(conv.get('id'), conv, db)

        else:
            initiate(msg, sender_id, db)


def handle_message(msg, db, handler):
    print("HANDLE MESSAGE")
    return handler('message', msg)


def handle_postback(msg, db, handler):
    print("HANDLE POSTBACK")
    return handler('postback', msg)
