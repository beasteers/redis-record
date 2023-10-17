import time


class Sync:
    def __init__(self, speed_fudge=1):
        self.speed_fudge = speed_fudge
        self.t0 = self.tproc = self.tpub0 = self.tpub = 0

    def clear(self):
        self.t0 = self.tproc = self.tpub0 = self.tpub = None

    def start(self, timestamp):
        self.t0 = self.tproc = time.time()
        self.tpub0 = self.tpub = timestamp

    def wait_time(self, timestamp):
        if self.t0 is None:
            self.start(timestamp)

        ti = time.time()
        # estimate amount of time to sleep
        data_time_since_start = timestamp - self.tpub0
        real_time_since_start = ti - self.t0
        process_time = ti - self.tproc
        delay = max(data_time_since_start - real_time_since_start - process_time, 0)
        return delay

    def sync(self, timestamp):
        delay = self.wait_time(timestamp)
        if delay:
            time.sleep(delay / self.speed_fudge)
        
        # update for next iteration
        self.tpub = timestamp
        self.tproc = time.time()


class Timer(Sync):
    def __init__(self, rate=None):
        self.delta = 1/rate
        super().__init__()

    def wait_time(self, timestamp=None):
        return super().wait_time(self.tpub + self.delta)
    
    def sync(self, timestamp=None):
        return super().sync(self.tpub + self.delta)
    
    def nowait_sync(self, timestamp=None):
        if not self.wait_time(timestamp):
            self.sync(timestamp)