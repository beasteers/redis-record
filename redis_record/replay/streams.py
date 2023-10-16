import time
import json
import tqdm
import base64
import redis

from ..config import *
from ..util import get_recording_filename
from .sync import Sync
from ..storage_formats.replay import get_player



def replay(name, host=HOST, port=PORT, db=DB, realtime=True, speed_fudge=1, recording_type='mcap', recording_dir=RECORDING_DIR):
    r = redis.Redis(host=host, port=port, db=db)
    sync = Sync(speed_fudge=speed_fudge)

    pbar = tqdm.tqdm()
    with get_player(recording_type, name, recording_dir) as reader:
        for stream_id, ts, data in reader.iter_messages():
            if realtime:
                sync.sync(ts)

            pbar.update()
            pbar.set_description(f'{ts:.3f} {stream_id}')
            r.xadd(stream_id, data, '*') # t1


def cli():
    import fire
    fire.Fire(replay)

if __name__ == '__main__':
    cli()