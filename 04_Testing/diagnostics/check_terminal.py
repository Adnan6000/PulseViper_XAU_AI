import MetaTrader5 as mt5

if not mt5.initialize():
    print(mt5.last_error())
    quit()

print(mt5.terminal_info())
print(mt5.account_info())

mt5.shutdown()