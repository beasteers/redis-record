import tqdm
import queue
import redis
import logging

from ..config import *
from ..util import read_latest
from ..sync import Sync
from ..storage.replay import get_player

log = logging.getLogger(__name__)

def replay_once(name, host=HOST, port=PORT, db=DB, realtime=True, speed_fudge=1, recording_type=STORAGE_FORMAT, recording_dir=RECORDING_DIR):
    r = redis.Redis(host=host, port=port, db=db)
    sync = Sync(speed_fudge=speed_fudge)

    pbar = tqdm.tqdm()
    with get_player(name, recording_dir, type=recording_type) as reader:
        for stream_id, ts, data in reader.iter_messages():
            if realtime:
                sync.sync(ts)

            pbar.update()
            pbar.set_description(f'{ts:.3f} {stream_id}')
            r.xadd(stream_id, data, '*') # t1

def replay(
        name=None,
        replay_key=REPLAY_KEY, 
        seek_key=REPLAY_SEEK_KEY,
        pause_key=REPLAY_PAUSE_KEY,
        recording_dir=RECORDING_DIR, 
        wait_block=3000,
        realtime=True, speed_fudge=1,
        single_recording=None, recording_type=STORAGE_FORMAT,
        host=HOST, port=PORT, db=DB
):
    if single_recording is None:
        single_recording = bool(name)
    if single_recording:
        return replay_once(name, host=host, port=port, db=db, realtime=realtime, speed_fudge=speed_fudge, recording_type=recording_type, recording_dir=recording_dir)

    r = redis.Redis(host=host, port=port, db=db)
    sync = Sync(speed_fudge=speed_fudge)
    pbar = tqdm.tqdm()

    player = None
    record_name = name
    paused = False
    seek = 0
    rec_cursor = {replay_key: '0'}
    while True:
        # ---------------------- Watch for changes in recording ---------------------- #

        # query for recording name stream
        results, rec_cursor = read_latest(r, rec_cursor, block=False if record_name else wait_block)

        # check for recording changes
        for sid, xs in results:
            if sid == replay_key:
                for t, x in xs[-1:]:
                    if player is not None:
                        player.close()
                        player = None
                    record_name = x[b'd'].decode() or None if x else None
                    paused = int(x.get(b'pause', b'0').decode() or 0)
                    seek = int(x.get(b'seek', b'0').decode() or 0)
                    if record_name:
                        log.info(f"new replay request: {record_name}")
            if sid == seek_key and player is not None:
                player.seek(int(x[b'd'].decode() if x else None or 0))
            if sid == pause_key:
                paused = int(x[b'd'].decode() if x else None or 0)

        if not record_name or paused:        
            continue

        if player is None:
            log.info(f'new ({recording_type}) player: {record_name} from {recording_dir}')
            try:
                player = get_player(record_name, recording_dir, type=recording_type)
            except FileNotFoundError as e:
                log.warning(f"File not Found: {e}")
                r.xadd(replay_key, {b'd': b''}, '*')
                continue
            if seek:
                player.seek(seek)
        

        msg = player.next_message()            
        if msg is None:
            log.info(f"Finished replaying recording: {record_name}")
            record_name = None
            r.xadd(replay_key, {b'd': b''}, '*')
            continue
        stream_id, ts, data = msg

        if realtime:
            sync.sync(ts)

        pbar.update()
        pbar.set_description(f'{ts:.3f} {stream_id}')
        r.xadd(stream_id, data, '*') # t1


def cli():
    import logging
    from tqdm.contrib.logging import logging_redirect_tqdm
    import fire
    logging.basicConfig(level=logging.DEBUG)
    with logging_redirect_tqdm():
        fire.Fire(replay)

if __name__ == '__main__':
    cli()