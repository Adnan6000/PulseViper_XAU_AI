"""
PulseViper Database Backup
"""

from pathlib import Path
import shutil
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parents[2]

DATABASE = ROOT_DIR / "01_Data" / "pulseviper.db"
BACKUP_DIR = ROOT_DIR / "01_Data" / "Backups"


class BackupManager:

    def create_backup(self) -> Path:

        BACKUP_DIR.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        backup_file = BACKUP_DIR / f"pulseviper_backup_{timestamp}.db"

        shutil.copy2(DATABASE, backup_file)

        return backup_file


backup = BackupManager()