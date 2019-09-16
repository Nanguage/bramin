from functools import wraps


def patch_op(obj, op):
    from .pipe import Pipe
    real = getattr(obj, op)
    @wraps(real)
    def fake(self, other):
        if other is Pipe:
            return NotImplemented
        else:
            return real(self, other)
    setattr(obj, op, fake)
    return obj


def patch(obj):
    """substitute __or__ method, for use 'obj | P | func' synatax"""
    patch_op(obj, '__or__')


def patch_all():
    # patch pandas
    try:
        import pandas as pd
        patch(pd.DataFrame)
        patch(pd.Series)
        patch(pd.Index)
    except ImportError:
        pass
