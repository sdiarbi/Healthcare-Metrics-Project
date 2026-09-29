import streamlit as st
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Cost & Financial Metrics", layout="wide")
session = get_active_session()

selected_state = st.session_state.get('selected_state', 'CA')

st.title("💰 Cost & Financial Analytics")
st.markdown(f"Evaluating nursing payroll costs, per-patient stay expenses, overtime financial impact, and revenue alignment for **{selected_state}**.")
st.sidebar.info(f"Active State: {selected_state}")

# ----------------------------------------------------
# 1. Total Payroll Costs for Nurses
# ----------------------------------------------------
st.markdown("### 1️⃣ Total Payroll Costs for Nurses by Hospital & State")
st.markdown("Tracks aggregated labor expenditures for RN, LPN, and CNA staffing.")

st.info(
    "**Data Source Note:** CMS PBJ data supplies hours worked but does not capture hourly wage rates or total compensation dollars. "
    "To display live payroll costs, join your staffing mart with CMS Cost Report (HCRIS) or internal payroll ledger tables."
)

# ----------------------------------------------------
# 2. Average Cost per Patient Stay
# ----------------------------------------------------
st.markdown("### 2️⃣ Average Cost per Patient Stay by Hospital & State")
st.markdown("Measures overall operational and clinical expense allocation relative to patient discharge volume.")

query_census_proxy = f"""
    SELECT 
        COUNTY_NAME,
        MASTER_PROVIDER_NAME AS HOSPITAL_NAME,
        ROUND(AVG(RESIDENT_CENSUS), 2) AS AVG_CENSUS,
        SUM(TOTAL_DIRECT_CARE_HOURS) AS TOTAL_ANNUAL_HOURS
    FROM HEALTHCARE_DB.GOLD.GOLD_MART_STAFFING_METRICS
    WHERE STATE = '{selected_state}'
    GROUP BY COUNTY_NAME, MASTER_PROVIDER_NAME
    ORDER BY AVG_CENSUS DESC;
"""
df_cost_proxy = session.sql(query_census_proxy).to_pandas()
if not df_cost_proxy.empty:
    st.dataframe(df_cost_proxy.head(10), use_container_width=True)
    st.caption("Displaying baseline annual nurse hours and census data while awaiting financial ledger integration for cost-per-stay calculation.")

st.markdown("---")

# ----------------------------------------------------
# 3. Cost of Overtime Hours as a % of Total Payroll
# ----------------------------------------------------
st.markdown("### 3️⃣ Cost of Overtime Hours as a Percentage of Total Payroll")
st.markdown("Quantifies financial premium spend driven by nurse overtime usage.")

st.warning(
    "**Data Availability Constraint:** Calculating overtime payroll percentages requires individual employee timesheet records "
    "with overtime multiplier flags (1.5x) and associated wage rates, which are stripped in facility-level daily CMS PBJ aggregates."
)

st.markdown("---")

# ----------------------------------------------------
# 4. Hospital Revenue vs. Payroll Expenses
# ----------------------------------------------------
st.markdown("### 📊 4️⃣ Hospital Revenue vs. Payroll Expenses")
st.markdown("Compares gross operating revenue against total staffing and operational payroll outlays.")

col_f1, col_f2 = st.columns(2)
with col_f1:
    st.markdown("#### 💵 Operating Revenue Trends")
    st.info("Aggregates Medicare reimbursements, private insurance payouts, and net patient revenue streams.")
with col_f2:
    st.markdown("#### 📉 Labor Expense Ratio")
    st.info("Evaluates labor cost as a percentage of total operating revenue to monitor hospital operating margins.")