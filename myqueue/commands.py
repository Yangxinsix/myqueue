from typing import List, Dict, Any
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
    except (AttributeError, ImportError):  # , ModuleNotFoundError):
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
        else:
            mod = cmd
            func = None
            if is_module(mod):
                type = 'python-module'
            else:
                mod, _, func = cmd.rpartition('.')
                if func:
                    if is_module(mod):
                        type = 'python-function'
                    else:
                        type = 'shell-script'
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
        return ' '.join(['.'] + ['./' + self.cmd] + self.args)

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
        self.mod, self.func = cmd.rsplit('.', 1)
        Command.__init__(self, cmd, args)

    def __str__(self):
        args = []
        for arg in self.args:
            for t in [int, float]:
                try:
                    arg = t(arg)
                    break
                except ValueError:
                    pass
            args.append(repr(arg))
        args = ', '.join(args)

        return ('python3 -c "import {mod}; {mod}.{func}({args})"'
                .format(mod=self.mod, func=self.func, args=args))

    def todict(self):
        return {'type': 'python-function',
                'cmd': self.name.split('+')[0],
                'args': self.args}
