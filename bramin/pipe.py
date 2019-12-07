from typing import (
    Any, Optional, Union, Callable, List, Tuple, NewType
)
import types
from copy import copy
from functools import partial
import operator

from ._utils import (
    SpecialMethods,
    is_partial_like, replace_partial_args, format_partial,
    Singleton, type_error, type_guard
)
from .io import callable_file
from .subp import subp


class EndMarker(metaclass=Singleton):
    def __init__(self, attach=None):
        self.attach = attach

    def __ror__(self, left: str):
        """Dealing with the problem caused by '|' operator's priority,
        when redirect the stream to a file, like:

        P | func1 | func2 > "target.txt" | END
        """
        if not isinstance(left, str):
            return NotImplemented
        self.attach = left
        return self


END = EndMarker()


FuncList = List[Callable]


class CallChain(object):
    """Represent a series of nested invoked functions(callable objs).

    >>> def add1(a):
    ...     return a + 1
    >>> add3 = CallChain([add1, add1, add1])
    >>> add3(39)  # equivalent to add1(add1(add1(39)))
    42
    """

    def __init__(self, invoke_chain: Optional[FuncList] = None,
                 _input: Any = None):
        self._chain = invoke_chain if invoke_chain is not None else []
        self._input = _input

    def __call__(self, _input=None):
        if len(self._chain) <= 0:
            raise ValueError(
                "There are at least one callable in invoke_chain.")
        self._input = _input
        res = self._input
        for func in self._chain:
            res = self._process(func, res)
        return res

    def _process(self, func: Callable, old: Any) -> Any:
        return func(old)

    @type_guard
    def _append(self, func: Callable):
        self._chain.append(func)


class MetaPipe(type):
    """Control the behavior of pass object into pipe directly:
    obj | P | ... | END
    """

    def __or__(self, right):
        p = self()
        return p | right

    def __ror__(self, left):
        return self(_input=left)

    def __rrshift__(self, left):
        p = self()
        return p | callable_file(left)

    def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
        import numpy as np
        if ufunc is np.bitwise_or:
            return self(_input=inputs[0])
        else:
            return NotImplemented


class Pipe(CallChain, metaclass=MetaPipe):

    @property
    def last(self) -> Optional[Callable]:
        if self._chain:
            return self._chain[-1]
        else:
            return None

    def __or__(self, right: Union[Callable, EndMarker]):
        if right is placeholder:
            ph = placeholder([lambda x:x])  # add an identity func
            chain_ = self._chain + [ph]
            p = type(self)(chain_, self._input)
            return p
        elif isinstance(right, subp) and isinstance(self.last, subp):
            # concat two subp obj
            chain_ = self._chain[:-1]
            chain_.append(self.last | right)
            p = type(self)(chain_, self._input)
            return p
        elif isinstance(right, Pipe):  # concat two Pipe obj
            chain_ = self._chain+right._chain
            p = type(self)(chain_, self._input)
            return p
        elif callable(right):
            chain_ = self._chain + [right]
            p = type(self)(chain_, self._input)
            return p
        elif right is END:
            return self.__call__(self._input)
        else:
            raise type_error(f"{type(self)}.__or__",
                             Union[EndMarker, callable], type(right))

    @type_guard
    def __rshift__(self, right: str) -> "Pipe":
        chain_ = self._chain + [callable_file(right, 'a')]
        p = type(self)(chain_, self._input)
        return p

    @type_guard
    def __gt__(self, right: Union[str, EndMarker]):
        if right is END:  # case:   ... | func > "filename" | END
            a = END.attach
            if a is None:
                raise type_error(f"{type(self)}.__gt__", str, EndMarker)
            elif not isinstance(a, str):
                raise type_error(f"{type(self)}.__gt__", str, type(a))
            p = type(self)(self._chain + [callable_file(a, 'w')], self._input)
            return p(p._input)
        else:
            p = type(self)(self._chain +
                           [callable_file(right, 'w')], self._input)
            return p

    def _process(self, func: Callable, old: Any) -> Any:
        if isinstance(func, placeholder):
            # placeholder object
            new = placeholder._eval(func, old)
        elif is_partial_like(func) and \
            (placeholder in set(func.args) or
             placeholder in set(func.keywords)):
            # placeholder in the partial-like parameters
            # because MetaPlaceHolder reloaded __eq__, shold convert args to set
            # replace placeholder to real pass-in
            func = replace_partial_args(func, placeholder, old)
            func = replace_partial_args(func, placeholder, old,
                                        match_func=lambda i, v, t: isinstance(
                                            v, t),
                                        replace_func=lambda v, r: v(r))
            new = func()
        else:
            new = func(old)
        return new

    def __repr__(self) -> str:
        def _repr(o):
            if isinstance(o, placeholder):
                return repr(o)
            elif is_partial_like(o):
                return format_partial(o)
            elif hasattr(o, '__qualname__'):
                return o.__qualname__
            else:
                return repr(o)
        chain_str = " -> ".join([_repr(f) for f in self._chain])
        return f"[P: {chain_str} ]"

    def __str__(self) -> str:
        return repr(self)


class MetaPlaceHolder(type):
    def __init__(ph, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # add mimic special method to placeholder obj

        def make_mths(ph, op, tp, impl):
            def _mimic(self, *args, **kwargs):
                f = partial(impl, ph, *args, **kwargs)
                self._append(f)
                return self
            return _mimic
        _assign_special_methods(ph, make_mths)

    def __repr__(self) -> str:
        return '_x_'

    def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
        """Support numpy ndarray
        see:
        https://docs.scipy.org/doc/numpy-1.13.0/neps/ufunc-overrides.html"""
        ph = self()
        f = partial(ufunc, *inputs, **kwargs)
        ph._append(f)
        return ph


def _assign_special_methods(obj, make_mimic):
    def filter_(name, tp):
        black_list = ['or', 'ror', 'getattribute', 'setattr', 'delattr']
        if name in black_list:
            return False
        return True

    for _op, _tp, _impl in SpecialMethods(
        ['numeric/left', 'numeric/right', 'container',
         'basic/compare', 'attribute_access/attr'],
        filter_,
        with_impl=True
    ):
        setattr(obj, f"__{_op}__", make_mimic(obj, _op, _tp, _impl))


def _make_meta_mths(obj, op, tp, impl):
    def _mimic(self, *args, **kwargs):
        ph = self()
        f = partial(impl, self, *args, **kwargs)
        ph._append(f)
        return ph
    return _mimic


_assign_special_methods(MetaPlaceHolder, _make_meta_mths)


class placeholder(CallChain, metaclass=MetaPlaceHolder):

    def __index__(self):
        return id(self)

    def __repr__(self) -> str:
        return f'<ph at {hex(id(self))}>'

    def _process(self, func: Callable, old: Any) -> Any:
        if is_partial_like(func):
            # replace placeholder to real pass-in
            func = replace_partial_args(func, placeholder, old,
                                        match_func=lambda i, v, t: (i == 0) and v is t)
            func = replace_partial_args(func, placeholder, self._input,
                                        match_func=lambda i, v, t: (i > 0) and v is t)
            if func.func is operator.getitem:
                def _replace(v, r):
                    return v(r) if len(v._chain) > 0 else old
                func = replace_partial_args(
                    func, placeholder, old,
                    match_func=lambda i, v, t: isinstance(v, t),
                    replace_func=_replace
                )
            new = func()
        else:
            new = func(old)
        return new

    @classmethod
    def _eval(cls, ph, _input):
        if isinstance(ph, placeholder):
            return cls._eval(ph(_input), _input)
        else:
            return ph

    def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
        f = partial(ufunc, *inputs, **kwargs)
        self._append(f)
        return self
