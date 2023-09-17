import time
import json
import tqdm
import base64
import redis
from mcap.reader import make_reader

from ..config import *
from ..util import get_recording_filename




def replay(name, host=HOST, port=PORT, db=DB, realtime=True, speed_fudge=1, recording_dir=RECORDING_DIR):
    fname = get_recording_filename(name, recording_dir)

    r = redis.Redis(host=host, port=port, db=db)

    pbar = tqdm.tqdm()
    t0 = 0
    with open(fname, "rb") as f:
        reader = make_reader(f)
        print(reader.get_header())
        for schema, channel, message in reader.iter_messages():
            args = json.loads(message.data)
            stream_id = args['stream_id']
            data = {k: base64.b64decode(x.encode()) for k, x in args['data'].items()}
            t1 = message.publish_time*10e-9 * 10e-3 # for some reason it's -12 not -9??

            # real-time
            if realtime:
                delay = max(t1 - t0, 0)
                if delay > 1:
                    pbar.set_description(f'sleeping for {delay}s {t1} {stream_id} - {t0}')
                if t0 and delay:
                    time.sleep(delay/speed_fudge) # FIXME recalc speed accounting for lost time. /speed_fudge is a quick fix.
                t0 = t1

            pbar.update()
            pbar.set_description(f'{t1:.3f} {stream_id}')
            r.xadd(stream_id, data, '*') # t1


def cli():
    import fire
    fire.Fire(replay)

if __name__ == '__main__':
    cli()