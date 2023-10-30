import os
import datetime
from ...config import *
from ...util import get_recording_filename


class ZIPInfo:
    def __init__(self, recording_dir=RECORDING_DIR):
        self.recording_dir = recording_dir

    def list(self, *, info=False):
        recordings = [
            os.path.splitext(f)[0]
            for f in os.listdir(self.recording_dir)
        ]
        if info:
            recordings = [self.info(n) for n in recordings]
        return recordings
    
    def info(self, name):
        path = os.path.join(self.recording_dir, name)
        sids = os.listdir(path)
        files = {sid: os.listdir(os.path.join(path, sid)) for sid in sids}
        times = {sid: [tuple(float(t) for t in f.removesuffix('.zip').split('_')) for f in fs] for sid, fs in files.items()}
        starts, ends = zip(*times) or ((), ())
        t0 = min(starts)
        t1 = max(ends)

        return {
            "name": name,
            "start_time": t0,
            "end_time": t1,
            "start_datetime": datetime.datetime.fromtimestamp(t0).strftime('%c'),
            "end_datetime": datetime.datetime.fromtimestamp(t1).strftime('%c'),
            "streams": [
                {
                    "name": sid,
                    "chunks": times,
                }
                for sid, fs in files.items()
            ],
        }
