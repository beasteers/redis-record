

class BaseRecorder:
    def __init__(self, out_dir='.', schema=None):
        self.out_dir = out_dir
        self.schema = schema

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
