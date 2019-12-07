import io
import gzip
from typing import Callable, List, Iterable, Optional
from collections import namedtuple
import inspect


class FileType(object):
    def __init__(self, name: str,
                 matcher: Callable[[str], bool],
                 opener: Callable,
                 reader: Callable,
                 writer: Callable):
        self.name = name
        self.matcher = matcher
        self.opener = opener
        self.reader = reader
        self.writer = writer


class callable_file(object):
    """Represent file as a callable object.
    Open file automatically according to it's filename.

    Example write:
    >>> fw = callable_file("/tmp/bramin_test.txt", "w")
    >>> fw(["123", "456"])  # write file with a function call
    '/tmp/bramin_test.txt'
    >>> with open("/tmp/bramin_test.txt", 'r') as f:
    ...     f.read()
    '123456'

    Example read:
    >>> fr = callable_file("/tmp/bramin_test.txt")
    >>> list(fr())  # read file with a function call
    ['123456']
    """

    file_types: List[FileType] = []

    def __init__(self, fname: str, *args, **kwargs):
        for ftype in reversed(self.file_types):
            if ftype.matcher(fname):
                self._args = (fname, args, kwargs)
                self._ftype = ftype
                break
        else:
            raise IOError(
                f"Could not found any registered file type match {fname}")

    def __call__(self, contents: Optional[Iterable] = None):
        fname, args, kwargs = self._args
        mode = self._get_mode(self._ftype.opener, args, kwargs)
        if len(args) > 0:
            args = args[1:]
        kwargs['mode'] = mode

        fh = self._ftype.opener(fname, *args, **kwargs)
        if 'r' in mode:  # read from file
            return self._read_file(fh)
        else:            # write to file
            self._ftype.writer(fh, contents)
            fh.close()
            return fname

    @staticmethod
    def _get_mode(func, args, kwargs) -> str:
        if len(args) > 0:
            mode = args[0]
        elif 'mode' in kwargs:
            mode = kwargs['mode']
        else:
            sig = inspect.signature(func)
            mode = sig.parameters['mode'].default
        return mode

    def _read_file(self, fh) -> Iterable:
        for rec in self._ftype.reader(fh):
            yield rec
        fh.close()

    @classmethod
    def register(cls, file_type: FileType):
        """Register a filetype"""
        cls.file_types.append(file_type)

    @classmethod
    def unregister(clf, name: str):
        """Register a filetype"""
        for idx in range(len(clf.file_types)-1, -1, -1):
            tp = clf.file_types[idx]
            if tp.name == name:
                clf.file_types.pop(idx)
                break


def _write_text(fh, lines):
    for l in lines:
        fh.write(l)


text_file = FileType(
    "text",
    lambda fname: True,
    open,
    lambda fh: fh,
    _write_text
)


callable_file.register(text_file)


gzipped_text = FileType(
    "gzipped_text",
    lambda fname: fname.endswith('.gz'),
    gzip.open,
    lambda fh: io.TextIOWrapper(fh),
    lambda fh, lines: _write_text(io.TextIOWrapper(fh), lines)
)
