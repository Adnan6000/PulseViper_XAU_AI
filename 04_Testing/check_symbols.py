import MetaTrader5 as mt5

if not mt5.initialize():
    print(mt5.last_error())
    quit()

symbols = mt5.symbols_get()

for s in symbols:
    print(s.name)

mt5.shutdown()