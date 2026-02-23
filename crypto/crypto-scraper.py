import requests
import json

def get_crypto_prices(symbols):
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": ",".join(symbols),
        "vs_currencies": "usd",
        "include_market_cap": "true",
        "include_24hr_vol": "true",
        "include_24hr_change": "true"
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        return None

def main():
    symbols = ["bitcoin", "ethereum", "solana", "dusk-network"]
    data = get_crypto_prices(symbols)
    if data:
        report = []
        for sym in symbols:
            if sym in data:
                item = data[sym]
                report.append({
                    "symbol": sym,
                    "price": item.get("usd", "N/A"),
                    "market_cap": item.get("usd_market_cap", "N/A"),
                    "volume_24h": item.get("usd_24h_vol", "N/A"),
                    "change_24h": item.get("usd_24h_change", "N/A")
                })
        print("Crypto Report (CoinGecko)")
        print("=" * 50)
        for r in report:
            print(f"{r['symbol'].upper()}: $" + str(r['price']))
            print(f"  Market Cap: $" + str(r['market_cap']))
            print(f"  24h Vol: $" + str(r['volume_24h']))
            print(f"  24h Change: {r['change_24h']}%\n")
    else:
        print("Failed to fetch crypto data")

if __name__ == "__main__":
    main()