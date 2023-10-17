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

    it = None
    def iter_messages(self):
        if self.it is None:
            self.it = iter(self.reader.iter_messages())
        for schema, channel, message in self.it:
            yield self._parse_message(message)

    def next_message(self):
        if self.it is None:
            self.it = iter(self.reader.iter_messages())
        schema, channel, message = next(self.it)
        return self._parse_message(message)

    def _parse_message(self, message):
        args = json.loads(message.data)
        stream_id = args['stream_id']
        data = {k: base64.b64decode(x.encode()) for k, x in args['data'].items()}
        ts = message.publish_time*10e-9 * 10e-3 # for some reason it's -12 not -9??
        return stream_id, ts, data