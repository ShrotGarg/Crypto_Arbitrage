import math
import itertools
import ccxt
import time

# === CONFIG ===
money = 10000  # start with 10K
FEE = 0.001  # 0.1% Binance spot fee
TEST_MODE = True  # Set False for real Binance data
MAX_PATH_LEN = 4
TOP_COINS = [
    "BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE",
    "DOT", "MATIC", "AVAX", "LTC", "TRX", "LINK", "ATOM", "UNI"
]

exchange = ccxt.binance()

def build_graph():
    """Build graph of exchange rates"""
    graph = {}

    if TEST_MODE:
        fake_rates = {
            ("BTC", "ETH"): 20.0,
            ("ETH", "USDT"): 2000.0,
            ("USDT", "BTC"): 0.00055
        }
        for (base, quote), rate in fake_rates.items():
            graph.setdefault(base, {})[quote] = rate * (1 - FEE)
            graph.setdefault(quote, {})[base] = (1 / rate) * (1 - FEE)
        return graph

    print("Fetching tickers...")
    tickers = exchange.fetch_tickers()
    for symbol, data in tickers.items():
        try:
            base, quote = symbol.split('/')
        except Exception:
            continue
        if base not in TOP_COINS or quote not in TOP_COINS:
            continue
        if 'bid' not in data or data['bid'] is None:
            continue
        price = data['bid']
        graph.setdefault(base, {})[quote] = price * (1 - FEE)
        graph.setdefault(quote, {})[base] = (1 / price) * (1 - FEE)
    return graph


def simulate_path(graph, path, starting_money):
    """Simulate trading along a path"""
    money_cur = starting_money
    for i in range(len(path) - 1):
        u, v = path[i], path[i+1]
        if v not in graph[u]:
            return None
        rate = graph[u][v]
        money_cur *= rate
    return money_cur


def find_and_trade_cycles(graph, max_len=3):
    """Find every cycle, trade if profitable, return all path results"""
    global money
    currencies = list(graph.keys())
    profitable_trades = []  # store profitable ones
    all_paths = []          # store everything for display

    for start in currencies:
        for path_len in range(2, max_len+1):
            for perm in itertools.permutations(currencies, path_len-1):
                cycle = [start] + list(perm) + [start]
                final_money = simulate_path(graph, cycle, money)
                if final_money is None:
                    continue

                change_pct = ((final_money - money) / money) * 100
                if change_pct > 0:
                    trade_info = (
                        f"✅ TRADE: {' -> '.join(cycle)} | PROFIT {change_pct:+.4f}% | "
                        f"Money before: {money:.6f} → after: {final_money:.6f}"
                    )
                    profitable_trades.append(trade_info)
                    money = final_money  # update balance
                else:
                    trade_info = (
                        f"Path: {' -> '.join(cycle)} | LOSS {change_pct:+.4f}%"
                    )
                all_paths.append(trade_info)

    return all_paths, profitable_trades


if __name__ == "__main__":
    while True:
        graph = build_graph()
        all_paths, profitable_trades = find_and_trade_cycles(graph, MAX_PATH_LEN)

        # Print all paths first
        print("\n=== Paths This Cycle ===")
        for p in all_paths:
            print(p)

        # Then highlight profitable trades before balance
        if profitable_trades:
            print("\n=== Profitable Trades This Cycle ===")
            for t in profitable_trades:
                print(t)
                
        # Shows your balance after each cycle
        print(f"\n💰 Current Balance: {money:.6f}\n")

        if TEST_MODE:
            break
        time.sleep(5) # To not surpass the binance rate limit
