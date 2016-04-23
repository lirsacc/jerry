import datetime as dt
import re

import rethinkdb as r

import jerry.messages as m

MASTER = 'MASTER'
SLAVE = 'SLAVE'


def _pass(*a, **kw):
    pass

GOTO_RE = re.compile(r'^\s*[Gg][Oo]\s?[Tt][Oo]\s?(\w+)$')


def extract_dest(text):
    match = GOTO_RE.match(text)
    if match is None:
        return None
    else:
        return match.group(1)


class attrdict(object):
    def __init__(self, d):
        self.__dict__ = d


class Conversation(object):

    def __init__(self, user_id):
        assert user_id
        self._data = attrdict({
            "user_id": user_id,
            "origin": None,
            "destination": None,
            "status": MASTER,
            "time": None,
            "options": [],
            "started_at": dt.datetime.now(r.make_timezone("00:00")),
            "accessed_at": dt.datetime.now(r.make_timezone("00:00")),
            "current_msg": None,
            "closed": False,
        })

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
        obj = cls(data['user_id'])
        obj._data = attrdict(data)
        return obj

    def current(self):
        return self._data.current_msg

    def next(self):
        if self._data.status == SLAVE:
            return None

        if self._data.destination is None:
            return m.DESTINATION
        elif self._data.origin is None:
            return m.ORIGIN
        elif self._data.time is None:
            return m.WHEN
        else:
            return "Blah..."

        return None

    def handler(self):
        if self._data.status != SLAVE:
            return None

        if self._data.destination is None:
            return self._save_destination
        elif self._data.origin is None:
            return self._save_origin
        elif self._data.time is None:
            return self._save_time
        else:
            return _pass

    def _save_origin(self, type_, payload):
        if type_ in ('message'):
            orig = payload[type_]['text']
            self.set('origin', orig)
            return True
        else:
            return False

    def _save_destination(self, type_, payload):
        if type_ in ('message'):
            dest = payload[type_]['text']
            self.set('destination', dest)
            return True
        else:
            return False

    def _save_time(self, type_, payload):
        if type_ in ('message'):
            value = payload[type_]['text']
            self.set('time', value)
            return True
        else:
            return False
