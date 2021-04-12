"""Progress-bar."""
import sys
from typing import Iterator


def progress_bar(length: int,
                 message: str = '',
                 verbosity: int = 1) -> Iterator[int]:
    """Progress-bar.

    Example::

        pb = progress_bar(10, 'Text:')
        for i in range(10):
            ...
            next(pb)

    Output::

        Text: |--------------------| 100.0%
    """
    if verbosity == 0:
        return iter(range(length))

    if sys.stdout.isatty():
        print(f'{message} |                    |   0.0%', end='', flush=True)
    else:
        print(f'{message} ', end='', flush=True)

    return _progress_bar(length, message)


def _progress_bar(length: int,
                  message: str = '') -> Iterator[int]:
    if not sys.stdout.isatty():
        for n in range(length):
            if n == length - 1:
                print('|--------------------| 100.0%')
            yield n
        return

    for n in range(length):
        p = 100 * (n + 1) / length
        bar = '-' * int(round(20 * (n + 1) / length))
        print(f'\r{message} |{bar:20}| {p:5.1f}%',
              end='',
              flush=True)
        if n == length - 1:
            print()
        yield n


if __name__ == '__main__':
    from time import sleep
    pb = progress_bar(500, 'Test 1:')
    for _ in range(500):
        sleep(0.002)
        next(pb)
    pb = progress_bar(500, 'Test 2:', 0)
    for _ in range(500):
        next(pb)
    pb = progress_bar(5, 'Test 3:')
    for _ in range(5):
        sleep(2.5)
        next(pb)
