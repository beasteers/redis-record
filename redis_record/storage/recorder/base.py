
import logging

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)



class BaseRecorder:
    def __init__(self, out_dir='.', schema=None):
        self.out_dir = out_dir
        self.schema = schema
        self.last_timestamp = None
        self.index = 0

    def _fix_timestamp(self, timestamp):
        if isinstance(timestamp, str):
            return timestamp

        timestamp = int(timestamp*1000)
        if self.last_timestamp == timestamp:
            self.index += 1
        else:
            self.index = 0
        self.last_timestamp = timestamp
        return f'{timestamp}-{self.index}'

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()

    def write(self, sid, timestamp, data):
        raise NotImplementedError

    def close(self):
        pass

    def ensure_writer(self, name, force=False):
        raise NotImplementedError

    def ensure_channel(self, sid):
        raise NotImplementedError
