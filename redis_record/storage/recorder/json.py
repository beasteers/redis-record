import os
import orjson
from .base import BaseRecorder
from ...util import move_with_suffix

import logging

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class JsonRecorder(BaseRecorder):
    recording_dir = ''
    def __init__(self, out_dir='.', list_key='data'):
        self.out_dir = out_dir
        self.writer = {}
        self.list_key = list_key

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()

    def ensure_writer(self, name):
        self.close()
        self.recording_dir = os.path.join(self.out_dir, name)
        move_with_suffix(self.recording_dir)
        os.makedirs(self.recording_dir, exist_ok=True)

    def ensure_channel(self, sid):
        if sid not in self.writer:
            self.writer[sid] = open(os.path.join(self.recording_dir, f'{sid}.json'), 'wb')
            self.writer[sid].write(b'[\n')
            self.writer[sid].i_line = 0
        return self.writer[sid]

    def close(self):
        for w in self.writer.values():
            w.write(b'\n]\n')
            w.close()
        self.writer.clear()

    def write(self, sid, t, data):
        w = self.ensure_channel(sid)
        data = self._add_timestamp_to_json(data, t)
        data = self._serialize(data)
        if w.i_line:
            w.write(b',\n')
        w.write(data)
        w.i_line += 1

    def _add_timestamp_to_json(self, d, ts):
        if ts is not None:
            try:
                if isinstance(d, bytes):
                    d = orjson.loads(d)
                if self.list_key:
                    if not isinstance(d, dict):
                        d = {self.list_key: d}
                    if 'timestamp' not in d:
                        d['timestamp'] = ts
            except Exception:
                print("error reading data")
                print(d)
                raise
        return d

    def _serialize(self, d):
        try:
            if not isinstance(d, bytes):
                d = orjson.dumps(d, option=orjson.OPT_NAIVE_UTC | orjson.OPT_SERIALIZE_NUMPY)
        except Exception:
            print("error writing data")
            print(d)
            raise
        return d
