"""
PulseViper History Validator
Enterprise Data Quality Engine
"""

import pandas as pd


class HistoryValidator:

    REQUIRED_COLUMNS = [
        "time",
        "open",
        "high",
        "low",
        "close",
        "tick_volume",
        "spread",
    ]

    def validate_columns(self, df: pd.DataFrame):

        missing = []

        for column in self.REQUIRED_COLUMNS:

            if column not in df.columns:
                missing.append(column)

        if missing:
            raise ValueError(
                f"Missing Columns: {missing}"
            )

        return True

    def validate_empty(self, df: pd.DataFrame):

        if df.empty:
            raise ValueError("Dataset is empty.")

        return True

    def validate_duplicates(self, df: pd.DataFrame):

        duplicates = df.duplicated().sum()

        if duplicates > 0:
            raise ValueError(
                f"Duplicate rows found: {duplicates}"
            )

        return True

    def validate_nulls(self, df: pd.DataFrame):

        nulls = df.isnull().sum().sum()

        if nulls > 0:
            raise ValueError(
                f"Dataset contains {nulls} NULL values."
            )

        return True


validator = HistoryValidator()