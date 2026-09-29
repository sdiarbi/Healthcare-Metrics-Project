import streamlit as st
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Quality Metrics & Outcomes", layout="wide")
session = get_active_session()

selected_state = st.session_state.get('selected_state', 'CA')

st.title("⭐ Quality Metrics & Clinical Outcomes")
st.markdown(f"Evaluating patient satisfaction, length of stay, readmission rates, and their correlation with staffing levels for **{selected_state}**.")
st.sidebar.info(f"Active State: {selected_state}")

# ----------------------------------------------------
# 1. Patient Satisfaction Scores
# ----------------------------------------------------
st.markdown("### 1️⃣ Patient Satisfaction Scores by Hospital")
st.markdown("Measures HCAHPS survey results (e.g., overall hospital rating, nurse communication scores).")

# Note: Assumes a quality join or separate table. If data is pending, display constraint notice.
st.info(
    "**Data Source Note:** Patient satisfaction scores (HCAHPS) are sourced from CMS Hospital Compare datasets. "
    "To display this live, ensure your Snowflake database includes a joined quality mart containing provider-level survey averages."
)

# ----------------------------------------------------
# 2. Average Length of Stay (ALOS)
# ----------------------------------------------------
st.markdown("### 2️⃣ Average Length of Stay (ALOS) by Department & State")
st.markdown("Tracks inpatient duration patterns across facility departments.")

query_alos = f"""
    SELECT 
        COUNTY_NAME,
        MASTER_PROVIDER_NAME AS HOSPITAL_NAME,
        ROUND(AVG(RESIDENT_CENSUS), 2) AS AVG_CENSUS
    FROM HEALTHCARE_DB.GOLD.GOLD_MART_STAFFING_METRICS
    WHERE STATE = '{selected_state}'
    GROUP BY COUNTY_NAME, MASTER_PROVIDER_NAME
    ORDER BY AVG_CENSUS DESC;
"""
# Placeholder metric/table until ALOS admission/discharge timestamps are integrated
df_alos = session.sql(query_alos).to_pandas()
st.dataframe(df_alos.head(10), use_container_width=True)
st.caption("Showing facility census baseline while awaiting admission/discharge timestamp tables for exact ALOS calculation.")

st.markdown("---")

# ----------------------------------------------------
# 3. 30-Day Readmission Rates
# ----------------------------------------------------
st.markdown("### 3️⃣ Readmission Rates Within 30 Days")
st.markdown("Analyzed by hospital, state, and primary diagnosis category under the Hospital Readmissions Reduction Program.")

col_q1, col_q2 = st.columns(2)
with col_q1:
    st.markdown("#### 🏥 Facility Readmission Benchmarks")
    st.info("Tracks unplanned 30-day readmissions relative to national and state risk-adjusted standards.")
with col_q2:
    st.markdown("#### 📋 Breakdown by Diagnosis Category")
    st.info("Filters readmission trends across high-volume clinical categories (e.g., Heart Failure, Pneumonia, COPD).")

st.markdown("---")

# ----------------------------------------------------
# 4. Patient-to-Nurse Complaint Ratio
# ----------------------------------------------------
st.markdown("### ⚠️ 4️⃣ Patient-to-Nurse Complaint Ratio")
st.markdown("Examines formal grievances and staffing-related complaints relative to direct-care hours.")

st.warning(
    "**Data Availability Constraint:** Patient-to-nurse complaint ratios are typically managed through state health department "
    "grievance logs or internal facility incident reporting systems rather than standard public CMS PBJ datasets. "
    "Integration requires secure ingestion of hospital incident management databases."
)

st.markdown("---")

# ----------------------------------------------------
# 5. Correlation: Staffing Levels vs. Readmission Rates
# ----------------------------------------------------
st.markdown("### 📈 5️⃣ Correlation: Nurse Staffing Levels vs. Readmission Rates")
st.markdown("Evaluates whether higher direct-care hours per resident day (HPRD) correlate with lower 30-day readmission rates.")

query_correlation_proxy = f"""
    SELECT 
        MASTER_PROVIDER_NAME AS HOSPITAL_NAME,
        ROUND(AVG(MASTER_TOTAL_NURSING_HPRD), 2) AS AVG_TOTAL_HPRD,
        ROUND(AVG(RESIDENT_CENSUS), 2) AS AVG_RESIDENT_CENSUS
    FROM HEALTHCARE_DB.GOLD.GOLD_MART_STAFFING_METRICS
    WHERE STATE = '{selected_state}' AND MASTER_TOTAL_NURSING_HPRD > 0
    GROUP BY MASTER_PROVIDER_NAME
    ORDER BY AVG_TOTAL_HPRD DESC;
"""
df_corr = session.sql(query_correlation_proxy).to_pandas()

if not df_corr.empty:
    st.markdown("**Staffing Intensity (HPRD) Scatter / Bar Distribution**")
    st.bar_chart(df_corr.set_index('HOSPITAL_NAME')['AVG_TOTAL_HPRD'].head(15))
    st.caption("Plotting facility HPRD levels. Once clinical readmission metrics are joined, this section will render direct scatter-plot correlations.")
    st.dataframe(df_corr, use_container_width=True)