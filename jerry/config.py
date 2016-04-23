import os

KEYS = (
    'PAGE_ACCESS_TOKEN',
    'SECURITY_TOKEN',
    'RETHINK_URL',
    'RETHINK_PORT'
)


def load_conf(conf={}, reload_=False):

    if reload_:
        conf.clear()

    if conf:
        return conf

    for key in KEYS:
        value = os.environ.get('JERRY_%s' % key)
        assert value, (key, value)
        conf[key] = value

    for key, value in os.environ.items():
        if key.startswith('JERRY_'):
            if key[6:] not in conf:
                conf[key[6:]] = value


    return conf
