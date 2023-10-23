import redis
import tqdm
from .config import *
from .sync import Clock

def data(stream_id='fake_data', size=1000, rate=None, payload={}, maxlen=1000, limit=None, r=None, host=HOST, port=PORT, db=DB):
    sync = Clock(rate)
    with (r or redis.Redis(host=host, port=port, db=db)) as r:
        pbar = tqdm.tqdm()
        i = 0
        while True:
            x = b'0'*size
            r.xadd(stream_id, {RECORD_XADD_DATA_FIELD: x, **payload}, id='*', maxlen=maxlen)
            pbar.update()
            sync.sync()
            i += 1
            if limit and i > limit:
                break

def cli():
    import fire
    fire.Fire(data)

if __name__ == '__main__':
    cli()