import streamlit as st
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Facility Metrics & Occupancy", layout="wide")
session = get_active_session()

selected_state = st.session_state.get('selected_state', 'CA')

st.title("🏢 Facility Metrics & Occupancy")
st.markdown(f"Detailed operational performance and occupancy metrics for **{selected_state}**.")
st.sidebar.info(f"Active State: {selected_state}")

# 1. Occupancy Trend
st.markdown("### 1️⃣ Hospital Occupancy Rate Trends (Monthly & Quarterly)")
query_occ_trend = f"""
    SELECT 
        MASTER_PROVIDER_NAME AS HOSPITAL_NAME,
        DATE_TRUNC('month', WORK_DATE) AS WORK_MONTH,
        CALENDAR_QUARTER,
        ROUND(AVG(RESIDENT_CENSUS), 2) AS AVG_DAILY_CENSUS,
        MAX(RESIDENT_CENSUS) AS PEAK_DAILY_CENSUS
    FROM HEALTHCARE_DB.GOLD.GOLD_MART_STAFFING_METRICS
    WHERE STATE = '{selected_state}' AND WORK_DATE IS NOT NULL
    GROUP BY MASTER_PROVIDER_NAME, DATE_TRUNC('month', WORK_DATE), CALENDAR_QUARTER
    ORDER BY HOSPITAL_NAME, WORK_MONTH;
"""
df_occ_trend = session.sql(query_occ_trend).to_pandas()

if not df_occ_trend.empty:
    hosp_list_occ = df_occ_trend['HOSPITAL_NAME'].unique()
    selected_occ_hosp = st.selectbox("Select Hospital for Occupancy Trend:", hosp_list_occ, key="occ_hosp")
    
    filtered_occ = df_occ_trend[df_occ_trend['HOSPITAL_NAME'] == selected_occ_hosp]
    st.line_chart(filtered_occ.set_index('WORK_MONTH')[['AVG_DAILY_CENSUS', 'PEAK_DAILY_CENSUS']])

st.markdown("---")

# 2. Bed Utilization
st.markdown("### 2️⃣ Bed Utilization & Departmental Workload")
query_utilization = f"""
    SELECT 
        COUNTY_NAME,
        MASTER_PROVIDER_NAME AS HOSPITAL_NAME,
        ROUND(AVG(RESIDENT_CENSUS), 2) AS AVG_CENSUS,
        ROUND(AVG(RN_HOURS), 1) AS AVG_RN_HOURS,
        ROUND(AVG(LPN_HOURS), 1) AS AVG_LPN_HOURS,
        ROUND(AVG(CNA_HOURS), 1) AS AVG_CNA_HOURS
    FROM HEALTHCARE_DB.GOLD.GOLD_MART_STAFFING_METRICS
    WHERE STATE = '{selected_state}'
    GROUP BY COUNTY_NAME, MASTER_PROVIDER_NAME
    ORDER BY AVG_CENSUS DESC;
"""
df_utilization = session.sql(query_utilization).to_pandas()
st.dataframe(df_utilization, use_container_width=True)

st.markdown("---")

# 3. Staffing vs. Occupancy
st.markdown("### 3️⃣ Direct Comparison: Staffing Levels vs. Bed Occupancy Rates")
query_staff_vs_occ = f"""
    SELECT TOP 20
        MASTER_PROVIDER_NAME AS HOSPITAL_NAME,
        ROUND(AVG(RESIDENT_CENSUS), 2) AS AVG_OCCUPANCY_CENSUS,
        ROUND(AVG(TOTAL_DIRECT_CARE_HOURS), 2) AS AVG_DAILY_STAFF_HOURS,
        ROUND(AVG(MASTER_TOTAL_NURSING_HPRD), 2) AS ACTUAL_HPRD
    FROM HEALTHCARE_DB.GOLD.GOLD_MART_STAFFING_METRICS
    WHERE STATE = '{selected_state}' AND RESIDENT_CENSUS > 0
    GROUP BY MASTER_PROVIDER_NAME
    ORDER BY AVG_OCCUPANCY_CENSUS DESC;
"""
df_staff_vs_occ = session.sql(query_staff_vs_occ).to_pandas()
if not df_staff_vs_occ.empty:
    st.bar_chart(df_staff_vs_occ.set_index('HOSPITAL_NAME')[['AVG_OCCUPANCY_CENSUS', 'ACTUAL_HPRD']])
st.dataframe(df_staff_vs_occ, use_container_width=True)

st.markdown("---")

# 4. Throughput
st.markdown("### 4️⃣ Top 10 Hospitals by Highest Patient Throughput")
query_throughput = f"""
    SELECT TOP 10
        COUNTY_NAME,
        MASTER_PROVIDER_NAME AS HOSPITAL_NAME,
        ROUND(AVG(RESIDENT_CENSUS), 2) AS AVG_PATIENT_CENSUS,
        SUM(TOTAL_DIRECT_CARE_HOURS) AS TOTAL_ANNUAL_NURSE_HOURS
    FROM HEALTHCARE_DB.GOLD.GOLD_MART_STAFFING_METRICS
    WHERE STATE = '{selected_state}'
    GROUP BY COUNTY_NAME, MASTER_PROVIDER_NAME
    ORDER BY AVG_PATIENT_CENSUS DESC;
"""
df_throughput = session.sql(query_throughput).to_pandas()
if not df_throughput.empty:
    st.bar_chart(df_throughput.set_index('HOSPITAL_NAME')['AVG_PATIENT_CENSUS'])
st.dataframe(df_throughput, use_container_width=True)

st.markdown("---")

# 5. Lowest Staffing Variance
st.markdown("### 5️⃣ Facilities with Lowest Staffing Levels Compared to Patient Load")
query_variance = f"""
    SELECT TOP 15
        COUNTY_NAME,
        MASTER_PROVIDER_NAME AS HOSPITAL_NAME,
        ROUND(AVG(RESIDENT_CENSUS), 2) AS AVG_PATIENT_CENSUS,
        ROUND(AVG(MASTER_TOTAL_NURSING_HPRD), 2) AS FACILITY_AVG_HPRD,
        ROUND(AVG(STATE_AVG_NURSE_HPRD), 2) AS BENCHMARK_STATE_HPRD,
        ROUND(AVG(VARIANCE_FROM_STATE_AVG), 2) AS AVG_VARIANCE
    FROM HEALTHCARE_DB.GOLD.GOLD_MART_STAFFING_METRICS
    WHERE STATE = '{selected_state}' AND RESIDENT_CENSUS > 0
    GROUP BY COUNTY_NAME, MASTER_PROVIDER_NAME
    ORDER BY AVG_VARIANCE ASC;
"""
df_variance = session.sql(query_variance).to_pandas()
if not df_variance.empty:
    st.bar_chart(df_variance.set_index('HOSPITAL_NAME')['AVG_VARIANCE'])
st.dataframe(df_variance, use_container_width=True)