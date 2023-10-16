import os
import json
import base64
from mcap.reader import make_reader


class MCAPPlayer:
    def __init__(self, name, recording_dir) -> None:
        self.path = name if os.path.isfile(name) else os.path.join(recording_dir, f'{name}.mcap')

    def __enter__(self):
        self.fh = open(self.path, "rb")
        self.reader = make_reader(self.fh)
        print(self.reader.get_header())
        return self

    def __exit__(self, exc_type, exc_value, trace):
        self.fh.close()

    def iter_messages(self):
        for schema, channel, message in self.reader.iter_messages():
            args = json.loads(message.data)
            stream_id = args['stream_id']
            data = {k: base64.b64decode(x.encode()) for k, x in args['data'].items()}
            ts = message.publish_time*10e-9 * 10e-3 # for some reason it's -12 not -9??
            yield stream_id, ts, data