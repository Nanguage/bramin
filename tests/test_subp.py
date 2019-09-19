import sys; sys.path.insert(0, '.')
from bramin.subp import subp


def gen_lines(s, t, st=1):
    for i in range(s, t, st):
        yield str(i) + "\n"


class TestSubp(object):

    def test_gen_str(self):
        g = gen_lines(11, 0, -1)
        p = subp("grep 1")
        assert list(p(g)) == ["11\n", "10\n", "1\n"]

    def test_subp_compose(self):
        p1 = subp("grep 1")
        p2 = subp("grep 2")
        p = p1 | p2
        assert p.cmd == "grep 1 | grep 2"
        g = gen_lines(1, 101)
        assert list(p(g)) == ["12\n", "21\n"]

    def test_without_input(self):
        tmp_f = "/tmp/bramin_test.txt"
        with open(tmp_f, 'w') as f:
            f.write('123')
        p = subp(f"cat {tmp_f}")
        assert list(p()) == ['123']

