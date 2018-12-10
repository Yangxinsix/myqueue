from typing import List, Dict, Any, Union
from pathlib import Path
from importlib.util import find_spec


class Command:
    def __init__(self, name: str, args: List[str]) -> None:
        self.args = args or []
        if args:
            name += '+' + '_'.join(self.args)
        self.name = name

    def todict(self)-> Dict[str, Any]:
        raise NotImplementedError


def is_module(mod: str) -> bool:
    try:
        m = find_spec(mod)
        return m is not None
    except (AttributeError, ImportError, ValueError):
        return False


def command(cmd: str,
            args: List[str] = [],
            type: str = None) -> Command:
    path, sep, name = cmd.rpartition('/')
    if '+' in name:
        name, _, rest = name.rpartition('+')
        args = rest.split('_') + args
    cmd = path + sep + name

    if type is None:
        if cmd.endswith('.py'):
            type = 'python-script'
        elif ':' in cmd:
            type = 'python-function'
        elif is_module(cmd):
            type = 'python-module'
        else:
            type = 'shell-script'

    if type == 'shell-script':
        return ShellScript(cmd, args)
    if type == 'python-script':
        return PythonScript(cmd, args)
    if type == 'python-module':
        return PythonModule(cmd, args)
    if type == 'python-function':
        return PythonFunction(cmd, args)

    raise ValueError


class ShellScript(Command):
    def __init__(self, cmd, args):
        Command.__init__(self, Path(cmd).name, args)
        self.cmd = cmd

    def __str__(self):
        if '/' in self.cmd:
            return ' '.join(['.', self.cmd] + self.args)
        return ' '.join([self.cmd] + self.args)

    def todict(self):
        return {'type': 'shell-script',
                'cmd': self.cmd,
                'args': self.args}


class PythonScript(Command):
    def __init__(self, script, args):
        path = Path(script)
        Command.__init__(self, path.name, args)
        if '/' in script:
            self.script = str(path.absolute())
        else:
            self.script = script

    def __str__(self):
        return 'python3 ' + ' '.join([self.script] + self.args)

    def todict(self):
        return {'type': 'python-script',
                'cmd': self.script,
                'args': self.args}


class PythonModule(Command):
    def __init__(self, mod, args):
        Command.__init__(self, mod, args)
        self.mod = mod

    def __str__(self):
        return ' '.join(['python3', '-m', self.mod] + self.args)

    def todict(self):
        return {'type': 'python-module',
                'cmd': self.name.split('+')[0],
                'args': self.args}


class PythonFunction(Command):
    def __init__(self, cmd, args):
        self.mod, self.func = cmd.rsplit(':', 1)
        Command.__init__(self, cmd, args)

    def __str__(self):
        args = ', '.join(repr(convert(arg)) for arg in self.args)
        return ('python3 -c "import {mod}; {mod}.{func}({args})"'
                .format(mod=self.mod, func=self.func, args=args))

    def todict(self):
        return {'type': 'python-function',
                'cmd': self.name.split('+')[0],
                'args': self.args}


def convert(x: str) -> Union[bool, int, float, str]:
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
