import pytest
import numpy as np
from myqueue.caching import encode, decode

objects = [
    np.zeros((0, 3), complex),
    1 + 2j,
    np.ones((2, 2), int)]


@pytest.mark.parametrize('obj1', objects)
def test_encoding(obj1):
    text1 = encode(obj1)
    obj2 = decode(text1)
    text2 = encode(obj2)
    assert text1 == text2
    if isinstance(obj1, np.ndarray):
        assert (obj1 == obj2).all()
        assert obj1.shape == obj2.shape
        assert obj1.dtype == obj2.dtype
    else:
        assert obj1 == obj2
