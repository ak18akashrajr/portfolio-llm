import streamlit as st
import sys, os
# Add portfolio-data directory to Python path for module imports
sys.path.append(os.path.join(os.path.dirname(__file__), "portfolio-data"))
from agent import StockAgent
from dotenv import load_dotenv

# Set page configuration
st.set_page_config(
    page_title="Stock Analyst LLM",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load environment variables
load_dotenv()

# Custom CSS for premium look
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
        color: #ffffff;
    }
    .stMetric {
        background-color: #1e2130;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #30363d;
    }
    .stChatMessage {
        border-radius: 15px;
        margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize StockAgent
@st.cache_resource
def get_agent():
    return StockAgent()

try:
    agent = get_agent()
    stats = agent._get_portfolio_stats()
except Exception as e:
    st.error(f"Error initializing agent: {e}")
    st.stop()

# Sidebar - Portfolio Metrics
st.sidebar.title("🚀 Portfolio Dashboard")
st.sidebar.divider()

st.sidebar.metric("Current Portfolio Value", f"₹{stats['current_value']:,.2f}")
st.sidebar.metric("Total Orders", f"{stats['total_orders']}")

# 6-Month Growth with color
growth = stats['six_month_growth']
if isinstance(growth, (int, float)):
    st.sidebar.metric("6-Month Growth", f"{growth:,.2f}%", delta=f"{growth:,.2f}%")
else:
    st.sidebar.info(growth)

st.sidebar.divider()

# QoQ Growth Chart in Sidebar or Main


# Main Chat Interface
st.title("👨‍🔬 Stock Analyst LLM Agent")
st.caption("Ask queries based on your stock order history (e.g., QoQ growth, specific holdings, performance)")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I've analyzed your `stock_order_history.xlsx`. How can I help you today?"}
    ]

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Ask about your portfolio..."):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("Analyzing data..."):
        try:
            # Generate response from agent
            response = agent.chat(prompt)
            # Display assistant response in chat message container
            with st.chat_message("assistant"):
                st.markdown(response)
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
        except Exception as e:
            st.error(f"An error occurred: {e}")

# Footer
st.markdown("---")
st.caption("Developed with ❤️ using Groq & Streamlit")
