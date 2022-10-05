from myqueue.selection import Selection
from myqueue.states import State
from myqueue.email import configure_email


def modify(self,
           selection: Selection,
           newstate: State,
           email: set[State]) -> None:
    """Modify task(s)."""
    self._read()
    tasks = selection.select(self.tasks)

    if email != {State.undefined}:
        configure_email(self.config)
        for task in tasks:
            if self.dry_run:
                print(task, email)
            else:
                task.notifications = ''.join(state.value
                                             for state in email)
                self.changed.add(task)

    if newstate != State.undefined:
        for task in tasks:
            if task.state == 'hold' and newstate == 'queued':
                if self.dry_run:
                    print('Release:', task)
                else:
                    self.scheduler.release_hold(task)
            elif task.state == 'queued' and newstate == 'hold':
                if self.dry_run:
                    print('Hold:', task)
                else:
                    self.scheduler.hold(task)
            elif task.state == 'FAILED' and newstate in ['MEMORY',
                                                         'TIMEOUT']:
                if self.dry_run:
                    print('FAILED ->', newstate, task)
                else:
                    task.state = newstate
                    self.changed.add(task)
            else:
                raise ValueError(f'Can\'t do {task.state} -> {newstate}!')
            print(f'{task.state} -> {newstate}: {task}')
            task.state = newstate
            self.changed.add(task)
