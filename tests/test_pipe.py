import sys; sys.path.insert(0, '.')
from bramin import *
from bramin.subp import subp

import pytest

import toolz
from toolz import curry as c
from functools import reduce
import operator
from operator import add


inc = c(map, lambda x: x + 1)


@pytest.fixture
def tmp_f():
    return "/tmp/bramin_test.txt"


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
        pipe = P | _x_ + _x_
        assert pipe(1) == 2
        pipe = P | _x_ + _x_ + _x_ - 1
        assert pipe(1) == 2
        assert pipe(1) == 2

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
        assert df | P | _x_[_x_['a'] > 2].shape[0] | END == 1

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

        b = np.linspace(0, 2*np.pi, 100)
        pipe = P | c(add, _x_, np.sin(_x_))
        assert type(pipe(b)) is np.ndarray
        assert pipe(b).shape == b.shape
        pipe = P | _x_[:10]
        assert (b | P | pipe | END).shape[0] == 10
        pipe = P | (_x_ > np.pi)
        assert sum(pipe(b)) == 50
        pipe = P | _x_[_x_ > np.pi]
        assert pipe(b).min() > np.pi

    def test_write_text(self, tmp_f):
        def gen_lines():
            for i in range(10):
                yield str(i)*i + "\n"
        gen_lines() | P | c(filter, lambda l: len(l.strip()) > 0) > tmp_f | END
        with open(tmp_f) as f:
            lines = f.readlines()
            assert lines == list(gen_lines())[1:]
        (gen_lines() | P | c(filter, lambda l: len(l.strip()) > 0)) >> tmp_f | END
        with open(tmp_f) as f:
            lines = f.readlines()
            assert lines == list(gen_lines())[1:] + list(gen_lines())[1:]

    def test_read_text(self, tmp_f):
        with open(tmp_f, 'w') as f:
            for i in range(10, 0, -1):
                f.write(str(i)+"\n")
        to_int = c(map, lambda l: int(l.strip()))
        grep_odd = c(filter, lambda i: i%2==0)
        ans = tmp_f >> P | to_int | grep_odd | list | END
        assert ans == list(grep_odd(range(10, 0, -1)))

    def test_source_subp(self, tmp_f):
        with open(tmp_f, 'w') as f:
            for i in range(11):
                f.write(str(i)+"\n")
        filter_1 = c(filter, lambda l: "1" in l)
        pipe = P | subp(f"cat {tmp_f}") | filter_1 | list
        assert pipe() == ["1\n", "10\n"]

    def test_mid_subp(self):
        def gen_lines(n):
            for i in range(n):
                yield str(i) + "\n"
        pipe = P | gen_lines | subp("grep 1") | list
        assert pipe(11) == ["1\n", "10\n"]

    def test_compose_subp(self, tmp_f):
        with open(tmp_f, 'w') as f:
            for i in range(111111):
                f.write(str(i)+"\n")
        pipe = P | subp(f"cat {tmp_f}") | subp("grep 1") | list
        assert pipe._chain[0].cmd == f"cat {tmp_f} | grep 1"
        assert pipe()[:2] == ["1\n", "10\n"]
