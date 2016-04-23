
import datetime as dt
import json

STARTED = 0
OPTIONS_PROPOSED = 1
CONFIRMED = 2


class Conversation(object):

    def __init__(self, user_id):
        assert user_id
        self._data = {
            "user_id": user_id,
            "origin": None,
            "destination": None,
            "time": None,
            "status": STARTED,
            "options": [],
            "started_at": dt.datetime.utcnow()
        }

    def to_dict(self):
        return self._data

    @classmethod
    def from_dict(cls, data):
        assert isinstance(data, dict)
        obj = cls()
        obj._data = data
