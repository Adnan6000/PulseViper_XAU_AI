import importlib



backup_module = importlib.import_module("02_AI.Database.backup")

backup = backup_module.backup


def test_backup():

    file = backup.create_backup()

    assert file.exists()
