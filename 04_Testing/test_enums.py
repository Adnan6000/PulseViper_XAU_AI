from pathlib import Path
import sys
import importlib

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

enums = importlib.import_module("02_AI.Common.enums")


def test_enums():

    assert enums.LiquidityType.BUY_SIDE.value == "BUY_SIDE"

    assert enums.LiquidityType.SELL_SIDE.value == "SELL_SIDE"

    assert enums.BOSType.BULLISH.value == "BULLISH"

    assert enums.CHOCHType.BEARISH.value == "BEARISH"