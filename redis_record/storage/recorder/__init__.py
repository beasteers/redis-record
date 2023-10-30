from redis_record.config import STORAGE_FORMAT


def get_recorder(*a, type=STORAGE_FORMAT, **kw):
    # XXX: not extensible
    if type == 'mcap':
        from .mcap import MCAPRecorder
        return MCAPRecorder(*a, **kw)
    if type == 'zip':
        from .zip import ZipRecorder
        return ZipRecorder(*a, **kw)
    
    raise ValueError(f"Unknown recorder type: {type}")