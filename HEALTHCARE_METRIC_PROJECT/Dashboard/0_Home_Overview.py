import streamlit as st
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Healthcare Metrics Dashboard", layout="wide")

session = get_active_session()

st.title("🏥 Healthcare Metrics Dashboard")
st.markdown("""
    A unified view of facility staffing and operational performance across all locations to evaluate how direct-care 
    hours, workload, and patient volumes impact care delivery and efficiency.

    The dashboard provides clear visibility into nurse-to-patient ratios (HPRD) and monthly working hours by hospital 
    and state. It also tracks resident census trends, highlights facilities with high patient throughput, and pinpoints 
    where staffing levels fall short relative to patient load.
""")

# --- GLOBAL SIDEBAR FILTER STORED IN SESSION STATE ---
st.sidebar.header("Global Filters")

state_query = "SELECT DISTINCT STATE FROM HEALTHCARE_DB.GOLD.GOLD_MART_STAFFING_METRICS WHERE STATE IS NOT NULL ORDER BY STATE;"
states_df = session.sql(state_query).to_pandas()
state_list = states_df['STATE'].tolist()
default_idx = state_list.index('CA') if 'CA' in state_list else 0

# Store selected state in session state so pages can access it
if 'selected_state' not in st.session_state:
    st.session_state['selected_state'] = state_list[default_idx]

st.session_state['selected_state'] = st.sidebar.selectbox(
    "Select State:", 
    state_list, 
    index=state_list.index(st.session_state['selected_state']) if st.session_state['selected_state'] in state_list else default_idx
)

st.success(f"Currently viewing data for state: **{st.session_state['selected_state']}**. Use the sidebar navigation above to switch between analytical modules.")