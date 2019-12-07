import sys
sys.path.insert(0, '.')
import typing as t

import pytest

from bramin._utils import *


@pytest.fixture
def sms():
    return SpecialMethods()


class TestSpecialMethods(object):
    def test_get_item(self, sms):
        assert sms['basic/initial'] == ['new', 'init']
        assert 'radd' in sms['numeric/right']

    def test_inner_grp_names(self, sms):
        sms = SpecialMethods()
        names = list(sms._inner_grp_names())
        for tp in names:
            sms[tp]

    def test_iter(self):
        sms = SpecialMethods(types=['basic/initial', 'basic/compare'])
        for name, tp in sms:
            assert name in sms[tp]
            assert '__' not in name
        sms = SpecialMethods()
        for name, tp in sms:
            assert name in sms[tp]
        sms = SpecialMethods(with_underline=True)
        for name, tp in sms:
            assert name.strip('__') in sms[tp]
            assert '__' in name

    def test_filter(self):
        def f(name, tp): return True if name != 'init' else False
        tp = 'basic/compare'
        sms = SpecialMethods(types=[tp], filter_func=f)
        assert 'new', tp in list(sms)
        assert 'init', tp not in list(sms)


class TestTypeGuard(object):

    def test_func(self):
        @type_guard
        def f1(a: int) -> int:
            return a
        assert type(f1(1)) == int
        with pytest.raises(TypeError):
            f1("a")

    def test_func_ret(self):
        @type_guard(check_ret=False)
        def f1(a: int) -> int:
            return "1"
        assert type(f1(1)) == str

    def test_mth(self):
        class A(object):
            @type_guard
            def mth1(self, a: int) -> int:
                return a

            @type_guard
            def mth2(self, a: "A"):
                return a

            @type_guard
            def mth3(self, a: "A") -> "B":
                return a

        a = A()
        assert isinstance(a.mth1(1), int)
        assert isinstance(a.mth2(a), A)
        with pytest.raises(TypeError):
            a.mth2(1)
        with pytest.raises(TypeError):
            a.mth3(1)

    def test_Any(self):
        @type_guard
        def f1(a: Any) -> Any:
            return a
        assert f1(1) == 1
        assert f1("aaaa") == "aaaa"
        assert f1(f1) == f1

    def test_Union(self):
        @type_guard
        def f1(a: t.Union[int, str]):
            return a
        assert f1(1) == 1
        assert f1("1") == "1"
        with pytest.raises(TypeError):
            f1(b"1")

    def test_Callable(self):
        @type_guard
        def f1(a: t.Callable):
            return a
        assert f1(f1) == f1
        with pytest.raises(TypeError):
            f1(1)
