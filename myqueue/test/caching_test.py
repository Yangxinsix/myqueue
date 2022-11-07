from __future__ import annotations

import os
from datetime import datetime
from math import inf
from pathlib import Path

import numpy as np
import pytest

from myqueue.caching import (CacheFileNotFoundError, decode, encode,
                             json_cached_function)

objects = [
    [27, 1.4, {'a': 7, 'b': [1, 2]}, inf, -inf],
    1 + 2j,
    None,
    datetime.now(),
    np.zeros((0, 3), complex),
    np.zeros((3, 0), complex),
    np.zeros((2, 1), complex),
    np.zeros(2, np.float32),
    np.ones((2, 2), int)]


@pytest.mark.parametrize('obj1', objects)
def test_encoding(obj1):
    """Test encoding/decoding."""
    text1 = encode(obj1)
    obj2 = decode(text1)
    text2 = encode(obj2)
    assert text1 == text2
    print(text1)
    if isinstance(obj1, np.ndarray):
        assert (obj1 == obj2).all()
        assert obj1.shape == obj2.shape
        assert obj1.dtype == obj2.dtype
    else:
        assert obj1 == obj2


def func(a: int, b: int) -> int:
    """Test function."""
    return a + b


def test_no_cache(tmp_path):
    """Test function that returns non-jsonable object."""
    os.chdir(tmp_path)
    function = json_cached_function(func, 'add', [1], {'b': 2})
    with pytest.raises(CacheFileNotFoundError):
        function(only_read_from_cache=True)

    assert function() == 3

    assert Path('add.result').read_text() == '3'
    Path('add.result').write_text('4')
    assert function() == 4
