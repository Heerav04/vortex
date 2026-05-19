import streamlit as st
import sqlite3
import pandas as pd
import json
import plotly.express as px
from pathlib import Path
import os

# Ensure we can find the DB relative to the app
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "telemetry.sqlite3"

st.set_page_config(page_title="Vortex Analytics", page_icon="📈", layout="wide")
st.title("Vortex AI OS - Telemetry Dashboard")
st.markdown("*A data-science view of Assistant routing efficiency, latency, and modular migration progress.*")

if not DB_PATH.exists():
    st.warning(f"Telemetry database not found at {DB_PATH}. Start Vortex and execute some commands first!")
    st.stop()

@st.cache_data(ttl=5) # Refresh data every 5 seconds
def load_data():
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query("SELECT * FROM events", conn)
    
    if df.empty:
        return df, df

    # Parse JSON payloads
    df['payload_dict'] = df['payload'].apply(lambda x: json.loads(x) if pd.notnull(x) else {})
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Split into interactions and tool executions
    interactions = df[df['event_type'] == 'interaction'].copy()
    tools = df[df['event_type'] == 'tool_executed'].copy()
    
    if not tools.empty:
        tools['tool_namespace'] = tools['payload_dict'].apply(lambda x: x.get('tool', 'unknown'))
        tools['tool_action'] = tools['payload_dict'].apply(lambda x: x.get('action', 'unknown'))
        tools['success'] = tools['payload_dict'].apply(lambda x: x.get('success', False))
        
        # Determine Modular vs Legacy based on the actions we migrated
        # We know time, open_app, and set_volume are modular
        modular_actions = ['time', 'open_app', 'set_volume']
        tools['architecture'] = tools['tool_action'].apply(
            lambda x: 'Modular (BaseTool)' if x in modular_actions else 'Legacy (Function)'
        )
        
    return interactions, tools

interactions, tools = load_data()

if tools.empty:
    st.info("No tool telemetry recorded yet. Ask Vortex some questions to populate the dashboard!")
    st.stop()

# Key Metrics
st.markdown("### System Health & Performance")
col1, col2, col3, col4 = st.columns(4)

success_rate = (tools['success'].sum() / len(tools)) * 100 if len(tools) > 0 else 0
avg_latency = tools['latency_ms'].mean() if len(tools) > 0 else 0
total_queries = len(interactions)
modular_percentage = (len(tools[tools['architecture'] == 'Modular (BaseTool)']) / len(tools)) * 100 if len(tools) > 0 else 0

col1.metric("Overall Success Rate", f"{success_rate:.1f}%")
col2.metric("Avg Tool Latency", f"{avg_latency:.1f} ms")
col3.metric("Total User Queries", f"{total_queries}")
col4.metric("Modular Adoption", f"{modular_percentage:.1f}%")

st.markdown("---")

col_a, col_b = st.columns(2)

with col_a:
    st.markdown("### Tool Routing Split (Modular vs Legacy)")
    fig_arch = px.pie(tools, names='architecture', color='architecture', 
                     color_discrete_map={'Modular (BaseTool)':'#10b981', 'Legacy (Function)':'#f59e0b'},
                     hole=0.4)
    st.plotly_chart(fig_arch, use_container_width=True)

with col_b:
    st.markdown("### Tool Execution Latency (ms)")
    fig_lat = px.box(tools, x='tool_namespace', y='latency_ms', color='architecture',
                    color_discrete_map={'Modular (BaseTool)':'#10b981', 'Legacy (Function)':'#f59e0b'})
    st.plotly_chart(fig_lat, use_container_width=True)

st.markdown("---")
st.markdown("### Assistant Usage Trends")
tool_counts = tools['tool_action'].value_counts().reset_index()
tool_counts.columns = ['Tool Action', 'Executions']
fig_bar = px.bar(tool_counts, x='Tool Action', y='Executions', color='Executions', color_continuous_scale='Blues')
st.plotly_chart(fig_bar, use_container_width=True)
