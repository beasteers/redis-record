import time
import datetime
import asyncio
import logging

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

class Sync:
    def __init__(self, speed_fudge=1, warn_above=10):
        self.speed_fudge = speed_fudge
        self.t0 = self.tproc = self.tpub0 = self.tpub = 0
        self.warn_above = warn_above

    def clear(self):
        self.t0 = self.tproc = self.tpub0 = self.tpub = 0

    def start(self, timestamp):
        self.t0 = self.tproc = time.time()
        self.tpub0 = self.tpub = timestamp

    def wait_time(self, timestamp):
        if self.t0 == 0:
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
            self._warn(timestamp, delay)
            time.sleep(delay / self.speed_fudge)
        
        # update for next iteration
        self.tpub = timestamp
        self.tproc = time.time()

    async def sync_async(self, timestamp):
        delay = self.wait_time(timestamp)
        if delay:
            self._warn(timestamp, delay)
            await asyncio.sleep(delay / self.speed_fudge)
        
        # update for next iteration
        self.tpub = timestamp
        self.tproc = time.time()

    def _warn(self, timestamp, delay):
        if delay > self.warn_above:
            log.warning(
                f"Sleeping for {delay:.3f} seconds. \n"
                f"Simulating {datetime.datetime.fromtimestamp(self.tpub).strftime('%H:%M:%S.%f')} - {datetime.datetime.fromtimestamp(timestamp).strftime('%H:%M:%S.%f')}")


class Clock(Sync):
    def __init__(self, rate=None):
        self.delta = 1/rate if rate else 0
        super().__init__()

    def wait_time(self, timestamp=None):
        if not self.delta: return 0
        return super().wait_time(self.tpub + self.delta)
    
    def sync(self, timestamp=None):
        return super().sync(self.tpub + self.delta)
    
    async def sync_async(self, timestamp=None):
        return await super().sync_async(self.tpub + self.delta)
    
    def nowait_sync(self, timestamp=None):
        if not self.wait_time(timestamp):
            self.sync(timestamp)



if __name__ == '__main__':
    def test(rate=3):
        import tqdm
        pbar = tqdm.tqdm()
        sync = Clock(rate)
        while True:
            pbar.update()
            sync.sync()
    import fire
    fire.Fire(test)