from pathlib import Path
from typing import List, Dict


def find_activation_scripts(folders: List[Path]) -> Dict[Path, Path]:
    scripts = {}
    for folder in folders:
        found = []
        while True:
            if folder in scripts:
                break

            script = folder / 'venv/activate'
            if script.is_file():
                found.append(folder)
                break

            script = folder / 'venv/bin/activate'
            if script.is_file():
                found.append(folder)
                break

            folder = folder.parent
            if folder == Path('/'):
                break

        for dir in found:
            scripts[dir] = script

    return {folder: scripts[folder]
            for folder in folders
            if folder in scripts}


if __name__ == '__main__':
    import sys
    scripts = find_activation_scripts([Path(dir) for dir in sys.argv[1:]])
    for folder, script in scripts.items():
        print(f'{folder}: {script}')
