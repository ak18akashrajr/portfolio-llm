from groq import Groq
import os
import pandas as pd
import json
from dotenv import load_dotenv

# Import sub-agents
from agents.math_agent import MathAgent
from agents.analytics_agent import AnalyticsAgent
from agents.live_data_agent import LiveDataAgent
from agents.prediction_agent import PredictionAgent
from agents.education_agent import EducationAgent
from data_processor import process_stock_data

load_dotenv()

class Orchestrator:
    def __init__(self, model_name="openai/gpt-oss-120b"):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.client = Groq(api_key=self.api_key)
        self.model_name = model_name
        
        # Load data once
        # Using absolute path logic similar to before
        file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "portfolio-data", "stock_order_history.xlsx")
        self.data_processor_result = process_stock_data(file_path) # Returns tuple
        
        # Wrap result in a simple object for agents to consume consistently
        class DataContext:
            def __init__(self, data_tuple):
                self.df = data_tuple[0]
                self.portfolio = data_tuple[1]
                self.holdings = data_tuple[2]
        
        self.data_context = DataContext(self.data_processor_result)
        
        # Initialize Agents
        self.math_agent = MathAgent(self.data_context)
        self.analytics_agent = AnalyticsAgent(self.data_context)
        self.live_agent = LiveDataAgent()
        self.prediction_agent = PredictionAgent(self.data_context)
        self.edu_agent = EducationAgent()
        
    def _classify_intent(self, query):
        """
        Uses LLM to classify the user query into one of the agent categories.
        Categories: MATH, ANALYTICS, LIVE, PREDICT, EDU, CHAT (General)
        """
        system_prompt = """
        You are an Intent Classifier. Classify the user's finance query into exactly one of these categories:
        
        - MATH: Questions about XIRR, CAGR, Averages, Totals, precise calculations.
        - LIVE: Questions about CURRENT prices, real-time value, or today's market status.
        - PREDICT: Questions asking for forecasts, future trends, or "what will happen".
        - EDU: Questions asking for definitions or explanations of terms (e.g., "What is P/E?").
        - ANALYTICS: Questions asking for insights, reasons, portfolio composition, or general analysis of the provided data.
        - CHAT: Simple greetings, irrelevant queries, or questions about who you are.
        
        Output ONLY the category name. Do not explain.
        """
        
        try:
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0,
                max_tokens=10
            )
            intent = completion.choices[0].message.content.strip().upper()
            # Clean up potentially messy output (e.g. "CATEGORY: MATH")
            if "MATH" in intent: intent = "MATH"
            elif "LIVE" in intent: intent = "LIVE"
            elif "PREDICT" in intent: intent = "PREDICT"
            elif "EDU" in intent: intent = "EDU"
            elif "ANALYTICS" in intent: intent = "ANALYTICS"
            elif "CHAT" in intent: intent = "CHAT"
            
            return intent
        except Exception as e:
            print(f"Intent Classification Error: {e}")
            return "ANALYTICS" # Default fallback

    def route_query(self, user_query):
        intent = self._classify_intent(user_query)
        print(f"DEBUG: Routing '{user_query}' to {intent}")
        
        try:
            if intent == "MATH":
                if "xirr" in user_query.lower():
                    # Check if we can get current value from live agent
                    curr_val, _ = self.live_agent.calculate_current_valuation(self.data_context.holdings)
                    if curr_val > 0:
                        xirr_val = self.math_agent.compute_xirr_with_terminal_value(curr_val)
                        return f"**XIRR Calculation**\n\nBased on your realized cash flows and a current portfolio value of ₹{curr_val:,.2f}:\n\nYour Portfolio XIRR is **{xirr_val:.2f}%**."
                    else:
                        return self.math_agent.calculate_xirr() # Will throw specific message
                else:
                    # Provide stats summary
                    # For simple math queries like averages which aren't yet implemented in MathAgent specific methods
                    # The user might be asking "What is average price of X?"
                    # Since Analytics agent has LLM, it's better suited for "English" math questions unless we implement specific NLP parsing in Math Agent.
                    # Let's fallback "soft math" to Analytics, or implement flexible math.
                    # For now, let's let Analytics handle specific queries if Math Agent is too rigid.
                    # BUT, if we returned MATH, we must answer.
                    return f"**Math Agent**: \n{self.math_agent.get_summary_stats()}"

            elif intent == "LIVE":
                # User wants live data
                val, details = self.live_agent.calculate_current_valuation(self.data_context.holdings)
                if not details:
                     return "Could not fetch live data at the moment."
                
                response = f"**Live Market Update**\n\n**Total Portfolio Value:** ₹{val:,.2f}\n\n"
                for sym, info in details.items():
                    response += f"- **{sym}**: ₹{info['price']:.2f} (Qty: {info['qty']}) = ₹{info['value']:,.2f}\n"
                return response

            elif intent == "PREDICT":
                return self.prediction_agent.predict_portfolio_trend()

            elif intent == "EDU":
                return self.edu_agent.explain(user_query)
            
            elif intent == "ANALYTICS":
                # Enrich with live context if possible
                curr_val, _ = self.live_agent.calculate_current_valuation(self.data_context.holdings)
                live_context = f"Current Live Portfolio Value: ₹{curr_val:,.2f}"
                return self.analytics_agent.analyze(user_query, live_context)
                
            elif intent == "CHAT":
                # Fallback / CHAT
                return "Hello! I am your Portfolio Orchestrator. You can ask me about:\n- **Math**: XIRR, Averages\n- **Live**: Current prices\n- **Analysis**: Performance insights\n- **Predictions**: Future trends\n- **Education**: Financial terms"
            
            else:
                 # If classification failed to match key categories but returned something else, default to Analytics
                 print(f"DEBUG: Unknown intent '{intent}', defaulting to ANALYTICS")
                 curr_val, _ = self.live_agent.calculate_current_valuation(self.data_context.holdings)
                 live_context = f"Current Live Portfolio Value: ₹{curr_val:,.2f}"
                 return self.analytics_agent.analyze(user_query, live_context)
                 
        except Exception as e:
            return f"An error occurred while processing your request: {e}"
                
        except Exception as e:
            return f"An error occurred while processing your request: {e}"

    def get_portfolio_stats(self):
        """
        Helper to return stats for the sidebar (similar to old Agent)
        """
        # Re-use logic from Analytics or Math agent ideally
        # For compatibility with streamlit_app sidebar:
        
        # 1. Basic Stats
        current_invested = self.data_context.portfolio['Cumulative_Investment'].iloc[-1]
        total_orders = len(self.data_context.df)
        
        # 2. Live Stats
        curr_market_val, _ = self.live_agent.calculate_current_valuation(self.data_context.holdings)
        
        # 3. Growth
        unrealized_pnl = curr_market_val - current_invested
        pnl_pct = (unrealized_pnl / current_invested * 100) if current_invested != 0 else 0
        
        # 4. 6 Month Growth (Historical)
        latest_date = self.data_context.portfolio.index.max()
        six_months_ago = latest_date - pd.DateOffset(months=6)
        if six_months_ago in self.data_context.portfolio.index:
            val_now = self.data_context.portfolio.loc[latest_date, 'Cumulative_Investment']
            val_then = self.data_context.portfolio.loc[six_months_ago, 'Cumulative_Investment']
            six_month_growth = ((val_now - val_then) / val_then) * 100 if val_then != 0 else 0
        else:
            six_month_growth = "Insufficient data"

        return {
            "current_value": current_invested,
            "market_value": curr_market_val,
            "unrealized_pnl": unrealized_pnl,
            "pnl_percentage": pnl_pct,
            "total_orders": total_orders,
            "six_month_growth": six_month_growth
        }
