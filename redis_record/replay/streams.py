import tqdm
import queue
import redis

from ..config import *
from ..util import read_latest
from .sync import Sync, Timer
from ..storage_formats.replay import get_player



def replay_once(name, host=HOST, port=PORT, db=DB, realtime=True, speed_fudge=1, recording_type='mcap', recording_dir=RECORDING_DIR):
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

def replay(
        name=None,
        replay_key=REPLAY_KEY, recording_dir=RECORDING_DIR, 
        wait_block=3000,
        realtime=True, speed_fudge=1,
        single_recording=None, recording_type='mcap',
        host=HOST, port=PORT, db=DB
):
    if single_recording is None:
        single_recording = bool(name)
    if single_recording:
        return replay_once(name, host=host, port=port, db=db, realtime=realtime, speed_fudge=speed_fudge, recording_type=recording_type, recording_dir=recording_dir)

    r = redis.Redis(host=host, port=port, db=db)
    sync = Sync(speed_fudge=speed_fudge)
    # timer = Timer(3)
    pbar = tqdm.tqdm()

    player = None
    record_name = name
    rec_cursor = {replay_key: '0'}
    while True:
        # ---------------------- Watch for changes in recording ---------------------- #

        # query for recording name stream
        # if timer.nowait_sync():
        results, rec_cursor = read_latest(r, rec_cursor, block=False if record_name else wait_block)

        # check for recording changes
        for sid, xs in results:
            if sid == replay_key:
                for t, x in xs[-1:]:
                    if player is not None:
                        player.close()
                        player = None
                    record_name = x[b'd'].decode() or None if x else None
                    print(f"new replay request: {record_name}")

        if not record_name:        
            continue

        if player is None:
            print('new player', recording_type, record_name, recording_dir)
            player = get_player(recording_type, record_name, recording_dir).__enter__()
        
        try:
            stream_id, ts, data = player.next_message()
        except (StopIteration, queue.Empty): # fixme
            tqdm.tqdm.write(f"Finished replaying recording: {record_name}")
            record_name = None
            r.xadd(replay_key, {b'd': b''}, '*')
            continue

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