import rethinkdb as r

from jerry.config import load_conf
cfg = load_conf()

TABLES = (
    'users',
    'conversations',
    'bookings',
    'seen_entries'
)


def connection():
    conn = r.connect(cfg['RETHINK_URL'], cfg['RETHINK_PORT'], db='jerry')
    return conn


def one(cursor):
    res = None
    seen = 0
    for res_ in cursor:
        if seen > 0:
            raise Exception('More than one result')
        res = res_
        seen += 1
    return res


def first(cursor):
    res = None
    for res_ in cursor:
        res = res_
        break
    return res
