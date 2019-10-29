from typing import Optional, Iterable, Callable, Any
import typing as t
from itertools import chain, repeat
import operator
import builtins
from functools import wraps, partial
import inspect
import types

import typing_inspect as ti


class SpecialMethods(object):
    """Traversal object's special methods.
    see: https://docs.python.org/3/reference/datamodel.html#special-method-names
    """
    groups = {
        'basic': {
            'initial': ['new', 'init'],
            'format':  ['repr', 'str', 'bytes', 'format'],
            'compare': ['lt', 'le', 'eq', 'ne', 'gt', 'ge'],
            'other':   ['del', 'hash', 'bool'],
        },

        'attribute_access': {
            'attr':       ['getattr', 'getattribute', 'setattr', 'delattr'],
            'descriptor': ['get', 'set', 'delete', 'set_name'],
            'other':      ['slots'],
        },

        'class_creation': [ 'init_subclass', 'mro_entries', 'prepare' ],
        'check': [ 'instancecheck', 'subclasscheck' ],

        'generic_types': [ 'class_getitem' ],
        'callable': [ 'call' ],

        'container': [ 'len', 'length_hint',
                       'getitem', 'setitem', 'delitem', 'missing',
                       'iter', 'reversed', 'contains' ],

        'numeric': {

            'left': [ 'add', 'sub', 'mul', 'matmul',
                      'truediv', 'floordiv', 'mod', 'divmod',
                      'pow', 'lshifh', 'rshift',
                      'and', 'xor', 'or' ],
            
            'other': [ 'neg', 'pos', 'abs', 'invert', 'index',
                       'round', 'trunc', 'floor', 'ceil', ],

        },

        'context': ['enter', 'exit'],
        'coroutines': ['await', 'aiter', 'anext'],

    }

    groups['numeric']['right']  = [ 'r'+op for op in groups['numeric']['left'] ]
    groups['numeric']['assign'] = [ 'i'+op for op in groups['numeric']['left'] ]

    def __init__(self, types:Optional[Iterable[str]]=None,
                       filter_func:Optional[Callable[[str, str], bool]]=None,
                       with_underline:bool=False,
                       with_impl:bool=False,
                       grp_sep:str='/'):
        self.types = types if types else self._inner_grp_names()
        self.filter_func = filter_func
        self.with_underline = with_underline
        self.with_impl = with_impl
        self.grp_sep = grp_sep

    def _inner_grp_names(self, grp=None, prefix='') -> Iterable[str]:
        grp = self.groups if grp is None else grp
        sep = self.grp_sep
        for k, v in grp.items():
            if isinstance(v, list):
                yield prefix+sep+k
            else:
                yield from self._inner_grp_names(v, prefix+sep+k)

    def __getitem__(self, key:str, grp=None) -> Iterable[str]:
        grp = self.groups if grp is None else grp
        sep = self.grp_sep
        key = key.lstrip(sep)
        if sep in key:
            first, *other = key.split(self.grp_sep)
            return self.__getitem__(sep.join(other), grp[first])
        else:
            names = grp[key]
            if not isinstance(names, list):
                raise KeyError(f'{key} is not a valid group name.')
            return names

    def _get_impl(self, name:str) -> Optional[Callable]:
        """Get the corresponding function with same semantic to the special method"""
        if name in dir(operator):
            impl = getattr(operator, name)
        elif name in dir(builtins):
            impl = getattr(builtins, name)
        elif name in self['numeric/right']:
            impl = reverse_args(self._get_impl(name.lstrip('r')))
        else:
            impl = None
        return impl

    def __iter__(self):
        names_and_tps = chain(*[zip(self[tp], repeat(tp)) for tp in self.types])
        f_ = None if (self.filter_func is None) else (lambda t: self.filter_func(*t))
        names_and_tps = filter(f_, names_and_tps)
        for name, tp in names_and_tps:
            name = f"__{name}__" if self.with_underline else name
            if self.with_impl:
                impl = self._get_impl(name)
                yield name, tp, impl
            else:
                yield name, tp


def reverse_args(func:Callable) -> Callable:
    """reverse func's args"""
    def wrapper(*args):
        return func(*args[::-1])
    wrapper.func = func
    return wrapper


def is_partial_like(func:Callable):
    """toolz.curry or functools.partial-like object?"""
    return (
        hasattr(func, 'func')
        and hasattr(func, 'args')
        and hasattr(func, 'keywords')
        and isinstance(func.args, tuple)
    )


def replace_partial_args(
        func:Callable, target:Any, repl:Any,
        match_func:Optional[Callable]=None,
        replace_func:Optional[Callable]=None,
    ) -> Callable:
    """Replace partial-like object's argument,
    return a new callable"""
    if match_func is None:
        match_func = lambda i, v, t: v is t
    if replace_func is None:
        replace_func = lambda v, r: r
    args   = [  (replace_func(v, repl) if match_func(i, v, target) else v) for i, v in enumerate(func.args)]
    kwargs = {k:(replace_func(v, repl) if match_func(k, v, target) else v) for k, v in func.keywords.items()}
    new_func = type(func)(func.func, *args, **kwargs)
    return new_func


def format_partial(func:Callable, verbose:bool=False) -> str:
    """Format a partial-like object"""
    fname = func.__qualname__ if hasattr(func, '__qualname__') else str(func)
    arg_str = ", ".join([repr(a) for a in func.args])
    kwargs_str = ", ".join([str(k)+":"+repr(v) for k,v in func.keywords.items()])
    if verbose:
        repr_ = f"<partial {fname}:{arg_str} {kwargs_str}>"
    else:
        repr_ = f"<partial {fname}>"
    return repr_


class Singleton(type):
    """Let class has only one instance."""
    def __init__(self, *args, **kwargs):
        self._instance = None
        super().__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        if self._instance is None:
            self._instance = super().__call__(*args, **kwargs)
            return self._instance
        else:
            return self._instance


def type_error(func_name, expect_tp, got_tp,
               arg_name=None, ret=False) -> TypeError:
    """format type error message."""
    msg = func_name
    if ret:
        msg += f"'s return"
    elif arg_name:
        msg += f"'s parameter '{arg_name}'"
    msg += f" expect type {expect_tp}, got {got_tp}."
    return TypeError(msg)


class type_guard(object):
    """Decorator for check func's input and output type,
    when it's invoked.
    Expected type is specified by it's annotation.
    
    Support a part of typing types:
        Any, Optional, Union, Callable
        (note: not support nested typing types now. like: Optional[Callable])
    """

    def __new__(cls, func=None, **kwargs):
        if func is None:
            return partial(cls, **kwargs)
        else:
            return super().__new__(cls)

    def __init__(self, func=None, *, check_ret=True):
        wraps(func)(self)
        self.func = func
        self.check_ret = check_ret
        self.sig = inspect.signature(func)
        self._func_name = get_callable_name(func)
        self._input_checkers = {}
        self._output_checker = None
        self._dispatch_checkers()

    def __call__(self, *args, **kwargs):
        self._check_input_args(*args, **kwargs)
        res = self.func(*args, **kwargs)
        self._check_output(res)
        return res

    def _check_input_args(self, *args, **kwargs):
        bound_values = self.sig.bind(*args, **kwargs)
        for name, value in bound_values.arguments.items():
            if name not in self._input_checkers: continue
            checker = self._input_checkers[name]
            expect_tp = self.sig.parameters[name].annotation
            checker(value)
            if not checker(value):
                raise type_error(self._func_name, expect_tp, type(value), name)

    def _check_output(self, res):
        expect_tp = self.sig.return_annotation
        if self.check_ret and self._output_checker:
            if not self._output_checker(res):
                raise type_error(self._func_name, expect_tp, type(res), ret=True)

    def _dispatch_checkers(self):
        sig = self.sig
        for name, p in sig.parameters.items():
            expect_tp = p.annotation
            if expect_tp is inspect._empty: continue
            self._input_checkers[name] = self._get_checker(expect_tp)
        if sig.return_annotation is not inspect._empty:
            self._output_checker = self._get_checker(sig.return_annotation)

    def _get_checker(self, expect_tp):
        if expect_tp is t.Any:
            return lambda v: True
        # about type determination of typing objs
        # see: https://github.com/python/typing/issues/528
        elif ti.is_union_type(expect_tp):
            return lambda v: isinstance(v, expect_tp.__args__)
        elif ti.is_callable_type(expect_tp):
            return lambda v: callable(v)
        elif isinstance(expect_tp, str):
            return self._get_str_checker(expect_tp)
        else:
            return lambda v: isinstance(v, expect_tp)

    @classmethod
    def _get_str_checker(cls, expect_tp):
        """
        annotation with string, it's the
        case of annotation in the class with it self. like:
          class A:
              def mth1(self, other:"A"): ...
        """
        def checker(v):
            caller_f = inspect.currentframe().f_back.f_back
            args = caller_f.f_locals['args']
            if (not args) or (expect_tp != type(args[0]).__name__):
                raise TypeError("string annotation can only be used "
                                "for annotate class it self.")
            tp = type(args[0])
            return isinstance(v, tp)
        return checker

    def __get__(self, instance, cls):
        if instance is None:
            return self
        else:
            return types.MethodType(self, instance)


def get_callable_name(func:Callable) -> str:
    if hasattr(func, '__qualname__'):
        name = func.__qualname__
    elif hasattr(func, '__name__'):
        name = func.__name__
    else:
        name = get_callable_name(type(func).__call__)
    return name

