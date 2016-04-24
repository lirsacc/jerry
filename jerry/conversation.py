"""
State machine to represent the booking process as a conversation
"""
import datetime as dt
import re

import parsedatetime
import rethinkdb as r

import jerry.messages as m
import jerry.db as _db
import jerry.mock_templates as mock
import jerry.generic_template as tmpl

MASTER = 'MASTER'
SLAVE = 'SLAVE'

TYPE_PERSONAL = 'PERSONAL'
TYPE_PRO = 'PROFESIONNAL'
ALLOWED_TYPES = (TYPE_PRO, TYPE_PERSONAL)


def save_option(user_id, option):
    db = _db.connection()
    r.table('users').insert({
        'user_id': user_id,
        'options': option
    }).run(db)


def _pass(*a, **kw):
    pass

GOTO_RE = re.compile(
    r'^[\w\s\']*([Gg][Oo]|[Tt]ravel|[Tt]rip)\s?[Tt][Oo]\s?(\w+)$'
)


def extract_dest(text):
    match = GOTO_RE.match(text)
    if match is None:
        return None
    else:
        return match.group(1)


class dumb_attrdict(object):
    def __init__(self, d):
        self.__dict__ = d


class Conversation(object):

    def __init__(self, user):
        assert user
        self._data = dumb_attrdict({
            "user_id": user['id'],
            "first_name": user['first_name'],
            "origin": None,
            "destination": None,
            "status": MASTER,
            "time": None,
            "options": None,
            "selected_option": None,
            "type": None,
            "started_at": dt.datetime.now(r.make_timezone("00:00")),
            "accessed_at": dt.datetime.now(r.make_timezone("00:00")),
            "current_msg": None,
            "closed": False,
            "confirmed": False,
        })
        self.remaining_allowance = 0

    def access(self):
        self._data.accessed_at = dt.datetime.now(r.make_timezone("00:00"))

    def set(self, key, value):
        assert key in self._data.__dict__
        setattr(self._data, key, value)

    def get(self, key):
        assert key in self._data.__dict__
        return getattr(self._data, key)

    def is_master(self):
        return self._data.status == MASTER

    def is_slave(self):
        return self._data.status == SLAVE

    def enslave(self):
        print("ENSLAVING")
        self._data.status = SLAVE

    def free(self):
        self._data.status = MASTER

    def to_dict(self):
        copy = dict(**self._data.__dict__)
        return copy

    @classmethod
    def from_dict(cls, data):
        assert isinstance(data, dict)
        obj = cls({
            'id': data['user_id'],
            'first_name': data['first_name']
        })
        obj._data = dumb_attrdict(data)
        return obj

    def current(self):
        return self._data.current_msg

    # State machine from master state (send questions)
    def next(self):
        if self._data.status == SLAVE:
            return None

        if self._data.destination is None:
            return m.DESTINATION
        elif self._data.origin is None:
            return m.ORIGIN
        elif self._data.time is None:
            return m.WHEN
        elif self._data.options is None:
            options = mock.make_options(
                self.get('origin'),
                self.get('destination'),
                self.get('time'),
                ('train', 'car_rental')
            )
            self._data.options = options
            return mock.make_options_offers(options)
        elif self._data.type is None:
            return tmpl.generate_generic_template([tmpl.create_element(
                title='Confirm',
                subtitle=m.TYPE,
                buttons=[
                    tmpl.create_button("Business", payload=TYPE_PRO),
                    tmpl.create_button("Personal", payload=TYPE_PERSONAL)
                ]
            )])
        elif not self._data.confirmed:
            return tmpl.generate_generic_template([tmpl.create_element(
                title='Confirm',
                subtitle=m.CONFIRM % self.remaining_allowance,
                buttons=[
                    tmpl.create_button("Yes", payload="YES"),
                    tmpl.create_button("No", payload="NO")
                ]
            )])
        else:
            return m.MOAR

        return None

    # State machine from slave state (expects data)
    def handler(self):
        if self._data.status != SLAVE:
            return None

        if self._data.destination is None:
            return self._save_destination
        elif self._data.origin is None:
            return self._save_origin
        elif self._data.time is None:
            return self._save_time
        elif self._data.selected_option is None:
            return self._handle_option_postback
        elif self._data.type is None:
            return self._handle_booking_type
        elif not self._data.confirmed:
            return self._handle_confirmation
        else:
            return _pass

    def _save_origin(self, type_, payload, **kw):
        if type_ in ('message'):
            orig = payload[type_]['text']
            self.set('origin', orig)
            return True, None
        else:
            return False, m.MISSED

    def _save_destination(self, type_, payload, **kw):
        if type_ in ('message'):
            dest = payload[type_]['text']
            self.set('destination', dest)
            return True, None
        else:
            return False, m.MISSED

    def _save_time(self, type_, payload):
        if type_ in ('message'):
            value = payload[type_]['text']
            cal = parsedatetime.Calendar()

            dt_, _ = cal.parseDT(
                value,
                tzinfo=r.make_timezone("00:00")
            )

            assert dt_
            self.set('time', dt_)
            return True, (
                'Perfect %s! I have got all the information I need. Give me a '
                'second to find some options for you.' % (
                    self.get('first_name')
                )
            )
        else:
            return False, m.MISSED

    def _handle_option_postback(self, type_, msg, **kw):
        if type_ == 'postback':
            payload = msg['postback']['payload']
            parts_ = payload.split('::')
            action = parts_[0]

            if action != 'SEE_ALL':
                opt_index = parts_[1]
                assert opt_index is not None
                opt_index = int(opt_index)
                assert (
                    opt_index >= 0 and opt_index < len(self.get('options'))
                ), opt_index
            else:
                opt_index = None

            if action == 'BUY':
                self.set('selected_option', opt_index)
                return True, 'Great, just one more thing'
            elif action == 'DETAILS':
                opt = self.get('options')[opt_index]
                return False, mock.make_option_details(opt, opt_index)
            elif action == 'SEE_ALL':
                return False, mock.make_options_offers(self.get('options'))

        else:
            return False, m.MISSED

    def _set_type(self, value):
        assert value in ALLOWED_TYPES
        option = self.get('options')[self.get('selected_option')]
        value = value.upper()
        self.set('type', value)
        if value == TYPE_PRO:
            self.remaining_allowance = 2570 - option['price']
        elif value == TYPE_PERSONAL:
            self.remaining_allowance = 1260 - option['price']
        return True, None

    def _handle_booking_type(self, type_, msg, **kw):
        if type_ == 'message':
            value = msg[type_]['text']
            return self._set_type(value)
        elif type_ == 'postback':
            value = msg['postback']['payload']
            return self._set_type(value)
        else:
            return False, m.MISSED

    def _handle_confirmation(self, type_, msg):
        if type_ == 'postback':
            value = msg['postback']['payload']
            if value == 'YES':
                self.set('confirmed', True)
                option = self.get('options')[self.get('selected_option')]
                save_option(self.get('user_id'), option)
                self.set('closed', True)
                return True, [
                    'Thank you for your booking %s' % self.get('first_name'),
                    m.FINISHED % (
                        self.get('origin'),
                        self.get('destination'),
                        self.get('time').isoformat()
                    ),
                    mock.make_option_booking(option,
                                             self.get('selected_option'))
                ]
            else:
                False, m.MISSED
        else:
            return False, m.MISSED
