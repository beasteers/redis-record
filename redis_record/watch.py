import redis
from redis_record.record.monitor import Monitor
from .config import *

def watch(host=HOST, port=PORT, db=DB, charlimit=30):
    with redis.Redis(host=host, port=port, db=db) as r:
        with Monitor(r.connection_pool) as m:
            for data in m.listen():
                cmd_items = data['args']
                print(*[x[:charlimit] for x in cmd_items], max(len(x) for x in cmd_items))


def cli():
    import fire
    fire.Fire(watch)

if __name__ == '__main__':
    cli()