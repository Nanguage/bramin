from typing import Union, Optional, Iterable, Tuple
from subprocess import Popen, PIPE
from functools import partial
from itertools import tee
from threading import Thread
import types
import io

from ._utils import (type_error, type_guard)

Popen_ = partial(Popen, shell=True)


ByteOrStr = Union[str, bytes]
ProcessInput = Union[Iterable[ByteOrStr], ByteOrStr]


class subp(object):
    def __init__(self, cmd: str):
        self.cmd = cmd
        self.text_mode = True

    @type_guard
    def __or__(self, right: 'subp') -> 'subp':
        """Allow compose(concat) subp with '|'"""
        cmd = self.cmd + " | " + right.cmd
        return subp(cmd)

    @type_guard
    def __gt__(self, right: str) -> 'subp':
        """Allow redirect output to file."""
        cmd = self.cmd + " > " + right
        return subp(cmd)

    @type_guard
    def __rshift__(self, right: str) -> 'subp':
        """Allow redirect in append mode."""
        cmd = self.cmd + " >> " + right
        return subp(cmd)

    def __call__(self, input_: Optional[ProcessInput] = None) -> Iterable[ByteOrStr]:
        cmd = self.cmd
        t = None

        # dispatch Popen according to input type
        if input_ is None:
            p = Popen_(cmd, stdout=PIPE)
            stdout = self._fh_wrapper(p.stdout)
        elif isinstance(input_, Iterable) and (not isinstance(input_, (str, bytes))):
            input_, elm_tp = self._get_elm_type(input_)
            if elm_tp is bytes:
                self.text_mode = False
            elif elm_tp is not str:
                raise self._subp_tp_err(Iterable[elm_tp])
            p = Popen_(cmd, stdin=PIPE, stdout=PIPE)
            # write the stdin using another thread, for non-blocking IO
            stdin = self._fh_wrapper(p.stdin)

            def write_to_stdin(p):
                for line in input_:
                    stdin.write(line)
                stdin.close()
            t = Thread(target=write_to_stdin, args=(p,))
            t.start()
            stdout = self._fh_wrapper(p.stdout)
        elif type(input_) is str:
            p = Popen_(cmd, stdin=PIPE, stdout=PIPE)
            _o, _ = p.communicate(input=input_.encode('utf-8'))
            stdout = io.StringIO(_o.decode('utf-8'))
        elif type(input_) is bytes:
            self.text_mode = False
            p = Popen_(cmd, stdin=PIPE, stdout=PIPE)
            _o, _ = p.communicate(input=input_)
            stdout = io.BytesIO(_o)
        else:
            raise self._subp_tp_err(type(input_))

        for line in stdout:
            yield line

        if t:
            t.join()
        p.terminate()

    def _fh_wrapper(self, fh):
        """wrap the file handler if in text_mode."""
        if self.text_mode:
            return io.TextIOWrapper(fh)
        else:
            return fh

    @classmethod
    def _subp_tp_err(cls, tp):
        return type_error(f"{cls}.__call__",
                          Union[None, str, bytes,
                                Iterable[str], Iterable[bytes]],
                          tp)

    def _get_elm_type(self, iter_: Iterable) -> Tuple[Iterable, type]:
        """Guess the element type of a iterable obj,
        also return a not iterated copy."""
        iter_, _iter = tee(iter_)
        try:
            e = next(_iter)
        except StopIteration:
            raise ValueError(f"{repr(self)} input iterable has no element.")
        return iter_, type(e)

    def __repr__(self) -> str:
        return f"subp('{self.cmd}')"
