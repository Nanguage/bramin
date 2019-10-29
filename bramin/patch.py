import typing as t
from functools import wraps, partial


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


def patch_all():
    """substitute __or__ method, for use 'obj | P | func' synatax"""
    patch = partial(patch_op, op='__or__')
    # patch pandas
    try:
        import pandas as pd
        patch(pd.DataFrame)
        patch(pd.Series)
        patch(pd.Index)
    except ImportError:
        pass
