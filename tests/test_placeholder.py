import sys; sys.path.insert(0, '.')
from bramin import *

import operator


class TestPlaceHolder(object):
    def test_instance_numeric_left_ops(self):
        ph = placeholder()
        ph / 3 * 2 + 1
        assert ph._chain[0].func is operator.truediv
        assert ph._chain[1].func is operator.mul
        assert ph._chain[2].func is operator.add
        assert ph(3) == 3.0
        ph = placeholder()
        ph // 3 * 2 + 1
        assert ph._chain[0].func is operator.floordiv
        assert ph(3) == 3

    def test_instance_numeric_right_ops(self):
        ph = placeholder()
        3 * ph
        assert ph(1) == 3
        ph = placeholder()
        3 / ph
        assert ph(1) == 3.0

    def test_instance_container_ops(self):
        ph = placeholder()
        ph[1]
        assert ph([1,2,3]) == 2
        ph = placeholder()
        ph[1] = 'a'
        l = [1, 2, 3]
        ph(l)
        assert l[1] == 'a'
        #ph = placeholder()
        #import ipdb; ipdb.set_trace()
        #len(ph)
        #assert ph(range(10)) == 10
        ph = placeholder()
        reversed(ph)
        assert list(ph([1, 2, 3])) == [3, 2, 1]
        #ph = placeholder()
        #import ipdb; ipdb.set_trace()
        #1 in ph
        #assert ph([1,2,3]) == True
        #ph = placeholder()
        #g = (i for i in ph)
        #ph([1,2,3])
        #assert list(g) == [1,2,3]

    def test_instance_compare_ops(self):
        ph = placeholder()
        ph > 1
        assert ph(2) is True
        assert ph(1) is False
        ph = placeholder()
        ph < 0
        assert ph(-1) is True
        assert ph(1)  is False
        ph = placeholder()
        ph == 0
        assert ph(0)  is True
        assert ph(-1) is False
        ph = placeholder()
        ph >= 0
        assert ph(0)  is True
        assert ph(-1) is False
        ph = placeholder()
        ph <= 0
        assert ph(0) is True
        assert ph(1) is False

    def test_instance_attr_access_ops(self):
        class A: a = 1
        ph = placeholder()
        #import ipdb; ipdb.set_trace()
        ph.a
        assert ph(A)   == 1
        assert ph(A()) == 1

    def test_multiple_instance(self):
        ph1 = placeholder()
        ph2 = placeholder()
        ph3 = placeholder()
        ph1 + 1 + 2 * ph2 + ph3
        assert ph1(1)(1)(38) == 42

    def test_class_ops(self):
        ph = placeholder + 1
        assert ph._chain[0].func is operator.add
        assert ph(1) == 2
        class A: a = 1
        ph = placeholder.a
        assert ph(A) == 1
        assert ph(A()) == 1

    def test_class_make_multiple_instance(self):
        ph = placeholder + 1 + placeholder * 2
        assert ph(1)(2) == 6
