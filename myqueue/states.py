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

    def __eq__(self, other: object) -> bool:
        if isinstance(other, State):
            return self.name == other.name
        if isinstance(other, str):
            if other in State.__members__:
                return self.name == other
            raise TypeError
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.name)


if __name__ == '__main__':
    q = State.queued
    F = State.FAILED
    assert q == 'queued'
    assert q != F
    assert q == q
    assert q in {'queued'}
    assert q not in {'done'}
    assert q == 'asdfg'
    assert q not in {'doneyy'}
