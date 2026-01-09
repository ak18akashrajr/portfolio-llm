from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

class EducationAgent:
    def __init__(self, model_name="openai/gpt-oss-120b"):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model_name = model_name
        self.system_prompt = """
        You are a financial educator. Your goal is to explain complex stock market concepts in simple, easy-to-understand terms.
        
        Guidelines:
        - Keep explanations concise (under 3 paragraphs).
        - Use analogies where possible.
        - Define key terms like XIRR, CAGR, P/E Ratio, Beta, Alpha, Dividend Yield, etc. when asked.
        - Do NOT give financial advice (buy/sell). Only explain the concepts.
        """

    def explain(self, query):
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Explain this concept: {query}"}
        ]
        
        try:
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.3
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Sorry, I couldn't generate an explanation at this time. Error: {e}"
