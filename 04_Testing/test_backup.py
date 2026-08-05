from pathlib import Path
import importlib
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

backup_module = importlib.import_module("02_AI.Database.backup")

backup = backup_module.backup


def test_backup():

    file = backup.create_backup()

    assert file.exists()