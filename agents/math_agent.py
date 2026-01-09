import pandas as pd
from pyxirr import xirr
from datetime import date

class MathAgent:
    def __init__(self, data_processor):
        """
        data_processor: Instance of DataProcessor or similar that holds the dataframe
        """
        self.df = data_processor.df
        # We need a reference to the processed portfolio data for cash flows
        # Assuming data_processor has 'portfolio_daily' or we can derive cash flows from df
        
    def calculate_xirr(self):
        """
        Calculates the XIRR for the entire portfolio.
        Cash Flows:
        - Dates: Transaction Dates
        - Amounts: 
            - Negative for BUY (Outflow)
            - Positive for SELL (Inflow)
            - Positive Current Value for "Today" (Terminal Value)
        """
        try:
            # 1. Get realized cash flows from transactions
            cash_flows = self.df[['Execution date and time', 'Value', 'Type']].copy()
            cash_flows['Amount'] = cash_flows.apply(
                lambda x: -x['Value'] if x['Type'] == 'BUY' else x['Value'], axis=1
            )
            
            # Prepare format for pyxirr (date, amount)
            dates = cash_flows['Execution date and time'].dt.date.tolist()
            amounts = cash_flows['Amount'].tolist()
            
            # 2. Add Terminal Value (Current Portfolio Value)
            # We need to calculate current value. 
            # Ideally this comes from the Live Data agent or the internal accounting.
            # For accurate XIRR, we need the CURRENT live value of holdings.
            # If not available, we use the cost basis (which makes XIRR == 0 roughly), so we strongly prefer live value.
            # For now, let's rely on the passed data_processor to give us 'current_holdings'
            
            # Re-calculate or fetch current value
            # Note: This agent assumes it gets the LATEST value somehow. 
            # To keep it simple, we will ask the orchestrator to pass the 'current_terminal_value' 
            # But here we are independent. Let's calculate purely realized XIRR? No, XIRR needs terminal value.
            
            return "XIRR requires current portfolio value. Please invoke with terminal value."

        except Exception as e:
            return f"Error calculating XIRR: {e}"

    def compute_xirr_with_terminal_value(self, current_value):
        try:
            # 1. Cash flows from history
            cash_flows = self.df[['Execution date and time', 'Value', 'Type']].copy()
            # BUY is Outflow (-), SELL is Inflow (+)
            cash_flows['Amount'] = cash_flows.apply(
                lambda x: -x['Value'] if x['Type'] == 'BUY' else x['Value'], axis=1
            )
            
            dates = cash_flows['Execution date and time'].dt.date.tolist()
            amounts = cash_flows['Amount'].tolist()
            
            # 2. Add Terminal Value
            dates.append(date.today())
            amounts.append(current_value)
            
            # 3. Calculate
            result = xirr(dates, amounts)
            if result is None:
                return 0.0
            return result * 100 # Return as percentage
            
        except Exception as e:
            return f"Error accounting XIRR: {e}"

    def get_summary_stats(self):
        """
        Returns basic math stats like Total Invested, Total Realized, etc.
        """
        total_invested = self.df[self.df['Type'] == 'BUY']['Value'].sum()
        total_sold = self.df[self.df['Type'] == 'SELL']['Value'].sum()
        
        return {
            "Total Capital Deployed": total_invested,
            "Total Capital Realized": total_sold,
            "Net Invested Capital": total_invested - total_sold
        }
