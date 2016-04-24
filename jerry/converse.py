import logging
from pprint import pprint

import requests
import rethinkdb as r

from jerry.config import load_conf
import jerry.messages as m
from jerry.conversation import Conversation, extract_dest
import jerry.utils as u
import jerry.db as _db

logger = logging.getLogger(__name__)
cfg = load_conf()

MSG_URL = ('https://graph.facebook.com/v2.6/me/messages?access_token=%s'
           % cfg['PAGE_ACCESS_TOKEN'])


def send_message(recipient_id, payload):
    assert payload

    if isinstance(payload, list):
        return [
            send_message(recipient_id, payload_)
            for payload_ in payload
        ]

    data = {
        'recipient': {
            'id': recipient_id
        },
    }

    if isinstance(payload, dict):
        data['message'] = payload
    elif isinstance(payload, str):
        data['message'] = {
            'text': payload
        }
    else:
        raise Exception

    print("SENDING")
    pprint(data)

    req = requests.post(MSG_URL, json=data)
    if req.status_code != 200:
        logger.warning("Failed to send message %s" % req.text)


def start_conversation(user, db, destination=None):
    print("STARTING CONVERSATION WITH", user)
    conv = Conversation(user)
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


def initiate(msg, sender, db):
    # Can only initiate with a regular message
    if 'message' not in msg:
        send_message(sender['id'], m.MISSED)
        return

    print("NEW CONV")
    send_message(sender['id'], m.HELLO % sender['first_name'])
    cid, conv = start_conversation(sender, db)

    destination_match = extract_dest(msg['message']['text'])

    if destination_match:
        print("FOUND DEST", destination_match)
        conv.set('destination', destination_match)

    send_message(sender['id'], conv.next())
    conv.enslave()
    save_conversation(cid, conv, db)


def handle(msg, db):

    sender_id = msg['sender']['id']

    print('-------------------------------------------------------------------')
    print('-------------------------------------------------------------------')

    # Ignore ACK msgs from FB for now
    if 'delivery' in msg:
        logger.debug('Ignored delivery message: %s' % msg)
        return

    if 'message' in msg and msg['message'].get('text', '') == 'help':
        send_message(sender_id, m.HELP)
        return

    print("HANDLING")
    pprint(msg)
    print()

    user = _db.one(r.table('users').filter(r.row['id'] == sender_id).run(db))
    if user is None:
        print("NEW USER")
        first_name = u.get_first_name_of_user(sender_id)
        sender = {
            "id": sender_id,
            "first_name": first_name,
        }
        r.table('users').insert(sender).run(db)
        initiate(msg, sender, db)

    else:
        print("FOUND USER")

        conv = _db.first(r.table('conversations')
                         .filter(r.row['user_id'] == sender_id)
                         .run(db))

        if conv:
            conv = Conversation.from_dict(conv)

        if conv and not conv.get('closed'):

            # In case you use go to, reset conversation
            if 'message' in msg:
                destination_match = extract_dest(msg['message']['text'])
                if destination_match:
                    conv.set('closed', True)
                    save_conversation(conv.get('id'), conv, db)
                    initiate(msg, sender, db)
                    return

            print("FOUND OLD CONV", conv.get('status'))

            if conv.is_master():
                next_msg = conv.next()
                print("NEXT MESSAGE =>", next_msg)
                if next_msg is not None:
                    send_message(sender_id, next_msg)
                    conv.enslave()
            else:  # conv.is_slave()
                # Handle messages as we are expecting something
                backup_conv = conv.to_dict()
                try:
                    handler = conv.handler()
                    yield_, feedback = False, None
                    if 'message' in msg:
                        yield_, feedback = handle_message(msg, db, handler)
                    elif 'postback' in msg:
                        yield_, feedback = handle_postback(msg, db, handler)

                    conv.free()
                    if yield_:
                        if feedback is not None:
                            send_message(sender_id, feedback)
                        next_msg = conv.next()
                        print("NEXT MESSAGE =>", next_msg)
                        if next_msg is not None:
                            send_message(sender_id, next_msg)
                            conv.enslave()
                    elif feedback:
                        send_message(sender_id, feedback)
                        conv.enslave()
                    else:
                        send_message(sender_id, m.MISSED)
                        conv.enslave()
                except (ValueError, AssertionError) as ex:
                    # Something went wrong, cancel it all out
                    # Ideally this would determined the error kind and
                    # send details regarding how to solve the problem.
                    logger.warning(str(ex))
                    conv = Conversation.from_dict(backup_conv)
                    conv.set('id', backup_conv.id)
                    conv.enslave()
                    send_message(sender_id, m.MISSED)

            save_conversation(conv.get('id'), conv, db)

        else:
            initiate(msg, user, db)


def handle_message(msg, db, handler):
    print("HANDLE MESSAGE")
    return handler('message', msg)


def handle_postback(msg, db, handler):
    print("HANDLE POSTBACK", msg['postback']['payload'])
    return handler('postback', msg)
