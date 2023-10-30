# Class to record all desired redis activity
import os
import base64
import re
import tqdm
import codecs
import redis
from redis.client import Monitor as Monitor_

from .. import util
from ..storage.recorder import get_recorder
from ..config import *
from .. import cmd




class Monitor(Monitor_):
    monitor_re = re.compile(rb"\[(\d+) (.*?)\] (.*)")
    command_re = re.compile(rb'"(.*?(?<!\\))"')
    def next_command(self):
        """Parse the response from a monitor command"""
        # https://github.com/redis/redis/blob/4031a187321be26fc96c044fec3ee759841e8379/src/replication.c#L576
        response = self.connection.read_response(disable_decoding=True)
        command_time, command_data = response.split(b" ", 1)
        db_id, client_info, raw_command = self.monitor_re.match(command_data).groups()
        command_parts = self.command_re.findall(raw_command)  # TODO: this is slow
        command_parts = [codecs.escape_decode(x)[0] for x in command_parts]

        client_info = client_info.decode()
        if client_info == "lua":
            client_address = client_type = "lua"
            client_port = ""
        else:
            client_address, client_port = client_info.rsplit(":", 1)  # ipv6 has colons
            client_type = "unix" if client_info.startswith("unix") else "tcp"
        return {
            "time": float(command_time.decode()),
            "db": int(db_id.decode()),
            "client_address": client_address,
            "client_port": client_port,
            "client_type": client_type,
            "args": command_parts,
        }



def record(
        name=None, record_key=MONITOR_KEY, record_cmds=MONITOR_CMDS, 
        out_dir=RECORDING_DIR, single_recording=None, recording_type='mcap',
        host=HOST, port=PORT, db=DB,
    ):
    '''Record all commands using MONITOR command.
    
    Arguments:
        name (str): name of the recording. Only use this if you want to start a recording when the script begins.
        record_key (str): the key in redis used to store the recording name.
        record_cmds (list[str]): the redis commands to record.
        out_dir (str): the directory to write recordings to.
    '''
    record_name = name
    single_recording = bool(name) if single_recording is None else single_recording

    pbar = tqdm.tqdm()

    record_cmds = [c.lower() for c in record_cmds]
    tqdm.tqdm.write(f"Monitoring commands: {record_cmds}")

    r = redis.Redis(host=host, port=port, db=db, decode_responses=False)
    try:
        with get_recorder(type=recording_type, schema={ "cmd": { "type": "array" } }, out_dir=out_dir) as rec, r:
            if record_name:
                cmd.start_monitoring(r, record_name)

            with Monitor(r.connection_pool) as m:
                # look up the initial recording name
                record_name = (r.get(record_key) or b'').decode()
                tqdm.tqdm.write(f"recording name: {record_name}")

                for data in m.listen():
                    # parse command
                    cmd_items = data['args']
                    if not cmd_items:  # rare parsing problems
                        continue
                    cmd_name = cmd_items[0].decode().lower()
                    if cmd_name not in CMD_IGNORE_DISPLAY:
                        pbar.set_description(cmd_name)

                    # listen for delete key
                    if cmd_name == 'del':
                        for key in cmd_items[1:]:
                            if key == record_key:
                                rec.close()
                                record_name = None
                                print("ended recording")
                                continue

                    # listen for set key
                    if cmd_name == 'set':
                        key, value = cmd_items[1:3]
                        if key == record_key and record_name != value:
                            rec.close()
                            record_name = value
                            print("new recording:" if record_name else "ended recording", record_name)
                            continue
                    
                    # no recording
                    if not record_name:
                        continue
                    
                    # make sure a writer is open
                    rec.ensure_writer(record_name)
                    if cmd_name not in record_cmds:
                        continue

                    # pick which channel to write to
                    if cmd_name in {'set', 'xadd'}:
                        sid = b'::'.join(cmd_items[:2]).decode()
                    else:
                        sid = cmd_items[0].decode()

                    # write command to file
                    rec.write(sid, data['time'], prepare_data(cmd_items))
                    pbar.update()
    finally:
        if single_recording:
            cmd.stop_monitoring(r)


def prepare_data(cmd_items):
    return {"cmd": [base64.b64encode(x).decode() for x in cmd_items]}



def cmd():
    import fire
    fire.Fire(record)

if __name__ == '__main__':
    from pyinstrument import Profiler
    p = Profiler()
    try:
        with p:
            cmd()
    finally:
        p.print()
