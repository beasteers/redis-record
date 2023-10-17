import os
import glob
import zipfile
import queue

from redis_record.util import parse_epoch_time


class ZipPlayer:
    def __init__(self, path, recording_dir):
        self.recording_dir = path if os.path.exists(path) else os.path.join(recording_dir, path)
        self.file_index = {}
        self.zipfh = {}
        self.last_timestamps = {}
        self.queue = queue.PriorityQueue()

        self._load_file_index()
        for stream_id in self.file_index:
            self._queue_next_file(stream_id)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def next_message(self):
        # get next message
        _, (stream_id, ts) = self.queue.get(block=False)

        # load data
        with self.zipfh[stream_id].open(ts, 'r') as f:
            data = f.read()
        tx = parse_epoch_time(ts)
        # possibly load next file
        if ts >= self.last_timestamps[stream_id]:
            self._queue_next_file(stream_id)
        return stream_id, tx, {'d': data}

    def iter_messages(self):
        try:
            while True:
                yield self.next_message()
        except queue.Empty:
            pass

    def close(self):
        for zf in self.zipfh.values():
            zf.close()
        self.zipfh.clear()


    def _load_file_index(self):
        self.file_index = {
            stream_id: sorted(glob.glob(os.path.join(self.recording_dir, stream_id, '*.zip')))
            for stream_id in os.listdir(self.recording_dir)
        }

    def _queue_next_file(self, stream_id):
        if self.zipfh.get(stream_id) is not None:
            self.zipfh[stream_id].close()
        if not self.file_index[stream_id]:
            return
        
        # load the zipfile and file list
        fname = self.file_index[stream_id].pop()
        self.zipfh[stream_id] = zf = zipfile.ZipFile(fname, 'r', zipfile.ZIP_STORED, False)
        ts = sorted(zf.namelist())
        if not ts:
            self.zipfh[stream_id].close()
            return 
        self.last_timestamps[stream_id] = ts[-1]

        # queue up the timestamps
        for t in ts:
            tx = parse_epoch_time(t)
            self.queue.put((int(tx*1e6), (stream_id, t)))
