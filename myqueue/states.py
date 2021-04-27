from enum import Enum
from typing import Set


class State(Enum):
    """Task-state enum.

    The following 9 states are defined:

    >>> for state in State:
    ...     state
    <State.UNDEFINED: 'U'>
    <State.queued: 'q'>
    <State.hold: 'h'>
    <State.running: 'r'>
    <State.done: 'd'>
    <State.FAILED: 'F'>
    <State.TIMEOUT: 'T'>
    <State.MEMORY: 'M'>
    <State.CANCELED: 'C'>

    >>> State.queued == State.queued
    True
    >>> State.queued == 'queued'
    True
    >>> State.queued == 'queue'
    Traceback (most recent call last):
      ...
    TypeError: Unknown state: queue
    >>> State.queued == 117
    False
    >>> State.done in {'queued', 'running'}
    False
    >>> State.str2states('dA')
    """

    undefined = 'u'
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
            raise TypeError(f'Unknown state: {other}')
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.name)

    def __str__(self) -> str:
        return self.name

    def is_bad(self) -> bool:
        """Return true for FAILED, TIMEOUT, MEMORY and CANCELED.

        >>> State.running.is_bad()
        False
        """
        return self.name.isupper()

    @staticmethod
    def str2states(s: str) -> Set['State']:
        """"""
        states: Set[State] = set()
        for c in s:
            if s == 'a':
                states.update([State.queued,
                               State.hold,
                               State.running,
                               State.done])
            elif s == 'A':
                states.update([State.FAILED,
                               State.CANCELED,
                               State.TIMEOUT,
                               State.MEMORY])
            else:
                try:
                    states.add(State(s))
                except ValueError:
                    raise ValueError(
                        'Unknown state: ' + s +
                        '.  Must be one of q, h, r, d, F, C, T, M, a or A.')
        return states
    