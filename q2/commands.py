from typing import List
from pathlib import Path


class Command:
    def __init__(self, name: str, args: List[str]) -> None:
        self.args = args or []
        self.name = '_'.join([name] + self.args)


def command(cmd: str, args: List[str] = None, type: str = None) -> Command:
    if '_' in cmd:
        if args:
            raise ValueError
        cmd, _, rest = cmd.partition('_')
        args = rest.split('_')

    cmd, _, func = cmd.partition(':')

    if func:
        if type is not None and type != 'python-module':
            raise ValueError
        type = 'python-module'

    if type is None:
        if cmd.endswith('.py'):
            type = 'python-script'
        else:
            type = 'python-module'

    if type == 'shell-command':
        return ShellCommand(cmd, args)
    if type == 'python-script':
        return PythonScript(cmd, args)
    if type == 'python-module':
        return PythonModule(cmd, args, func)

    raise ValueError


class ShellCommand(Command):
    def __init__(self, cmd, args):
        Command.__init__(self, Path(cmd).name, args)
        self.cmd = cmd

    def __str__(self):
        return ' '.join([self.cmd] + self.args)

    def todict(self):
        return {'type': 'shell-command',
                'cmd': self.cmd,
                'args': self.args}


class PythonScript(Command):
    def __init__(self, script, args):
        Command.__init__(self, Path(script).name, args)
        self.script = script

    def __str__(self):
        return 'python3 ' + ' '.join([self.script] + self.args)

    def todict(self):
        return {'type': 'python-script',
                'cmd': self.script,
                'args': self.args}


class PythonModule(Command):
    def __init__(self, mod, args, func):
        name = mod
        if func:
            name += ':' + func
        Command.__init__(self, name, args)
        self.mod = mod
        self.func = func

    def __str__(self):
        if self.func:
            args = ', '.join(self.args)
            return ('python3 -c "import {mod}; {mod}.{func}({args})"'
                    .format(mod=self.mod, func=self.func, args=args))
        return ' '.join(['python3', '-m', self.mod] + self. args)

    def todict(self):
        return {'type': 'python-module',
                'cmd': self.name.split('_')[0],
                'args': self.args}
