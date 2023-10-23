import time
import tqdm
import datetime
import redis
from .config import *
from .util import get_recording_filename


def _xadd(r, key, value, timestamp='*', maxlen=RECORD_NAME_MAXLEN, **kw):
    return r.xadd(key, {RECORD_XADD_DATA_FIELD: value, **kw}, id=timestamp or '*', maxlen=maxlen)

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

def seek_replay(r, seek, timestamp=None):
    return _xadd(r, REPLAY_SEEK_KEY, seek, timestamp)



class Commands:
    def __init__(self, host=HOST, port=PORT, db=DB, r=None):
        self.r = r or redis.Redis(host, port=port, db=db)

    def __enter__(self):
        return self
    
    def __exit__(self, *a):
        self.r.close()

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
    
    def current_replay(self):
        return self.r.xrevrange(REPLAY_KEY, count=1)
    
    

    def recorder(self, *a, **kw):
        from redis_record.record import record
        return record(*a, **kw)
    
    def recorder(self, *a, **kw):
        from redis_record.replay import replay
        return replay(*a, **kw)
    
    # ----------------------------------- Misc ----------------------------------- #

    # def fake(self, *a, **kw):
    #     from .fake import data
    #     return data(*a, **kw)
    
    def fake(self, stream_id, rate=100, limit=None, **kw):
        from .sync import Clock
        sync = Clock(rate)
        pbar = tqdm.tqdm()
        i = 0
        while True:
            self.add_fake(stream_id, i, **kw)
            pbar.update()
            sync.sync()
            i += 1
            if limit and i >= limit:
                break
    
    def add_fake(self, stream_id, data=None, size=1000, **kw):
        x = str(data).encode() if data is not None else b'0'*size
        return x, _xadd(self.r, stream_id, x, **kw)

    def read(self, sids, block=None, **kw) -> tuple[list, dict[str, str]]:
        if isinstance(sids, list):
            sids = {s: f'{time.time()*1000:.0f}-0' for s in sids}
        data = self.r.xread(sids, block=block, **kw)
        # decode stream IDs and timestamps
        data = _decode_xread_format(data)
        return data, _update_cursor(sids, data)


def _update_cursor(sids: dict[str, str], data: list[str|tuple]) -> dict[str, str]:
    for s, ts in data:
        if ts:
            sids[s] = max(t for t, x in ts)
    return sids


def _decode_xread_format(data):
    return [(s.decode(), [(t.decode(), x) for t, x in xs]) for s, xs in data]


def cli():
    import fire
    fire.Fire(Commands)

if __name__ == '__main__':
    cli()
