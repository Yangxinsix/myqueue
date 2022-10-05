def sync(self) -> None:
    """Syncronize queue with the real world."""
    self._read()
    in_the_queue = {'running', 'hold', 'queued'}
    ids = self.scheduler.get_ids()
    cancel = []
    remove = []
    for task in self.tasks:
        if task.id not in ids:
            if task.state in in_the_queue:
                cancel.append(task)
            if not task.folder.is_dir():
                remove.append(task)

    if cancel:
        if self.dry_run:
            print(plural(len(cancel), 'job'), 'to be canceled')
        else:
            for task in cancel:
                task.state = State.CANCELED
                self.changed.add(task)
            print(plural(len(cancel), 'job'), 'canceled')

    if remove:
        if self.dry_run:
            print(plural(len(remove), 'job'), 'to be removed')
        else:
            for task in remove:
                self.tasks.remove(task)
                self.changed.add(task)
            print(plural(len(remove), 'job'), 'removed')
