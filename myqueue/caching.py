"""Simple caching function implementation using JSON."""
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Sequence, TypeVar
from functools import lru_cache, wraps


T = TypeVar('T')


class CacheFileNotFoundError(FileNotFoundError):
    """JSON cache file not found."""


def json_cached_function(function: Callable[..., T],
                         name: str,
                         args: Sequence[Any],
                         kwargs: dict[str, Any]) -> Callable[..., T]:
    """Add file-caching to function.

    The decorated function will write its result in JSON format to a
    file called <name>.result.
    """
    path = Path(f'{name}.result')

    @wraps(function)
    def new_func(only_read_from_cache: bool = False) -> T:
        """A caching function.

        If *only_read_from_cache* is True then an CacheFileNotFoundError
        exception will be raised if the file does not exist.
        """
        if path.is_file():
            return decode(path.read_text(encoding='utf-8'))
        if only_read_from_cache:
            raise CacheFileNotFoundError
        result = function(*args, **kwargs)
        if mpi_world().rank == 0:
            path.write_text(encode(result), encoding='utf-8')
        return result

    return new_func


class MPIWorld:
    """A no-MPI implementation."""
    rank: int = 0


@lru_cache()
def mpi_world() -> MPIWorld:
    """Find and return a world object with a rank attribute."""
    import sys
    mod = sys.modules.get('mpi4py')
    if mod:
        return mod.MPI.COMM_WORLD  # type: ignore
    mod = sys.modules.get('_gpaw')
    if hasattr(mod, 'Communicator'):
        return mod.Communicator()  # type: ignore
    mod = sys.modules.get('_asap')
    if hasattr(mod, 'Communicator'):
        return mod.Communicator()  # type: ignore
    return MPIWorld()


class Encoder(json.JSONEncoder):
    """Encode complex, datetime, Path and ndarray objects.

    >>> import numpy as np
    >>> Encoder().encode(1+2j)
    '{"__complex__": [1.0, 2.0]}'
    >>> Encoder().encode(datetime(1969, 11, 11, 0, 0))
    '{"__datetime__": "1969-11-11T00:00:00"}'
    >>> Encoder().encode(Path('abc/123.xyz'))
    '{"__path__": "abc/123.xyz"}'
    >>> Encoder().encode(np.array([1., 2.]))
    '{"__ndarray__": [1.0, 2.0]}'
    """
    def default(self, obj: Any) -> Any:
        if isinstance(obj, complex):
            return {'__complex__': [obj.real, obj.imag]}

        if isinstance(obj, datetime):
            return {'__datetime__': obj.isoformat()}

        if isinstance(obj, Path):
            return {'__path__': str(obj)}

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


def object_hook(dct: dict[str, Any]) -> Any:
    """Decode complex, datetime, Path and ndarray representations.

    >>> object_hook({'__complex__': [1.0, 2.0]})
    (1+2j)
    >>> object_hook({'__datetime__': '1969-11-11T00:00:00'})
    datetime.datetime(1969, 11, 11, 0, 0)
    >>> object_hook({'__path__': 'abc/123.xyz'})
    PosixPath('abc/123.xyz')
    >>> object_hook({'__ndarray__': [1.0, 2.0]})
    array([1., 2.])
    """
    data = dct.get('__complex__')
    if data is not None:
        return complex(*data)

    data = dct.get('__datetime__')
    if data is not None:
        return datetime.fromisoformat(data)

    data = dct.get('__path__')
    if data is not None:
        return Path(data)

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
