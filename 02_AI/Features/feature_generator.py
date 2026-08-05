"""
===============================================================================
Module      : feature_generator.py
Project     : PulseViper XAU AI
Version     : 3.1
Purpose     : Central Feature Engineering Pipeline
===============================================================================
"""

from pathlib import Path
import sys
import importlib
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


trend = importlib.import_module(
    "02_AI.Features.trend_features"
).trend


class FeatureGenerator:

    def generate(
        self,
        df: pd.DataFrame
    ) -> pd.DataFrame:

        data = df.copy()

        # Trend Features
        data = trend.generate(data)

        return data


feature_generator = FeatureGenerator()