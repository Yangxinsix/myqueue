"""Progress-bar."""
from __future__ import annotations
import os
import sys


class Spinner:
    def __init__(self) -> None:
        """Print the characters .oOo.oOo.oOo.oOo and so on."""
        if sys.stdout.isatty():
            self.fd = sys.stdout
        else:
            self.fd = open(os.devnull, 'w')
        self.n = 0

    def spin(self) -> None:
        """Spin the spinner."""
        N = 500
        if self.n % N == 0:
            self.fd.write('\r' + '.oOo'[(self.n // N) % 4])
            self.fd.flush()
        self.n += 1

    def reset(self) -> None:
        """Place cursor at the beginning of the line."""
        self.n = 0
        self.fd.write('\r')


def main(x: float = 1) -> None:
    """Demo."""
    from time import sleep
    spinner = Spinner()
    for _ in range(10000):
        spinner.spin()
        sleep(0.00005 * x)
    spinner.reset()
    print('Done!')


if __name__ == '__main__':
    main()
