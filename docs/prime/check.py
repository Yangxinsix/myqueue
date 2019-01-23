import json
from pathlib import Path

dct = json.loads(Path('factors.json').read_text())
factors = dct['factors']
if len(factors) == 1:
    Path('PRIME').write_text('')  # create empty file
