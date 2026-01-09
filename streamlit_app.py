import streamlit as st
import sys, os
# Add portfolio-data and agents directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "portfolio-data"))
sys.path.append(os.path.join(os.path.dirname(__file__), "agents"))

from agents.orchestrator import Orchestrator
from dotenv import load_dotenv

# Set page configuration
st.set_page_config(
    page_title="Stock Analyst Multi-Agent",
    page_icon="🤖",
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

# Initialize Orchestrator
@st.cache_resource
def get_orchestrator():
    return Orchestrator()

try:
    orchestrator = get_orchestrator()
    # Get stats for sidebar
    stats = orchestrator.get_portfolio_stats()
except Exception as e:
    st.error(f"Error initializing agents: {e}")
    st.stop()

# Sidebar - Portfolio Metrics
st.sidebar.title("🚀 Multi-Agent Dashboard")
st.sidebar.divider()

st.sidebar.metric("Invested Value", f"₹{stats['current_value']:,.2f}")
st.sidebar.metric("Live Market Value", f"₹{stats.get('market_value', 0):,.2f}")

# Calculate Unrealized P&L Delta color
pnl = stats.get('unrealized_pnl', 0)
pnl_pct = stats.get('pnl_percentage', 0)
st.sidebar.metric("Unrealized P&L", f"₹{pnl:,.2f}", delta=f"{pnl_pct:,.2f}%")

st.sidebar.metric("Total Orders", f"{stats['total_orders']}")

# 6-Month Growth with color
growth = stats['six_month_growth']
if isinstance(growth, (int, float)):
    st.sidebar.metric("6-Month Growth (Historical)", f"{growth:,.2f}%")
else:
    st.sidebar.info(growth)

st.sidebar.divider()
st.sidebar.info("🤖 **Active Agents:**\n- Orchestrator\n- Math Agent\n- Analytics Agent\n- Live Data Agent\n- Prediction Agent\n- Education Agent")

# Main Chat Interface
st.title("🤖 Multi-Agent Stock Analyst")
st.caption("Ask anything! The Orchestrator will route your query to the best expert agent.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am the **Orchestrator**. I have a team of agents ready to help you with Math, Analytics, Live Data, Predictions, and Education. How can we assist?"}
    ]

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Ask about XIRR, Predictions, or Analysis..."):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("Orchestrator is routing your query..."):
        try:
            # Generate response from orchestrator
            # Note: route_query returns a string directly
            response = orchestrator.route_query(prompt)
            
            # Display assistant response in chat message container
            with st.chat_message("assistant"):
                st.markdown(response)
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
        except Exception as e:
            st.error(f"An error occurred: {e}")

# Footer
st.markdown("---")
st.caption("Powered by Multi-Agent Architecture • Groq • Streamlit")
