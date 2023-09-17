# Redis Record

This lets you record redis streams and commands so that you can replay them easily at a later time.

## Getting Started - Using Python

To install the redis-record package:
```bash
git clone https://github.com/beasteers/redis-record.git
pip install -e ./redis-record
```

### Record

To start an on-demand recording:
```bash
python -m redis_record.record my_recording
```
To stop, just Interrupt the script (Ctrl-C).

This will create a file at `./recordings/my_recording.mcap`.

### Replay

To replay the file into the system, do:
```bash
python -m redis_record.replay my_recording
```

### List

## Getting Started - Using Docker

The recorder is designed to be a long-running process, meaning that you can deploy it as a docker container and just control it using redis commands.

This is useful if you want to be able to control the recording remotely and always have the data save to the same place.

```bash
docker-compose up -d
# to observe the recording process
docker logs redis-record
```

To start a recording, do:
```bash
python -m redis_record start my_second_recording
```

To stop a recording, do:
```bash
python -m redis_record stop my_second_recording
```

Currently, the replay container isn't a long-running container so you still need to invoke it like above:
```bash
python -m redis_record.replay my_recording
```

## Recording more than streams

The previous method is designed to capture XADD commands (data added to Redis streams). If you want to capture 
other redis commands, we can leverage Redis's MONITOR command to capture all commands.

```bash
python redis_record.record.monitor my_other_recording
```

By default, it will capture any of the SET command variants (`xadd, set, hmset, hset, hsetnx, lset, mset, msetnx, psetex, setbit, setrange, setex, setnx, getset, json.set, json.mset`), but it's easy enough to change! 


```bash
python redis_record.record.monitor my_other_recording --record-cmds '[xadd,set]'
```
I was initially going to just do `[xadd,set]` but figured trying to cover a more general use case as a default would be better.

To replay:

```bash
python redis_record.record.monitor my_other_recording
```

## TODOs
 - recording expiration (auto-stop a recording after e.g. 1 minute of inactivity)
 - s3 recording file storage
 - alternative exporters - e.g. mp4 - but would need consistent/general format.
 - persistent replay container - replay key controller
 - replay lock - don't allow two concurrent replays
