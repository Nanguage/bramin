from .pipe import Pipe, END
from .pipe import placeholder

_x_ = placeholder
P = Pipe

from .patch import patch_all

patch_all()

__all__ = ['P', '_x_', 'END']
