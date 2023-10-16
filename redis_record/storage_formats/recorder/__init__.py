


def get_recorder(type, *a, **kw):
    # XXX: not extensible
    if type == 'mcap':
        from .mcap import MCAPRecorder
        return MCAPRecorder(*a, **kw)
    if type == 'zip':
        from .zip import ZipRecorder
        return ZipRecorder(*a, **kw)
    
    raise ValueError(f"Unknown recorder type: {type}")