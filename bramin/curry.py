from typing import Callable
from functools import partial, update_wrapper
from inspect import _empty, signature
from copy import copy
from collections import OrderedDict as od

from ._utils import (
    type_error, is_partial_like
)


class curry(object):

    def __init__(self, func:Callable, *args, **kwargs):
        if not callable(func):
            raise type_error(f"{type(self)}.__init__", callable, type(func))

        is_p = is_partial_like(func)
        ori_func = func.func if is_p else func

        self.func = ori_func
        sig = signature(ori_func)
        self._params = list(sig.parameters.items())
        self._bindings = od([(n, p.default) for n, p in sig.parameters.items()])

        if is_p and hasattr(func, '_bindings'):
            self._bindings.update(func._bindings)
        elif is_p:
            self._bind(func.args, func.keywords)
        self._bind(*args, **kwargs)

        update_wrapper(self, ori_func)
        self._is_all_bound = False

    def _bind(self, *args, **kwargs):
        self._update_binding(self._bindings, args, kwargs)

    def _update_binding(self, bindings, args, kwargs):
        bids = bindings
        pars = self._params
        for val in args:
            for name, p in pars:
                if p.default is not _empty: break
                if bids[name] is _empty:
                    bids[name] = val
                    break
        for name, val in kwargs.items():
            bids[name] = val

    @property
    def all_bound(self) -> bool:
        if self._is_all_bound:
            return True
        else:
            res = all([p is not _empty for _, p in self._bindings.items()])
            self._is_all_bound = res
            return res

    @property
    def args(self) -> tuple:
        args_ = []
        for name, p in self._params:
            if p.default is not _empty: break
            if self._bindings[name] is _empty: break
            args_.append(self._bindings[name])
        return tuple(args_)

    @property
    def keywords(self) -> dict:
        kwargs = {}
        for name, p in self._params:
            if p.default is _empty: continue
            kwargs[name] = self._bindings[name]
        return kwargs

    def __call__(self, *args, **kwargs):
        try:
            return self.func(*self.args, **self.keywords)
        except TypeError as e:
            if self.all_bound: raise
            new = type(self)(self, *args, **kwargs)
            if new.all_bound:
                return new(*new.args, **new.keywords)
            else:
                return new

    def __repr__(self):
        bound = {
            n: v for n, v in self._bindings.items()
            if v is not _empty }
        b = ", ".join([f"{n}={repr(v)}" for n, v in bound.items()])
        s = f"<curry {self.__name__}{' ' + b if b else ''}>"
        return s
