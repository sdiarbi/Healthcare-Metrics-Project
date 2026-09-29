import streamlit as st
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Operational Metrics & Workforce Dynamics", layout="wide")
session = get_active_session()

selected_state = st.session_state.get('selected_state', 'CA')

st.title("⏱️ Operational Metrics & Workforce Dynamics")
st.markdown(f"Analyzing shift utilization, peak staffing windows, permanent vs. contract labor mix, and attrition trends for **{selected_state}**.")
st.sidebar.info(f"Active State: {selected_state}")

# ----------------------------------------------------
# 1. Shift Utilization Rates by Time of Day
# ----------------------------------------------------
st.markdown("### 1️⃣ Shift Utilization Rates by Time of Day")
st.markdown("Evaluates staffing distribution across morning, afternoon, and night shifts.")

st.info(
    "**Data Source Note:** CMS PBJ reports daily aggregated hours per staff type. True time-of-day shift utilization (morning vs. night) "
    "requires granular shift-start timestamp logs or electronic timekeeping records."
)

# ----------------------------------------------------
# 2. Peak Staffing Hours by Hospital and Department
# ----------------------------------------------------
st.markdown("### 2️⃣ Peak Staffing Hours by Hospital & Department")
st.markdown("Identifies peak workload and maximum direct-care coverage windows across facilities.")

query_peak_proxy = f"""
    SELECT 
        COUNTY_NAME,
        MASTER_PROVIDER_NAME AS HOSPITAL_NAME,
        ROUND(AVG(RESIDENT_CENSUS), 2) AS AVG_CENSUS,
        ROUND(AVG(TOTAL_DIRECT_CARE_HOURS), 2) AS AVG_DAILY_HOURS
    FROM HEALTHCARE_DB.GOLD.GOLD_MART_STAFFING_METRICS
    WHERE STATE = '{selected_state}'
    GROUP BY COUNTY_NAME, MASTER_PROVIDER_NAME
    ORDER BY AVG_DAILY_HOURS DESC;
"""
df_peak = session.sql(query_peak_proxy).to_pandas()
if not df_peak.empty:
    st.dataframe(df_peak.head(10), use_container_width=True)
    st.caption("Displaying daily direct-care volume baselines while hourly schedule logging is being integrated.")

st.markdown("---")

# ----------------------------------------------------
# 3. Ratio of Permanent Staff to Temporary/Contract Staff
# ----------------------------------------------------
st.markdown("### 3️⃣ Ratio of Permanent Staff to Temporary/Contract Staff")
st.markdown("Tracks reliance on agency, traveling, or per-diem nurses versus full-time permanent staff.")

col_op1, col_op2 = st.columns(2)
with col_op1:
    st.markdown("#### 👤 Permanent Staff Hours")
    st.info("Measures core internal workforce utilization and baseline care delivery stability.")
with col_op2:
    st.markdown("#### 🤝 Contract / Agency Staff Hours")
    st.info("Monitors supplemental labor utilization, which heavily impacts operating overhead and cost structures.")

st.markdown("---")

# ----------------------------------------------------
# 4. Trend Analysis of Nurse Attrition Rates
# ----------------------------------------------------
st.markdown("### 📉 4️⃣ Trend Analysis of Nurse Attrition Rates")
st.markdown("Tracks staff turnover velocity, tenure distribution, and retention indicators.")

st.warning(
    "**Data Availability Constraint:** Nurse attrition and turnover tracking require longitudinal HR personnel files "
    "(hire and termination dates with employee IDs), which fall outside the scope of public CMS daily staffing registries."
)