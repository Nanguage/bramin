import pytest

import toolz
from toolz import curry as c
from functools import reduce
import operator
from operator import add

import sys; sys.path.insert(0, '.')
from bramin import Pipe as P
from bramin import placeholder as _x_
from bramin import END

inc = c(map, lambda x: x + 1)


class TestPipe(object):
    def test_simple_pipe(self):
        ans = range(10) | P | inc | list | END
        assert ans == list(range(1, 11))

    def test_pipe_as_func(self):
        pipe = P | inc | list
        ans = pipe(range(10))
        assert ans == list(range(1, 11))

    def test_concat_pipe(self):
        p1 = P | inc | inc
        p2 = P | list 
        pipe = p1 | p2
        ans = pipe(range(10))
        assert ans == list(range(2, 12))

    def test_placeholder_in_func(self):
        pipe = P | c(map, lambda x:x+1, _x_) | list
        ans = pipe(range(10))
        assert ans == list(range(1, 11))
        ans = range(5) | P | c(toolz.accumulate, add, _x_) | list | END
        assert ans == [0, 1, 3, 6, 10]

    def test_placeholder_in_pipe(self):
        id_f = P | _x_
        assert id_f([1,2,3]) == [1,2,3]
        assert 1 | P | _x_ + 1 | _x_ // 2 | END == 1 
        #g = range(10) | P | (i for i in _x_) | END 
        #assert list(g) == list(range(10))

    def test_with_pandas(self):
        import pandas as pd
        df = pd.DataFrame([[1,2,3],
                           [2,3,4],
                           [4,3,1]], columns=['a','b','c'])
        pipe = P | _x_[_x_['a'] > 2].shape[0] 
        assert pipe(df) == 1
        assert df | P | pipe | END == 1

    def test_with_numpy(self):
        import numpy as np
        a = np.arange(10)
        pipe = P | np.sum
        assert pipe(a) == 45
        pipe = P | np.sin | _x_.shape[0]
        assert pipe(a) == 10
        pipe = P | np.sin(_x_) | _x_.shape[0]
        assert pipe(a) == 10
        assert a | P | pipe | END == 10
