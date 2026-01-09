from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

class AnalyticsAgent:
    def __init__(self, data_processor, model_name="openai/gpt-oss-120b"):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model_name = model_name
        self.df = data_processor.df
        self.holdings = data_processor.holdings
        # We can also access portfolio_daily if needed
        self.portfolio = data_processor.portfolio
        
        # Prepare context data once
        self.holdings_str = self.holdings.to_string()
        self.history_str = self.df.sort_values('Execution date and time').tail(50).to_string(index=False)

    def analyze(self, query, live_context=""):
        """
        Analyzes the portfolio based on the user query.
        live_context: String containing live market data (provided by LiveDataAgent via Orchestrator)
        """
        system_prompt = f"""
        You are a Portfolio Analytics Expert. Your role is to provide deep insights into the user's portfolio performance, composition, and behavior.
        
        Data Context:
        - Holdings (Net Quantity & Avg Price):
        {self.holdings_str}
        
        - Recent Transaction History (Last 50 trades):
        {self.history_str}
        
        - Live Market Context (if available):
        {live_context}
        
        Guidelines:
        - Analyze PATTERNS in the trading behavior (e.g., "You seem to be accumulating stocks in the Tech sector").
        - Explain WHY the portfolio might be up or down based on the holdings.
        - If asked about "Profitability", use the provided live context or calculate unrealized P&L if possible.
        - Be concise, professional, and data-driven.
        - Do NOT perform complex math yourself (like XIRR), assume the Math Agent handles that. Focus on qualitative analysis.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
        
        try:
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.2
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Error analyzing portfolio: {e}"
