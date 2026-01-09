import os
import pandas as pd
import httpx
import certifi
from groq import Groq
from dotenv import load_dotenv
from data_processor import process_stock_data

load_dotenv()

class StockAgent:
    def __init__(self, model_name="openai/gpt-oss-120b"):
        self.api_key = os.getenv("GROQ_API_KEY")
        
        # SSL certificate handling for Windows/Corporate environments
        try:
            # Try to use certifi for verification
            http_client = httpx.Client(verify=certifi.where())
        except Exception:
            # Fallback
            http_client = httpx.Client(verify=False)
            print("Warning: SSL verification disabled due to environment issues.")

        self.client = Groq(api_key=self.api_key, http_client=http_client)
        self.model_name = model_name
        self.df, self.portfolio, self.holdings = process_stock_data('stock_order_history.xlsx')
        
        # Conversation history
        stats = self._get_portfolio_stats()
        
        # Prepare holdings summary for the prompt
        holdings_text = self.holdings.to_string()
        
        # Prepare transaction history summary (last 200 transactions to fit context)
        # We only need relevant columns for the LLM: Execution date, Stock name, Type, Quantity, Value
        history_df = self.df[['Execution date and time', 'Stock name', 'Symbol', 'Type', 'Quantity', 'Value']].tail(200)
        history_text = history_df.to_string(index=False)
        
        system_prompt = f"""
        You are a financial analyst agent. You have access to the user's stock order history and portfolio metrics.
        All currency values are in Indian Rupees (INR, ₹).
        
        Current Portfolio Statistics (in INR):
        - Current Portfolio Value: {stats['current_value']}
        - Total Orders Executed: {stats['total_orders']}
        - QoQ Growth (last few quarters): {stats['qoq_growth']}
        - 6-Month Growth: {stats['six_month_growth']}%
        
        Current Asset Holdings (Summary in INR):
        {holdings_text}
        
        Detailed Transaction History (Last 200 Executed Orders):
        {history_text}
        
        Data Context:
        The user has provided an Excel sheet named 'stock_order_history.xlsx' which records their stock transactions (BUY/SELL).
        
        Specific Instructions:
        1. Answer queries accurately based on the provided stats, holdings, AND transaction history.
        2. If the user asks about a specific stock (e.g., "GoldBees"), look it up in the holdings table above.
        3. For queries about specific holdings, use this EXACT prefix in your response: 
           "Your current Valuation on <StockName> in INR is as follows," 
           followed by the details (Quantity, Average Price, Total Value).
        4. If the user asks about specific trades or dates (e.g., "Did I buy X in November 2025?"), search the "Detailed Transaction History" provided above and give a specific answer based on those rows.
        5. If requested for QoQ or growth, use the calculated summary stats.
        6. Always use the ₹ symbol or "INR" when mentioning monetary values.
        """
        self.messages = [{"role": "system", "content": system_prompt}]

    def _get_portfolio_stats(self):
        # Calculate QoQ growth
        self.portfolio['Quarter'] = self.portfolio.index.to_period('Q')
        qoq = self.portfolio.groupby('Quarter')['Cumulative_Investment'].last()
        qoq_growth = (qoq.pct_change() * 100).fillna(0)
        
        # Calculate 6-month growth
        latest_date = self.portfolio.index.max()
        six_months_ago = latest_date - pd.DateOffset(months=6)
        if six_months_ago in self.portfolio.index:
            val_now = self.portfolio.loc[latest_date, 'Cumulative_Investment']
            val_then = self.portfolio.loc[six_months_ago, 'Cumulative_Investment']
            six_month_growth = ((val_now - val_then) / val_then) * 100 if val_then != 0 else 0
        else:
            six_month_growth = "Insufficient data for 6-month calculation"
            
        return {
            "qoq_growth": qoq_growth.to_dict(),
            "six_month_growth": six_month_growth,
            "current_value": self.portfolio['Cumulative_Investment'].iloc[-1],
            "total_orders": len(self.df)
        }

    def chat(self, user_query):
        self.messages.append({"role": "user", "content": user_query})
        
        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=self.messages,
            temperature=0,
        )
        
        response = completion.choices[0].message.content
        self.messages.append({"role": "assistant", "content": response})
        return response

if __name__ == "__main__":
    import sys
    # Set encoding to utf-8 for Windows console
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    agent = StockAgent()
    print("Agent: Hello! I've analyzed your stock history. Ask me anything about your portfolio (type 'exit' to quit).")
    
    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("Agent: Goodbye! Happy investing.")
                break
            
            if not user_input.strip():
                continue
                
            response = agent.chat(user_input)
            print(f"\nAgent: {response}")
            
        except KeyboardInterrupt:
            print("\nAgent: Goodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")
