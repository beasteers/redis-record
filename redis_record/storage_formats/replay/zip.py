import os
import glob
import zipfile
import queue
from fnmatch import fnmatch

from redis_record.util import parse_epoch_time


class ZipPlayer:
    def __init__(self, path, recording_dir, subset=None):
        self.recording_dir = path if os.path.exists(path) else os.path.join(recording_dir, path)
        self.subset = subset if isinstance(subset, (list, tuple, set)) else [subset] if subset else []
        self.file_index = {}
        self.file_cursor = {}
        self.time_cursor = 0
        self.zipfh = {}
        self.file_end_timestamps = {}
        self.queue = queue.PriorityQueue()

        self._load_file_index()
        for stream_id in self.file_index:
            self._queue_next_file(stream_id)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

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
            _, (stream_id, ts) = self.queue.get(block=False)
            tx = parse_epoch_time(ts)
            if tx >= self.time_cursor or 0:
                break

        # load data
        self.time_cursor = tx
        with self.zipfh[stream_id].open(ts, 'r') as f:
            data = f.read()
        # possibly load next file
        if ts >= self.file_end_timestamps[stream_id]:
            self._queue_next_file(stream_id)
        return stream_id, tx, {'d': data}

    def iter_messages(self):
        try:
            while True:
                yield self.next_message()
        except queue.Empty:
            pass

    def close(self):
        self.time_cursor = 0
        self.queue.queue.clear()
        for zf in self.zipfh.values():
            zf.close()
        self.zipfh.clear()

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
        self.file_cursor = {s: 0 for s in self.file_index}

    def _queue_next_file(self, stream_id):
        self._queue_file(stream_id, self.file_cursor[stream_id] + 1)

    def _queue_file(self, stream_id, index):
        # close previous file
        if self.zipfh.get(stream_id) is not None:
            self.zipfh.pop(stream_id).close()
        # check if we're done with this stream
        if index >= len(self.file_index[stream_id]):
            return
        
        # load the zipfile
        fname, _, _ = self.file_index[stream_id][index]
        self.file_cursor[stream_id] = index
        self.zipfh[stream_id] = zf = zipfile.ZipFile(fname, 'r', zipfile.ZIP_STORED, False)
        # load the file list
        ts = sorted(zf.namelist())
        if not ts:
            self.zipfh[stream_id].close()
            return 
        self.file_end_timestamps[stream_id] = ts[-1]

        # queue up the timestamps
        for t in ts:
            tx = parse_epoch_time(t)
            self.queue.put((int(tx*1e6), (stream_id, t)))
