import streamlit as st
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Staffing & Nurse Hours", layout="wide")
session = get_active_session()

selected_state = st.session_state.get('selected_state', 'CA')

st.title("📊 Staffing & Nurse Hours")
st.markdown(f"Analyzing nurse-to-patient ratios and monthly direct care hours for **{selected_state}**.")
st.sidebar.info(f"Active State: {selected_state}")

st.subheader("Average Nurse-to-Patient Ratios (Hours Per Resident Day)")
st.markdown("Evaluates average daily care hours allocated per resident by department/role.")

query_hprd = f"""
    SELECT 
        STATE,
        PROVIDER_ID,
        MASTER_PROVIDER_NAME AS HOSPITAL,
        AVG(MASTER_RN_HPRD) AS AVG_RN_HPRD,
        AVG(CMS_LPN_HPRD) AS AVG_LPN_HPRD,
        AVG(CMS_AIDE_HPRD) AS AVG_CNA_HPRD
    FROM HEALTHCARE_DB.GOLD.GOLD_MART_STAFFING_METRICS
    WHERE STATE = '{selected_state}'
    GROUP BY STATE, PROVIDER_ID, MASTER_PROVIDER_NAME
    ORDER BY HOSPITAL;
"""

df_hprd = session.sql(query_hprd).to_pandas()

if not df_hprd.empty:
    col1, col2, col3 = st.columns(3)
    col1.metric("Avg RN HPRD (State)", f"{df_hprd['AVG_RN_HPRD'].mean():.2f}")
    col2.metric("Avg LPN HPRD (State)", f"{df_hprd['AVG_LPN_HPRD'].mean():.2f}")
    col3.metric("Avg CNA HPRD (State)", f"{df_hprd['AVG_CNA_HPRD'].mean():.2f}")
    
    st.markdown("---")
    chart_data = df_hprd.set_index('HOSPITAL')[['AVG_RN_HPRD', 'AVG_LPN_HPRD', 'AVG_CNA_HPRD']]
    st.bar_chart(chart_data.head(20))
    st.caption("Displaying top 20 facilities in selected state.")
    st.dataframe(df_hprd, use_container_width=True)
else:
    st.warning(f"No HPRD records found for state: {selected_state}")

st.markdown("---")

st.subheader("Total Hours Worked by Nurses per Hospital & Month")
st.markdown("Tracks aggregated monthly direct care hours by nursing category.")

query_monthly = f"""
    SELECT 
        STATE,
        COUNTY_NAME,
        MASTER_PROVIDER_NAME AS HOSPITAL,
        DATE_TRUNC('month', WORK_DATE) AS WORK_MONTH,
        SUM(RN_HOURS) AS TOTAL_RN_HOURS,
        SUM(LPN_HOURS) AS TOTAL_LPN_HOURS,
        SUM(CNA_HOURS) AS TOTAL_CNA_HOURS,
        SUM(TOTAL_DIRECT_CARE_HOURS) AS TOTAL_NURSE_HOURS
    FROM HEALTHCARE_DB.GOLD.GOLD_MART_STAFFING_METRICS
    WHERE WORK_DATE IS NOT NULL AND STATE = '{selected_state}'
    GROUP BY STATE, COUNTY_NAME, MASTER_PROVIDER_NAME, DATE_TRUNC('month', WORK_DATE)
    ORDER BY HOSPITAL, WORK_MONTH;
"""

df_monthly = session.sql(query_monthly).to_pandas()

if not df_monthly.empty:
    hospitals = df_monthly['HOSPITAL'].unique()
    selected_hospital = st.selectbox("Select Hospital for Trend Analysis:", hospitals)
    
    hospital_filtered = df_monthly[df_monthly['HOSPITAL'] == selected_hospital]
    
    st.markdown(f"**Monthly Direct Care Hours Trend: {selected_hospital}**")
    trend_chart_data = hospital_filtered.set_index('WORK_MONTH')[['TOTAL_RN_HOURS', 'TOTAL_LPN_HOURS', 'TOTAL_CNA_HOURS']]
    st.line_chart(trend_chart_data)
    
    st.dataframe(df_monthly, use_container_width=True)
else:
    st.warning(f"No monthly hour records found for state: {selected_state}")
    
st.markdown("---")

# Data Constraints Note
st.subheader("⚠️ Data Constraints: Individual vs. Facility-Level Metrics")
st.markdown("Certain individual-level operational metrics cannot be directly visualized from current CMS Payroll-Based Journal (PBJ) datasets:")

col_a, col_b = st.columns(2)
with col_a:
    st.markdown("#### 🚫 Percentage of Nurses Working Overtime")
    st.info("**Why it's unavailable:** CMS PBJ data provides facility-level daily aggregates rather than individual employee time-cards.")
with col_b:
    st.markdown("#### 🚫 Number of Shifts per Nurse (Avg/Median)")
    st.info("**Why it's unavailable:** Individual staff rosters and shift-level logs are stripped during aggregation into daily facility summaries.")