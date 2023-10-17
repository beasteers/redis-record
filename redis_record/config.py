import os

_all_set_cmds = 'xadd+set+hmset+hset+hsetnx+lset+mset+msetnx+psetex+setbit+setrange+setex+setnx+getset+json.set+json.mset'

MONITOR_KEY = os.getenv("RECORD_MONITOR_KEY") or 'RECORD:NAME'
MONITOR_CMDS = (os.getenv("RECORD_MONITOR_CMDS") or _all_set_cmds).split("+")


REPLAY_KEY = os.getenv("REPLAY_STREAMS_KEY") or 'XREPLAY:NAME'
RECORD_KEY = os.getenv("RECORD_STREAMS_KEY") or 'XRECORD:NAME'
RECORD_XADD_DATA_FIELD = (os.getenv("RECORD_STREAMS_DATA_KEY") or 'd').encode()
RECORD_NAME_MAXLEN = int(os.getenv("RECORD_NAME_MAXLEN") or 100)

HOST = os.getenv('REDIS_HOST') or 'localhost'
PORT = os.getenv('REDIS_PORT') or 6379
DB = os.getenv('REDIS_DB') or 0

RECORDING_DIR = os.getenv('RECORDING_DIR') or './recordings'

CMD_IGNORE_DISPLAY = {'multi', 'exec'}
