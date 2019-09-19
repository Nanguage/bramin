import sys; sys.path.insert(0, '.')
from bramin._utils import *

import pytest

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
        for tp in names: sms[tp]

    def test_iter(self):
        sms = SpecialMethods(types=['basic/initial', 'basic/compare'])
        for name, tp in sms:
            assert name in sms[tp]
            assert '__' not in name
        sms = SpecialMethods()
        for name, tp in sms: assert name in sms[tp]
        sms = SpecialMethods(with_underline=True)
        for name, tp in sms:
            assert name.strip('__') in sms[tp]
            assert '__' in name

    def test_filter(self):
        f = lambda name, tp: True if name != 'init' else False
        tp = 'basic/compare'
        sms = SpecialMethods(types=[tp], filter_func=f)
        assert 'new', tp in list(sms)
        assert 'init', tp not in list(sms)
