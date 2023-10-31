import os
import glob
import zipfile
import queue
from fnmatch import fnmatch

from redis_record.util import parse_epoch_time
from redis_record.config import RECORDING_DIR

import logging

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class ZipPlayer:
    def __init__(self, path, recording_dir=RECORDING_DIR, subset=None, raw_timestamp=None):
        self.recording_dir = path if recording_dir is None else os.path.join(recording_dir, path)
        self.subset = subset if isinstance(subset, (list, tuple, set)) else [subset] if subset else []
        self.file_index = {}
        self.file_cursor = {}
        self.time_cursor = 0
        self.zipfh = {}
        self.file_end_timestamps = {}
        self.queue = queue.PriorityQueue()
        self.raw_timestamp = raw_timestamp
        log.info("Created Player: %s - streams: %s", self.recording_dir, self.subset or 'all')

        self._load_file_index()
        for stream_id in self.file_index:
            self._queue_next_file(stream_id)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __iter__(self):
        yield from self.iter_messages()

    def seek(self, timestamp):
        self.close()  # TODO: do this more efficiently. the problem is selectively clearing the queue.
        for sid, fs in self.file_index.items():
            for i, (_, start, end) in enumerate(fs):
                if timestamp < end:
                    self._queue_file(sid, i)
                    break
        self.time_cursor = timestamp

    def next_message(self):
        # get next message
        while True:
            try:
                _, (stream_id, ts) = self.queue.get(block=False)
            except queue.Empty:
                return
            tx = parse_epoch_time(ts)
            if tx >= self.time_cursor or 0:
                # log.debug("using timestamp: %s", ts)
                break
            # log.debug("skipping timestamp: %s", ts)

        # load data
        self.time_cursor = tx
        with self.zipfh[stream_id].open(ts, 'r') as f:
            data = f.read()
        # possibly load next file
        if ts >= self.file_end_timestamps[stream_id]:
            self._queue_next_file(stream_id)
        tx = ts if self.raw_timestamp else tx
        return stream_id, tx, {'d': data}

    def iter_messages(self):
        msg = self.next_message()
        while msg:
            yield msg
            msg = self.next_message()

    def close(self):
        self.time_cursor = 0
        self.queue.queue.clear()
        for zf in self.zipfh.values():
            zf.close()
        self.zipfh.clear()
        log.info("Closed Player: %s - streams: %s", self.recording_dir, self.subset or 'all')

    def _get_time_range_from_file(self, fname):
        t0, t1 = fname.split(os.sep)[-1].removesuffix('.zip').split('_')
        return t0, t1

    def _load_file_index(self):
        self.file_index = {
            stream_id: [
                (f, *self._get_time_range_from_file(f))
                for f in sorted(glob.glob(os.path.join(self.recording_dir, stream_id, '*.zip')))
            ]
            for stream_id in os.listdir(self.recording_dir)
            if not self.subset or any(fnmatch(stream_id, p) for p in self.subset)
        }
        self.file_cursor = {s: -1 for s in self.file_index}
        log.debug('File Index: %s', self.file_index)
        log.debug('File Cursor: %s', self.file_cursor)

    def _queue_next_file(self, stream_id):
        self._queue_file(stream_id, self.file_cursor[stream_id] + 1)

    def _queue_file(self, stream_id, index):
        # close previous file
        if self.zipfh.get(stream_id) is not None:
            log.debug("closing opened file: %s", stream_id)
            self.zipfh.pop(stream_id).close()
        # check if we're done with this stream
        if index >= len(self.file_index[stream_id]):
            log.debug("finished stream: %s", stream_id)
            return
        
        # load the zipfile
        fname, _, _ = self.file_index[stream_id][index]
        log.debug("queueing file: %s", fname)
        self.file_cursor[stream_id] = index
        self.zipfh[stream_id] = zf = zipfile.ZipFile(fname, 'r', zipfile.ZIP_STORED, False)
        # load the file list
        ts = sorted(set(zf.namelist()))
        if not ts:
            log.debug("no data in file: %s", fname)
            self.zipfh[stream_id].close()
            return 
        self.file_end_timestamps[stream_id] = ts[-1]

        # queue up the timestamps
        log.debug("putting %d timestamps - up to %s", len(ts), ts[-1])
        for t in ts:
            tx = parse_epoch_time(t)
            self.queue.put((int(tx*1e6), (stream_id, t)))


def replay(name, *a, **kw):
    with ZipPlayer(name, *a, **kw) as player:
        for sid, t, data in player.iter_messages():
            logging.info('%s %s %s', sid, t, data)

def cli():
    import logging
    from tqdm.contrib.logging import logging_redirect_tqdm
    import fire
    logging.basicConfig(level=logging.DEBUG)
    with logging_redirect_tqdm():
        fire.Fire(replay)

if __name__ == '__main__':
    cli()