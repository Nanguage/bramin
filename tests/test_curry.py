import sys; sys.path.insert(0, '.')
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
