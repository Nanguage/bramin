import sys; sys.path.insert(0, '.')
from bramin.io import *

import pytest

import io
import gzip


tmp_text = "/tmp/bramin_test.txt"
tmp_gz_text = "/tmp/bramin_test.txt.gz"

@pytest.fixture
def lines():
    return ["1\n", "2\n"]


def test_unregistered():
    callable_file.unregister('text')
    with pytest.raises(IOError):
        f = callable_file(tmp_text, 'w')
    callable_file.register(text_file)


def test_read_text():
    with open(tmp_text, 'w') as f:
        f.write("1\n2\n")
    f = callable_file(tmp_text, mode='r')
    lines = f()
    assert list(lines) == ["1\n", "2\n"]


def test_write_text(lines):
    f = callable_file(tmp_text, mode='w')
    f(lines)
    with open(tmp_text) as f:
        assert f.readlines() == lines


def test_read_gz_text():
    with io.TextIOWrapper(gzip.open(tmp_gz_text, 'w')) as f:
        f.write("1\n2\n")
    callable_file.register(gzipped_text)
    f = callable_file(tmp_gz_text)
    lines = f()
    assert list(lines) == ["1\n", "2\n"]
    callable_file.unregister('gzipped_text')


def test_write_gz_text(lines):
    callable_file.register(gzipped_text)
    f = callable_file(tmp_gz_text, 'w')
    f(lines)
    with io.TextIOWrapper(gzip.open(tmp_gz_text)) as f:
        assert lines == f.readlines()
    callable_file.unregister('gzipped_text')
