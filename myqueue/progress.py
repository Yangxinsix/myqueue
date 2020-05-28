"""Progress indicator."""
import sys
from typing import Container, TypeVar, Generator

Thing = TypeVar('Thing')


def show_progress(things: Container[Thing],
                  message: str = '',
                  verbose: bool = True) -> Generator[Thing, None, None]:
    """Wrap container in progress-barr.

    >>> for i in show_progress([1, 2, 3, 4], 'Doing 4 things:'):
    ...     pass
    Doing 4 things: |----------| 100%
    """
    if verbose:
        return ProgressBar(things, message)
    return things


def progress_bar(length: int,
                 message: str = '',
                 verbose: bool = True) -> Generator[Thing, None, None]:
    """Progress-bar.

    >>> pb = progress_bar(2, verbose=False)
    >>> pb.tick()
    >>> pb.tick()
    >>> pb.finish()
    """
    if verbose:
        return ProgressBar(range(length), message)
    return SilentProgressBar()


class SilentProgressBar:
    def tick(self):
        pass

    def finish(self):
        pass


class ProgressBar:
    def __init__(self, things, message=''):
        self.things = things
        self.message = message
        self.iter = None
        if sys.stdout.isatty():
            print(f'{message} |          |   0%', end='', flush=True)
        else:
            print(f'{message} ', end='', flush=True)

    def __iter__(self):
        if sys.stdout.isatty():
            for n, thing in enumerate(self.things):
                yield thing
                p = int(round(100 * (n + 1) / len(self.things)))
                bar = '-' * int(round(10 * (n + 1) / len(self.things)))
                print(f'\r{self.message} |{bar:10}| {p:3}%',
                      end='',
                      flush=True)
            print()
        else:
            yield from self.things
            print('|----------| 100%')

    def tick(self):
        if self.iter is None:
            self.iter = iter(self)
        next(self.iter)

    def finish(self):
        if self.iter is None:
            return
        try:
            next(self.iter)
        except StopIteration:
            pass


if __name__ == '__main__':
    from time import sleep
    for _ in show_progress(range(500), 'Test 1:'):
        sleep(0.002)
    pb = progress_bar(500, 'Test 2:')
    for _ in range(500):
        pb.tick()
    pb.finish()
