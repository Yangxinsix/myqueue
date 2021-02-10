"""Simple caching function implementation using JSON."""
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict


class Cached:
    """A caching function."""
    def __init__(self, function: Callable, name: str):
        self.function = function
        self.path = Path(f'{name}.done')

    def has(self, *args, **kwargs) -> bool:
        """Check if function has been called."""
        return self.path.is_file()

    def __call__(self):
        """Call function (if needed)."""
        if self.has():
            return decode(self.path.read_text())
        result = self.function()
        self.path.write_text(encode(result))
        return result


def cached_function(function: Callable, name: str) -> Cached:
    """Wrap function if needed."""
    if hasattr(function, 'has'):
        return function  # type: ignore
    return Cached(function, name)


class Encoder(json.JSONEncoder):
    """Encode complex, datetime and ndarray objects.

    >>> import numpy as np
    >>> Encoder().encode(1+2j)
    '{"__complex__": [1.0, 2.0]}'
    >>> Encoder().encode(datetime(1969, 11, 11, 0, 0))
    '{"__datetime__": "1969-11-11T00:00:00"}'
    >>> Encoder().encode(np.array([1., 2.]))
    '{"__ndarray__": [1.0, 2.0]}'
    """
    def default(self, obj):
        if isinstance(obj, complex):
            return {'__complex__': [obj.real, obj.imag]}

        if isinstance(obj, datetime):
            return {'__datetime__': obj.isoformat()}

        if hasattr(obj, '__array__'):
            if obj.dtype == complex:
                dct = {'__ndarray__': obj.view(float).tolist(),
                       'dtype': 'complex'}
            else:
                dct = {'__ndarray__': obj.tolist()}
                if obj.dtype not in [int, float]:
                    dct['dtype'] = obj.dtype.name
            if obj.size == 0:
                dct['shape'] = obj.shape
            return dct

        return json.JSONEncoder.default(self, obj)


encode = Encoder().encode


def object_hook(dct: Dict[str, Any]) -> Any:
    """Convert ...

    >>> object_hook({'__complex__': [1.0, 2.0]})
    (1+2j)
    >>> object_hook({'__datetime__': '1969-11-11T00:00:00'})
    datetime.datetime(1969, 11, 11, 0, 0)
    >>> object_hook({'__ndarray__': [1.0, 2.0]})
    array([1., 2.])
    """
    data = dct.get('__complex__')
    if data is not None:
        return complex(*data)

    data = dct.get('__datetime__')
    if data is not None:
        return datetime.fromisoformat(data)

    data = dct.get('__ndarray__')
    if data is not None:
        import numpy as np
        dtype = dct.get('dtype')
        if dtype == 'complex':
            array = np.array(data, dtype=float).view(complex)
        else:
            array = np.array(data, dtype=dtype)
        shape = dct.get('shape')
        if shape is not None:
            array.shape = shape
        return array

    return dct


def decode(text: str) -> Any:
    """Convert JSON to object(s)."""
    return json.loads(text, object_hook=object_hook)
