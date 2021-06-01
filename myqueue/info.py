def info(queue, id: int) -> None:
    """Print information about a single task."""
    self._read()
    task = Selection({id}).select(self.tasks)[0]
    print(json.dumps(task.todict(), indent='    '))
    if self.verbosity > 1:
        path = self.scheduler.error_file(task)
        try:
            err = path.read_text()
        except FileNotFoundError:
            pass
        else:
            try:
                N = os.get_terminal_size().columns - 1
            except OSError:
                N = 70
            print(f'\nError file: {path}')
            print('v' * N)
            print(err)
            print('^' * N)

