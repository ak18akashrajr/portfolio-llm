import sys
import os

# Add parent directory to path to import live_market
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "live-data"))
from live_market import get_live_prices

class LiveDataAgent:
    def __init__(self):
        pass

    def get_latest_prices(self, symbols):
        """
        Fetches live prices for the given symbols.
        """
        return get_live_prices(symbols)

    def calculate_current_valuation(self, holdings_df):
        """
        Calculates current market value of the portfolio.
        holdings_df: DataFrame with 'Symbol' and 'Quantity' (Net)
        """
        if holdings_df.empty:
            return 0.0, {}

        # Reset index if Symbol is the index
        if 'Symbol' not in holdings_df.columns:
            holdings = holdings_df.reset_index()
        else:
            holdings = holdings_df

        unique_symbols = holdings['Symbol'].unique().tolist()
        
        # Try to fetch prices
        prices = {}
        try:
            prices = self.get_latest_prices(unique_symbols)
        except:
            pass # prices remains empty
            
        total_value = 0.0
        details = {}
        
        for index, row in holdings.iterrows():
            sym = row['Symbol']
            qty = row.get('Quantity_Change', row.get('Quantity', 0))
            cost_value = row.get('Total_Value', 0) # This is the invested amount provided by processor
            
            # Heuristic for mapping
            mapped_sym = f"{sym}.NS" if '.' not in sym else sym
            
            price = prices.get(sym, prices.get(mapped_sym, 0))
            
            if price > 0:
                market_val = qty * price
                details[sym] = {
                    "price": price,
                    "value": market_val,
                    "qty": qty,
                    "status": "Live"
                }
                total_value += market_val
            else:
                # Fallback to cost basis so we don't return 0 for everything
                # This ensures the portfolio value is at least the invested value (conservative/flat view)
                market_val = cost_value
                total_value += market_val
                details[sym] = {
                    "price": 0, # Indieates missing
                    "value": market_val,
                    "qty": qty,
                    "status": "Est. (Cost)"
                }
            
        return total_value, details
