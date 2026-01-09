import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def process_stock_data(file_path):
    # Load the excel file skipping metadata rows
    df = pd.read_excel(file_path, header=5)
    
    # Basic cleaning
    df = df.dropna(subset=['Stock name', 'Symbol', 'Execution date and time'])
    
    # Convert date to datetime
    df['Execution date and time'] = pd.to_datetime(df['Execution date and time'], format='%d-%m-%Y %I:%M %p')
    
    # Filter for Executed orders
    df = df[df['Order status'] == 'Executed']
    
    # Sort by date
    df = df.sort_values('Execution date and time')
    
    # Calculate impact on quantity and value
    # BUY: Quantity +, Value -
    # SELL: Quantity -, Value +
    df['Quantity_Change'] = df.apply(lambda x: x['Quantity'] if x['Type'] == 'BUY' else -x['Quantity'], axis=1)
    df['Value_Change'] = df.apply(lambda x: -x['Value'] if x['Type'] == 'BUY' else x['Value'], axis=1)
    
    # Calculate cumulative portfolio value and snapshot over time
    # However, for QoQ growth of portfolio, we need to track the value of current holdings at different points in time.
    # Since we don't have historical prices in the sheet, "growth" here might mean "Net Cash Invested" vs "Current Value"
    # But for QoQ based only on this sheet, we can track "Net Investment" or "Realized P&L"
    
    # Let's create a daily snapshot of the portfolio
    all_dates = pd.date_range(start=df['Execution date and time'].min().date(), end=df['Execution date and time'].max().date())
    portfolio_daily = pd.DataFrame(index=all_dates)
    
    # Group by date to get daily activity
    df['Date'] = df['Execution date and time'].dt.date
    daily_activity = df.groupby('Date').agg({
        'Quantity_Change': 'sum',
        'Value_Change': 'sum'
    })
    
    portfolio_daily = portfolio_daily.join(daily_activity, how='left').fillna(0)
    portfolio_daily['Cumulative_Investment'] = -portfolio_daily['Value_Change'].cumsum()
    
    # Calculate current holdings per Symbol
    # Group by Symbol to get Net Quantity and Total Net Cost
    holdings = df.groupby(['Symbol', 'Stock name']).agg({
        'Quantity_Change': 'sum',
        'Value_Change': 'sum'
    })
    
    # Only keep current holdings (Quantity > 0)
    holdings = holdings[holdings['Quantity_Change'] > 0]
    holdings['Avg_Price'] = -holdings['Value_Change'] / holdings['Quantity_Change']
    holdings['Total_Value'] = -holdings['Value_Change']
    
    return df, portfolio_daily, holdings

if __name__ == "__main__":
    df, portfolio, holdings = process_stock_data('stock_order_history.xlsx')
    print("Data processed successfully.")
    print(df.head())
    print("\nCurrent Holdings:")
    print(holdings)
