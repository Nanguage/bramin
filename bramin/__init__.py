__version__ = '0.0.1'

from .pipe import Pipe, END
from .pipe import placeholder
from .curry import curry

it = placeholder
P = Pipe

from .patch import patch_all

patch_all()

__all__ = ['P', 'it', 'END', 'curry']
