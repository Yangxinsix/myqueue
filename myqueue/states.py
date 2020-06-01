from enum import Enum


class State(Enum):
    queued = 'q'
    hold = 'h'
    running = 'r'
    done = 'd'
    FAILED = 'F'
    TIMEOUT = 'T'
    MEMORY = 'M'
    CANCELED = 'C'

    def azxdg__eq__(self, other):
        return self.name == other


if __name__ == '__main__':
    q = State.queued
    F = State.FAILED
    assert q == 'queued'
    assert q != F
    assert q == q
    assert q in {'queued'}
    assert q not in {'done'}
