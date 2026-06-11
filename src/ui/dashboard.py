import streamlit as st
import pandas as pd
import numpy as np
import requests
import time
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Predictive Maintenance Dashboard", layout="wide")

API_URL = "http://localhost:8000"

st.title("🏭 Predictive Maintenance Dashboard")
st.markdown("Real-time monitoring of equipment health and Remaining Useful Life (RUL).")

# Initialize session state for mock history if we can't get it from the API
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=["timestamp", "equipment_id", "type", "rul", "status", "confidence"])

def fetch_health():
    try:
        res = requests.get(f"{API_URL}/")
        return res.status_code == 200
    except:
        return False

# Sidebar
st.sidebar.header("System Status")
api_healthy = fetch_health()
if api_healthy:
    st.sidebar.success("API Connected")
else:
    st.sidebar.error("API Disconnected. Is the FastAPI server running?")

# Create an auto-refresh toggle
refresh_rate = st.sidebar.slider("Refresh Rate (seconds)", 1, 10, 2)
auto_refresh = st.sidebar.checkbox("Auto-refresh Data", value=True)

# Generate mock data for the dashboard to simulate real-time influx
def simulate_data_fetch():
    equipment_ids = ["bearing_01", "motor_05", "pump_12", "gearbox_03"]
    new_data = []
    for eq in equipment_ids:
        rul = np.random.uniform(50, 500)
        status = "critical" if rul < 100 else ("warning" if rul < 250 else "healthy")
        new_data.append({
            "timestamp": datetime.now(),
            "equipment_id": eq,
            "type": eq.split("_")[0],
            "rul": rul,
            "status": status,
            "confidence": np.random.uniform(0.85, 0.99)
        })
    return pd.DataFrame(new_data)

# Update history
new_df = simulate_data_fetch()
st.session_state.history = pd.concat([st.session_state.history, new_df]).tail(200)  # keep last 200 rows
current_status = new_df.copy()

# Layout: KPIs
col1, col2, col3, col4 = st.columns(4)
healthy_count = len(current_status[current_status["status"] == "healthy"])
warning_count = len(current_status[current_status["status"] == "warning"])
critical_count = len(current_status[current_status["status"] == "critical"])

col1.metric("Total Monitored", len(current_status))
col2.metric("Healthy", healthy_count)
col3.metric("Warnings", warning_count)
col4.metric("Critical", critical_count)

st.markdown("---")

# Layout: Charts
row1_col1, row1_col2 = st.columns([2, 1])

with row1_col1:
    st.subheader("Equipment RUL Overview")
    # Bar chart of current RUL
    fig = px.bar(
        current_status, 
        x="equipment_id", 
        y="rul", 
        color="status",
        color_discrete_map={"healthy": "green", "warning": "orange", "critical": "red"},
        title="Current Remaining Useful Life (Hours)"
    )
    st.plotly_chart(fig, use_container_width=True)

with row1_col2:
    st.subheader("Status Distribution")
    fig2 = px.pie(
        current_status, 
        names="status", 
        color="status",
        color_discrete_map={"healthy": "green", "warning": "orange", "critical": "red"},
        hole=0.4
    )
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# Live Data Table
st.subheader("Live Equipment Status")
st.dataframe(
    current_status[["equipment_id", "type", "rul", "status", "confidence"]].sort_values("rul"),
    use_container_width=True
)

if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()
