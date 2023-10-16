# Class to record all desired redis activity

import os
import time
import json
import tqdm
from mcap.writer import Writer


class BaseRecorder:
    def __init__(self, schema=None, out_dir='.'):
        self.out_dir = out_dir
        self.schema = schema

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()

    def write(self, timestamp, channel='all', **data):
        raise NotImplementedError

    def close(self):
        pass

    def ensure_writer(self, record_name, force=False):
        raise NotImplementedError

    def ensure_channel(self, channel='all'):
        raise NotImplementedError




def read(fname):
    from mcap.reader import make_reader
    with open(fname, "rb") as f:
        reader = make_reader(f)
        print(reader.get_header())
        # summary = reader.get_summary()
        # print(summary)
        for schema, channel, message in reader.iter_messages():
            print(f"{channel.topic} ({schema.name}): {message.data}")



def cli():
    import fire
    fire.Fire({
        "read": read,
    })

if __name__ == '__main__':
    cli()