from redis_record.config import STORAGE_FORMAT


def get_player(*a, type=STORAGE_FORMAT, **kw):
    # XXX: not extensible
    if type == 'mcap':
        from .mcap import MCAPPlayer
        return MCAPPlayer(*a, **kw)
    if type == 'zip':
        from .zip import ZipPlayer
        return ZipPlayer(*a, **kw)
    
    raise ValueError(f"Unknown recorder type: {type}")