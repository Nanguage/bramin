from typing import Optional, Iterable, Callable, Any
from itertools import chain, repeat
import operator
import builtins

class SpecialMethods(object):
    # see https://docs.python.org/3/reference/datamodel.html#special-method-names
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
