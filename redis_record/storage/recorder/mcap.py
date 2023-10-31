# Class to record all desired redis activity

import os
import time
import json
import base64
from mcap.writer import Writer
from .base import BaseRecorder
from ...config import DEFAULT_CHANNEL
from ...util import move_with_suffix

import logging

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class MCAPRecorder(BaseRecorder):
    def __init__(self, schema=None, out_dir='.'):
        self.out_dir = out_dir
        self.writer = self.fhandle = None
        self.schema = schema
        self.channel_ids = {}

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()

    def ensure_writer(self, record_name, force=False):
        if self.writer is not None and force:
            self.close()

        if self.writer is None:
            # create new writer
            os.makedirs(self.out_dir or '.', exist_ok=True)
            self.fname = fname = os.path.join(self.out_dir, f'{record_name}.mcap')
            move_with_suffix(self.fname)
            self.fhandle = fhandle = open(fname, "wb")
            self.writer = writer = Writer(fhandle)
            writer.start()
            log.info("Created Recorder: %s", fname)

            # https://mcap.dev/docs/python/mcap-apidoc/mcap.well_known#mcap.well_known.MessageEncoding
            kw = {"properties": self.schema} if self.schema else {}
            self.schema_id = writer.register_schema(
                name="data",
                encoding="jsonschema",
                data=json.dumps({"type": "object", **kw}).encode(),
            )
        return self

    def ensure_channel(self, channel=DEFAULT_CHANNEL):
        if channel not in self.channel_ids:
            log.debug("Opening Recorder Channel: %s %s", self.fname, channel)
            self.channel_ids[channel] = self.writer.register_channel(
                schema_id=self.schema_id,
                topic=channel,
                message_encoding="json",
            )

    def write(self, stream_id, timestamp, data):
        self.ensure_channel(stream_id)
        data = {'stream_id': stream_id, 'data': prepare_data(data)}
        self.writer.add_message(
            channel_id=self.channel_ids[stream_id],
            log_time=time.time_ns(),
            data=json.dumps(data).encode("utf-8"),
            publish_time=int(timestamp * 10e9),
        )

    def close(self):
        if self.writer is not None:
            self.writer.finish()
            self.fhandle.close()
            self.writer = self.fhandle = None
            self.channel_ids.clear()
            log.info("Closed Recorder: %s", self.fname)



def prepare_data(data):
    return {k.decode(): base64.b64encode(v).decode() for k, v in data.items()}



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