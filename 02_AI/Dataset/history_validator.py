"""
===============================================================================
Module      : history_validator.py
Project     : PulseViper XAU AI
Version     : 3.0
Purpose     : Enterprise History Validator
===============================================================================
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

    def validate(self, df: pd.DataFrame):

        self.validate_columns(df)
        self.validate_empty(df)
        self.validate_duplicates(df)
        self.validate_nulls(df)
        self.validate_ohlc(df)
        self.validate_sorting(df)

        return True

    def validate_columns(self, df):

        missing = [
            c for c in self.REQUIRED_COLUMNS
            if c not in df.columns
        ]

        if missing:
            raise ValueError(
                f"Missing Columns: {missing}"
            )

    def validate_empty(self, df):

        if df.empty:
            raise ValueError(
                "Dataset is empty."
            )

    def validate_duplicates(self, df):

        duplicates = df.duplicated().sum()

        if duplicates:
            raise ValueError(
                f"{duplicates} duplicate rows found."
            )

    def validate_nulls(self, df):

        total = df.isnull().sum().sum()

        if total:
            raise ValueError(
                f"{total} NULL values detected."
            )

    def validate_sorting(self, df):

        if not df["time"].is_monotonic_increasing:
            raise ValueError(
                "Dataset is not sorted by time."
            )

    def validate_ohlc(self, df):

        invalid = (
            (df["high"] < df["open"])
            |
            (df["high"] < df["close"])
            |
            (df["high"] < df["low"])
            |
            (df["low"] > df["open"])
            |
            (df["low"] > df["close"])
        )

        if invalid.any():

            raise ValueError(
                "Invalid OHLC values detected."
            )


validator = HistoryValidator()