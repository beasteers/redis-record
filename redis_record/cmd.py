import datetime
import redis
from .config import *
from .util import get_recording_filename


def _xadd(r, key, value, timestamp, **kw):
    return r.xadd(key, {RECORD_XADD_DATA_FIELD: value, **kw}, id=timestamp or '*', maxlen=RECORD_NAME_MAXLEN)

# ------------------------------ Monitor record ------------------------------ #

def start_monitoring(r, name):
    return r.set(MONITOR_KEY, name)

def stop_monitor(r):
    return r.delete(MONITOR_KEY)

# ---------------------------------- Record ---------------------------------- #

def start_recording(r, name, timestamp=None):
    return _xadd(r, RECORD_KEY, name, timestamp)

def stop_recording(r, timestamp=None):
    return _xadd(r, RECORD_KEY, '', timestamp)

def pause_recording(r, timestamp=None):
    return _xadd(r, RECORD_PAUSE_KEY, '1', timestamp)

def resume_recording(r, timestamp=None):
    return _xadd(r, RECORD_PAUSE_KEY, '0', timestamp)

# ---------------------------------- Replay ---------------------------------- #

def start_replay(r, name, timestamp=None, seek=0, pause=0):
    return _xadd(r, REPLAY_KEY, name, timestamp, seek=seek, pause=pause)

def stop_replay(r, timestamp=None):
    return _xadd(r, REPLAY_KEY, '', timestamp)

def pause_replay(r, timestamp=None):
    return _xadd(r, REPLAY_PAUSE_KEY, '1', timestamp)

def resume_replay(r, timestamp=None):
    return _xadd(r, REPLAY_PAUSE_KEY, '0', timestamp)

def seek_replay(r, seek, timestamp=None):
    return _xadd(r, REPLAY_SEEK_KEY, seek, timestamp)



class API:
    def __init__(self, host=HOST, port=PORT, db=DB, r=None):
        self.r = r or redis.Redis(host, port=port, db=db)

    # --------------------------------- Recording -------------------------------- #

    def start(self, name=None, timestamp=None):
        if not name:
            name = datetime.datetime.now().strftime("%Y.%m.%d-%H.%M.%S")
        return start_recording(self.r, name, timestamp)
    
    def pause_recording(self, timestamp=None):
        return pause_recording(self.r, timestamp)

    def resume_recording(self, timestamp=None):
        return resume_recording(self.r, timestamp)
    
    def stop(self, timestamp=None):
        return stop_recording(self.r, timestamp)
    
    # ---------------------------------- Replay ---------------------------------- #
    
    def replay(self, name, timestamp=None):
        return start_replay(self.r, name, timestamp)
    
    def pause(self, timestamp=None):
        return pause_replay(self.r, timestamp)
    
    def resume(self, timestamp=None):
        return resume_replay(self.r, timestamp)
    
    def seek(self, timestamp=None):
        return resume_replay(self.r, timestamp)
    
    def stop_replay(self, timestamp=None):
        return stop_replay(self.r, timestamp)
    
    # ----------------------------------- Misc ----------------------------------- #

    def fake(self, *a, **kw):
        from .fake import data
        return data(*a, **kw)


def cli():
    import fire
    fire.Fire(API)

if __name__ == '__main__':
    cli()
