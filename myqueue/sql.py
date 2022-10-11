from pathlib import Path
import sqlite3

INIT = """\
CREATE TABLE tasks (
  id INTEGER PRIMARY KEY,
  folder TEXT,
  state CHARCTER,
  cmd TEXT,
  resources: TEXT,
  restart INTEGER,
  workflow INTEGER,
  deps TEXT,
  diskspace INTEGER,
  notifications TEXT,
  creates TEXT,
  tqueued REAL,
  trunning REAL,
  tstop REAL,
  error TEXT,
  user TEXT);
CREATE INDEX folder_index on tasks(folder);
CREATE INDEX state_index on tasks(state);
"""


def create_db(path: Path):
    sqlite3.execute(INIT)


def write_tasks(tasks, db):
    ...
