import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
import sys
import os

# Add wrapper to fetch history if needed. 
# For now we might assume we predict on Portfolio Value history or a specific stock
# If specific stock, we need to fetch history.
# Let's rely on LiveDataAgent (live_market) to fetch history or use portfolio history.

class PredictionAgent:
    def __init__(self, data_processor):
        self.portfolio_history = data_processor.portfolio
        
    def predict_portfolio_trend(self, days=30):
        """
        Predicts future portfolio value based on historical cumulative investment trend.
        Uses simple Linear Regression.
        """
        try:
            # Prepare data: X = Days since start, Y = Cumulative Value
            df = self.portfolio.copy()
            if df.empty:
                return "Not enough data to predict."
                
            df['Days'] = (df.index - df.index[0]).days
            
            X = df[['Days']].values
            y = df['Cumulative_Investment'].values
            
            # Train Model
            model = LinearRegression()
            model.fit(X, y)
            
            # Predict
            last_day = X[-1][0]
            future_days = np.array([[last_day + i] for i in range(1, days + 1)])
            predictions = model.predict(future_days)
            
            # Format result
            start_pred = predictions[0]
            end_pred = predictions[-1]
            trend = "Upward" if end_pred > start_pred else "Downward"
            
            return f"Based on historical trend (Linear Regression), your portfolio is projected to trend **{trend}**. \nExpected Value in 30 days: ₹{end_pred:,.2f}"
            
        except Exception as e:
            return f"Error predicting trend: {e}"
