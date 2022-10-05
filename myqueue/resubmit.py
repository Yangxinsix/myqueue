def resubmit(self,
             selection: Selection,
             resources: Resources | None) -> None:
    """Resubmit failed or timed-out tasks."""
    self._read()
    tasks = []
    for task in selection.select(self.tasks):
        if task.state not in {'queued', 'hold', 'running'}:
            self.tasks.remove(task)
        task.remove_state_file()
        self.changed.add(task)
        task = Task(task.cmd,
                    deps=task.deps,
                    resources=resources or task.resources,
                    folder=task.folder,
                    restart=task.restart,
                    workflow=task.workflow,
                    creates=task.creates,
                    diskspace=0)
        tasks.append(task)
    self.submit(tasks, read=False)
