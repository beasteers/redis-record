import os

_all_set_cmds = 'xadd+set+hmset+hset+hsetnx+lset+mset+msetnx+psetex+setbit+setrange+setex+setnx+getset+json.set+json.mset'

MONITOR_KEY = os.getenv("RECORD_MONITOR_KEY") or 'RECORD:NAME'
MONITOR_CMDS = (os.getenv("RECORD_MONITOR_CMDS") or _all_set_cmds).split("+")


RECORD_KEY = os.getenv("RECORD_STREAMS_KEY") or 'XRECORD:NAME'
REPLAY_KEY = os.getenv("REPLAY_STREAMS_KEY") or 'XREPLAY:NAME'
RECORD_PAUSE_KEY = os.getenv("RECORD_STREAMS_PAUSE_KEY") or 'XRECORD:PAUSE'
REPLAY_PAUSE_KEY = os.getenv("REPLAY_STREAMS_PAUSE_KEY") or 'XREPLAY:PAUSE'
REPLAY_SEEK_KEY = os.getenv("REPLAY_STREAMS_SEEK_KEY") or 'XREPLAY:SEEK'

RECORD_XADD_DATA_FIELD = (os.getenv("RECORD_STREAMS_DATA_KEY") or 'd').encode()
RECORD_NAME_MAXLEN = int(os.getenv("RECORD_NAME_MAXLEN") or 100)

HOST = os.getenv('REDIS_HOST') or 'localhost'
PORT = os.getenv('REDIS_PORT') or 6379
DB = os.getenv('REDIS_DB') or 0

RECORDING_DIR = os.getenv('RECORDING_DIR') or './recordings'
DEFAULT_CHANNEL = 'all'

IGNORE_STREAMS = {RECORD_KEY, REPLAY_KEY, RECORD_PAUSE_KEY, REPLAY_PAUSE_KEY, REPLAY_SEEK_KEY}
CMD_IGNORE_DISPLAY = {'multi', 'exec'}
STORAGE_FORMAT = os.getenv('RECORD_STORAGE_FORMAT') or 'zip'
