from enum import Enum


class State(Enum):
    """Task-state enum.

    >>> State.queued == 'queued'
    True
    >>> State.done in {'queued', 'running'}
    False
    """

    UNDEFINED = '?'
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

    def __str__(self) -> str:
        return self.name

    def is_bad(self) -> bool:
        """Return true for UNDEFINED, FAILED, TIMEOUT, MEMORY and CANCELED.

        >>> State.running.is_bad()
        False
        """
        return self.name.isupper()
