import yfinance as yf
import requests

def get_live_prices(symbols):
    """
    Fetch live prices using standard yfinance.
    Returns empty dict if blocked or failed.
    """
    current_prices = {}
    
    # Try to set a basic user agent, but let yfinance handle the rest
    # Using 'v8' endpoint via Ticker.fast_info is usually best
    
    for sym in symbols:
        # Symbol Mapping
        if '.' not in sym:
            mapped_sym = f"{sym}.NS"
        else:
            mapped_sym = sym
            
        try:
            ticker = yf.Ticker(mapped_sym)
            price = None
            
            # fast_info
            if hasattr(ticker, 'fast_info'):
                try:
                    price = ticker.fast_info.get('last_price')
                except:
                    pass
            
            # history fallback
            if price is None:
                try:
                     hist = ticker.history(period="1d")
                     if not hist.empty:
                         price = hist['Close'].iloc[-1]
                except:
                    pass

            if price is not None:
                current_prices[sym] = price
            else:
                # Silent fail
                pass
                
        except Exception:
            # Silent fail to avoid crashing orchestration
            pass
            
    return current_prices

if __name__ == "__main__":
    # Test
    test_symbols = ["RELIANCE", "INFY", "GOLDBEES"]
    prices = get_live_prices(test_symbols)
    print("Live Prices:", prices)
