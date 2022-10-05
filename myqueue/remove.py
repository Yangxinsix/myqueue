def remove(self, selection: Selection) -> None:
    """Remove or cancel tasks."""

    self._read()

    tasks = selection.select(self.tasks)
    tasks = self.find_depending(tasks)

    self._remove(tasks)


def _remove(self, tasks: list[Task]) -> None:
    t = time.time()
    for task in tasks:
        if task.tstop is None:
            task.tstop = t  # XXX is this for dry_run only?

    if self.dry_run:
        if tasks:
            pprint(tasks, 0)
            print(plural(len(tasks), 'task'), 'to be removed')
    else:
        if self.verbosity > 0:
            if tasks:
                pprint(tasks, 0)
                print(plural(len(tasks), 'task'), 'removed')
        for task in tasks:
            if task.state in ['running', 'hold', 'queued']:
                self.scheduler.cancel(task)
            self.tasks.remove(task)
            # XXX why cancel?
            task.cancel_dependents(self.tasks, time.time())
            self.changed.add(task)

