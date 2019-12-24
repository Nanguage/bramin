import sys
sys.path.insert(0, '.')

from bramin.curry import curry


class TestCurry(object):

    def test_simple(self):
        def f(x, y, z):
            return (x, y, z)
        f_ = curry(f)
        assert f_(1)(2)(3) == (1, 2, 3)
        assert f_(x=1)(2)(3) == (1, 2, 3)
        assert f_(x=1, y=2)(3) == (1, 2, 3)
        assert f_(x=1, z=3)(2) == (1, 2, 3)

    def test_with_default(self):
        def f(x, y, z=1):
            return x, y, z
        f_ = curry(f)
        assert f_(1)(2, 3) == (1, 2, 3)

    def test_var_len_pos(self):
        def add(a, b, *args):
            return sum([a, b] + list(args))
        add_ = curry(add)
        assert add_(1, 2) == add_(a=1)(2) == add_(b=2)(1) == 3
        assert add_(1, 2, 3) == add_(1)(2, 3) == 6
        assert add_(1, 2, 3, 4) == 10

    def test_var_len_kw(self):
        def add(a, b, **kwargs):
            return sum([a, b] + list(kwargs.values()))
        add_ = curry(add)
        assert add_(1, 2) == 3
        assert add_(c=3)(1, 2) == 6 == add_(1, 2, c=3)
        assert add_(1, 2, c=3, d=4) == 10
