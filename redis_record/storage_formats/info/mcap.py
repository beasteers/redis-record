import os
import datetime
from ...config import *
from ...util import get_recording_filename


class MCAPInfo:
    def list(self, *, info=False, recording_dir=RECORDING_DIR):
        recordings = [
            os.path.splitext(f)[0]
            for f in os.listdir(recording_dir)
        ]
        if info:
            recordings = [self.info(n) for n in recordings]
        return recordings
    
    def info(self, name, recording_dir=RECORDING_DIR):
        from mcap.reader import make_reader
        fname = get_recording_filename(name, recording_dir)
        with open(fname, "rb") as f:
            reader = make_reader(f)
            s = reader.get_summary()
            stat = s.statistics
            
            t0 = stat.message_start_time / 10e8 # FIXME: ????????
            t1 = stat.message_end_time / 10e8
            return {
                "name": name,
                "start_time": t0,
                "end_time": t1,
                "start_datetime": datetime.datetime.fromtimestamp(t0).strftime('%c'),
                "end_datetime": datetime.datetime.fromtimestamp(t1).strftime('%c'),
                "streams": [
                    {
                        "name": c.topic,
                        "count": stat.channel_message_counts[c.id]
                    }
                    for c in s.channels.values()
                ],
                # "n_chunks": len(s.chunk_indexes),
                # "chunks": [c.chunk_length for c in s.chunk_indexes],
            }
