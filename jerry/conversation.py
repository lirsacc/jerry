
import datetime as dt

import rethinkdb as r

import jerry.messages as m

STARTED = 0
EXPECTING = 2


def _pass(*a, **kw):
    pass


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
            "time": None,
            "status": STARTED,
            "options": [],
            "started_at": dt.datetime.now(r.make_timezone("00:00")),
            "accessed_at": dt.datetime.now(r.make_timezone("00:00")),
            "current_msg": None
        })

    def access(self):
        self._data.accessed_at = dt.datetime.now(r.make_timezone("00:00"))

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
        if self._data.status == EXPECTING:
            return None

        self._data.status = EXPECTING
        if self._data.destination is None:
            return m.DESTINATION
        elif self._data.origin is None:
            return m.ORIGIN

        self._data.status = STARTED
        return None

    def handler(self):
        if self._data.status != EXPECTING:
            return None

        if self._data.destination is None:
            return self._save_destination
        elif self._data.origin is None:
            return self._save_origin
        else:
            return _pass

    def _save_origin(self, type, payload, send):
        pass

    def _save_destination(self, type, payload, send):
        pass
