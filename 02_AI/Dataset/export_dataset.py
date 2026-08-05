"""
PulseViper Dataset Exporter
"""

from pathlib import Path
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]

EXPORT_DIR = ROOT_DIR / "01_Data" / "Raw"

EXPORT_DIR.mkdir(exist_ok=True)


class DatasetExporter:

    def export(self, dataframe: pd.DataFrame, filename: str):

        path = EXPORT_DIR / filename

        dataframe.to_csv(path, index=False)

        return path


exporter = DatasetExporter()