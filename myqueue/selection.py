from __future__ import annotations
from pathlib import Path

from myqueue.states import State
from myqueue.utils import normalize_folder


class Selection:
    """Object used for selecting tasks."""

    def __init__(self,
                 ids: set[int] | None = None,
                 name: str | None = None,
                 states: set[State] = set(),
                 folders: list[Path] = [],
                 recursive: bool = True,
                 error: str | None = None):
        """Selection.

        Selection is based on:

            ids

        or:

            any combination of name, state, folder and error message.

        Use recursive=True to allow for tasks inside a folder.
        """

        self.ids = ids
        self.name = name
        self.states = states
        self.folders = folders
        self.recursive = recursive
        self.error = error

    def __repr__(self) -> str:
        return (f'Selection({self.ids}, {self.name}, {self.states}, '
                f'{self.folders}, {self.recursive}, {self.error})')

    def sql_where_statement(self, root: Path) -> tuple[str, list]:
        if self.ids is not None:
            q = ', '.join('?' * len(self.ids))
            return (f'id IN ({q})', list(self.ids))

        parts = []
        args = []
        if len(self.states) < 8:
            q = ', '.join('?' * len(self.states))
            parts.append(f'state IN ({q})')
            args += [state.value for state in self.states]

        if self.folders:
            part = []
            for folder in self.folders:
                f = normalize_folder(folder, root)
                if self.recursive:
                    part.append('folder GLOB ?')
                    args.append(f'{f}*')
                else:
                    part.append('folder = ?')
                    args.append(f)
            parts.append(f'({" OR ".join(part)})')

        if self.name:
            parts.append('name GLOB ?')
            args.append(self.name)

        if self.error:
            parts.append('error GLOB ?')
            args.append(self.error)

        return ' AND '.join(f'({part})' for part in parts), args
