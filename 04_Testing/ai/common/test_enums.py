import importlib



enums = importlib.import_module("02_AI.Common.enums")


def test_enums():

    assert enums.LiquidityType.BUY_SIDE.value == "BUY_SIDE"

    assert enums.LiquidityType.SELL_SIDE.value == "SELL_SIDE"

    assert enums.BOSType.BULLISH.value == "BULLISH"

    assert enums.CHOCHType.BEARISH.value == "BEARISH"
