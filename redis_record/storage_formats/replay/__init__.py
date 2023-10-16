


def get_player(type, *a, **kw):
    # XXX: not extensible
    if type == 'mcap':
        from .mcap import MCAPPlayer
        return MCAPPlayer(*a, **kw)
    if type == 'zip':
        from .zip import ZipPlayer
        return ZipPlayer(*a, **kw)
    
    raise ValueError(f"Unknown recorder type: {type}")