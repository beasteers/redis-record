from __future__ import annotations
import os
import datetime
from .config import *

import logging
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def maybe_encode(s: str|bytes, encoding='utf-8'):
    '''If the input is str, encode as utf-8 (or other).'''
    return s.encode(encoding) if isinstance(s, str) else s

def maybe_decode(s: str|bytes, encoding='utf-8'):
    '''If the input is bytes, decode as utf-8 (or other).'''
    return s.decode(encoding) if isinstance(s, bytes) else s

# ---------------------------------------------------------------------------- #
#                               Timestamp parsing                              #
# ---------------------------------------------------------------------------- #


def parse_epoch_time(tid: str|bytes):
    '''Convert a redis timestamp to epoch seconds.'''
    return int(maybe_decode(tid).split('-')[0])/1000

def format_epoch_time(tid: float, i='0'):
    '''Format a redis timestamp from epoch seconds.'''
    return f'{int(tid * 1000)}-{i}'

def parse_datetime(tid: str|bytes):
    '''Convert a redis timestamp to a datetime object.'''
    return datetime.datetime.fromtimestamp(parse_epoch_time(tid))

def format_datetime(dt: datetime.datetime):
    '''Format a redis timestamp from a datetime object.'''
    return format_epoch_time(dt.timestamp())

def format_iso(tid: str|bytes, format: str=''):
    '''Convert a redis timestamp to a iso format.'''
    if not format:
        return parse_datetime(tid).strftime(format)
    return parse_datetime(tid).isoformat()

def nonspecific_timestamp(tid: str|bytes):
    return f"{maybe_decode(tid).split('-')[0]}-*"

# ---------------------------------------------------------------------------- #
#                                Data formatting                               #
# ---------------------------------------------------------------------------- #

def pack_entries(entries):
    offsets = []
    content = bytearray()
    for sid, data in entries:
        sid = maybe_decode(sid)
        for ts, d in data:
            content += d[b'd']
            offsets.append((sid, maybe_decode(ts), len(content)))
    # jsonOffsets = orjson.dumps(offsets).decode('utf-8')
    return offsets, content

def decode_xread_format(data):
    return [
        (maybe_decode(s), [(maybe_decode(t), x) for t, x in xs])
        for s, xs in data
    ]


# ---------------------------------------------------------------------------- #
#                                 Redis Reading                                #
# ---------------------------------------------------------------------------- #


def read_next(r, sids, block=0, count=1, **kw):
    data = r.xread(sids, block=block, count=count, **kw)
    data = decode_xread_format(data)
    sids = update_cursor(sids, data)
    return data, sids

def read_latest(r, sids, block=False, count=1, **kw):
    with r.pipeline() as p:
        for sid, t in sids.items():
            p.xrevrange(sid, '+', f'({t}', count=count, **kw)
        data = list(zip(sids, p.execute()))
    if block and not any(x for s, x in data):
        data = r.xread(sids, block=block, count=count, **kw)
    data = decode_xread_format(data)
    sids = update_cursor(sids, data)
    return data, sids


def update_cursor(sids: dict[str, str], data: list[str|tuple]) -> dict[str, str]:
    for s, ts in data:
        if ts:
            sids[s] = max(t for t, x in ts)
    return sids


# --------------------------------- Recording -------------------------------- #


def get_recording_filename(name, recording_dir=RECORDING_DIR):
    if os.path.isfile(name):
        return name
    return os.path.join(recording_dir, f'{name}.mcap')


def move_with_suffix(src, prefix=None, suffix=None, has_ext=None):
    if os.path.exists(src):
        has_ext = os.path.isfile(src) if has_ext is None else has_ext
        if has_ext:
            base, ext = os.path.splitext(src)
        else:
            base, ext = src, ''
        base = f"{prefix or ''}{base}{suffix or ''}"

        i = 1
        dest = f"{base}_{i}{ext}"
        while os.path.exists(dest):
            i += 1
            dest = f"{base}_{i}{ext}"
        log.info("MOVING %s to %s", src, dest)
        os.rename(src, dest)
