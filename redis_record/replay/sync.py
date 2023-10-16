import time


class Sync:
    def __init__(self, speed_fudge=1):
        self.speed_fudge = speed_fudge
        self.t0 = None

    def start(self, timestamp):
        self.t0 = self.tproc = time.time()
        self.tpub0 = timestamp

    def sync(self, timestamp):
        if self.t0 is None:
            self.start(timestamp)

        ti = time.time()
        # estimate amount of time to sleep
        data_time_since_start = timestamp - self.tpub0
        real_time_since_start = ti - self.t0
        process_time = ti - self.tproc
        delay = max(data_time_since_start - real_time_since_start - process_time, 0)
        if delay:
            time.sleep(delay / self.speed_fudge)
        
        # update for next iteration
        self.tpub = timestamp
        self.tproc = time.time()
