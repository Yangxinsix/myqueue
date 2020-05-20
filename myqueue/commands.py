"""Definitions of commands.

There is a Command base class and five concrete classes:
ShellCommand, ShellScript, PythonScript, PythonModule and
PythonFunction.  Use the factory function command() to create
command objects.
"""
from typing import List, Dict, Any, Union
from pathlib import Path


class Command:
    """Base class."""
    def __init__(self, name: str, args: List[str]):
        self.args = args
        if args:
            name += '+' + '_'.join(self.args)
        self.name = name
        self.dct: Dict[str, Any] = {'args': args}
        self.short_name: str

    def set_non_standard_name(self, name: str) -> None:
        self.name = name
        self.dct['name'] = name

    def todict(self) -> Dict[str, Any]:
        raise NotImplementedError

    @property
    def fname(self):
        return self.name.replace('/', '\\')  # filename can't contain slashes


def command(cmd: str,
            args: List[str] = [],
            type: str = None,
            name: str = '') -> Command:
    """Create command object."""
    cmd, _, args2 = cmd.partition(' ')
    if args2:
        args = args2.split() + args
    path, sep, cmd = cmd.rpartition('/')
    if '+' in cmd:
        cmd, _, rest = cmd.rpartition('+')
        args = rest.split('_') + args
    cmd = path + sep + cmd

    if type is None:
        if cmd.startswith('shell:'):
            type = 'shell-command'
        elif cmd.endswith('.py'):
            type = 'python-script'
        elif '@' in cmd:
            type = 'python-function'
        elif path:
            type = 'shell-script'
        else:
            type = 'python-module'

    command: Command
    if type == 'shell-command':
        command = ShellCommand(cmd, args)
    elif type == 'shell-script':
        command = ShellScript(cmd, args)
    elif type == 'python-script':
        command = PythonScript(cmd, args)
    elif type == 'python-module':
        command = PythonModule(cmd, args)
    elif type == 'python-function':
        command = PythonFunction(cmd, args)
    else:
        raise ValueError

    if name:
        command.set_non_standard_name(name)

    return command


class ShellCommand(Command):
    def __init__(self, cmd: str, args: List[str]):
        Command.__init__(self, cmd, args)
        self.cmd = cmd
        self.short_name = cmd

    def __str__(self) -> str:
        return ' '.join([self.cmd[6:]] + self.args)

    def todict(self) -> Dict[str, Any]:
        return {**self.dct,
                'type': 'shell-command',
                'cmd': self.cmd}


class ShellScript(Command):
    def __init__(self, cmd: str, args: List[str]):
        Command.__init__(self, Path(cmd).name, args)
        self.cmd = cmd
        self.short_name = cmd

    def __str__(self) -> str:
        return ' '.join(['.', self.cmd] + self.args)

    def todict(self) -> Dict[str, Any]:
        return {**self.dct,
                'type': 'shell-script',
                'cmd': self.cmd}


class PythonScript(Command):
    def __init__(self, script: str, args: List[str]):
        path = Path(script)
        Command.__init__(self, path.name, args)
        if '/' in script:
            self.script = str(path.absolute())
        else:
            self.script = script
        self.short_name = path.name

    def __str__(self) -> str:
        return 'python3 ' + ' '.join([self.script] + self.args)

    def todict(self) -> Dict[str, Any]:
        return {**self.dct,
                'type': 'python-script',
                'cmd': self.script}


class PythonModule(Command):
    def __init__(self, mod: str, args: List[str]):
        Command.__init__(self, mod, args)
        self.mod = mod
        self.short_name = mod

    def __str__(self) -> str:
        return ' '.join(['python3', '-m', self.mod] + self.args)

    def todict(self) -> Dict[str, Any]:
        return {**self.dct,
                'type': 'python-module',
                'cmd': self.mod}


class PythonFunction(Command):
    def __init__(self, cmd: str, args: List[str]):
        if ':' in cmd:
            # Backwards compatibility with version 4:
            self.mod, self.func = cmd.rsplit(':', 1)
        else:
            self.mod, self.func = cmd.rsplit('@', 1)
        Command.__init__(self, cmd, args)
        self.short_name = cmd

    def __str__(self) -> str:
        args = ', '.join(repr(convert(arg)) for arg in self.args)
        mod = self.mod
        return f'python3 -c "import {mod}; {mod}.{self.func}({args})"'

    def todict(self) -> Dict[str, Any]:
        return {**self.dct,
                'type': 'python-function',
                'cmd': self.mod + '@' + self.func}


def convert(x: str) -> Union[bool, int, float, str]:
    """Convert str to bool, int, float or str."""
    if x == 'True':
        return True
    if x == 'False':
        return False
    try:
        f = float(x)
    except ValueError:
        return x
    if int(f) == f:
        return int(f)
    return f
