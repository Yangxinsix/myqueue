import sys


def show_progress(things, message, verbose):
    if verbose:
        return Progress(things, message)
    return things


class Progress:
    def __init__(self, things, message=''):
        self.things = things
        self.message = message
        if sys.stdout.isatty():
            print(f'{message}   0%', end='', flush=True)
        else:
            print(f'{message} ', end='', flush=True)

    def __iter__(self):
        if sys.stdout.isatty():
            for n, thing in enumerate(self.things):
                yield thing
                p = int(round(100 * (n + 1) / len(self.things)))
                print(f'\r{self.message} {p:3}%', end='', flush=True)
            print()
        else:
            yield from self.things
            print('100%')


if __name__ == '__main__':
    from time import sleep
    for _ in show_progress(range(500), '...:'):
        sleep(0.002)
