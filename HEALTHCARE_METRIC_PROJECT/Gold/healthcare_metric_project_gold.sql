/*
This script creates business-ready data marts that directly answer your Staffing, Facility, Quality, Cost, and Operational metrics.
*/

USE ROLE ACCOUNTADMIN;
USE WAREHOUSE COMPUTE_WH;
USE DATABASE HEALTHCARE_DB;
CREATE SCHEMA IF NOT EXISTS HEALTHCARE_DB.GOLD;

--------------------------------------------------------------------------------
-- 1. GOLD_MART_STAFFING_METRICS
-- Description: Combines daily internal shift data with CMS regulatory HPRD and state averages.
--
-- Silver Tables Used:
--   1. SILVER.SILVER_MASTER_DIM_PROVIDER      (Master CSV: Provider dimension)
--   2. SILVER.SILVER_MASTER_FACT_DAILY_STAFFING (Master CSV: Daily shift & care hours log)
--   3. SILVER.SILVER_CMS_DIM_PROVIDER         (CMS File: Provider baseline info)
--   4. SILVER.SILVER_CMS_FACT_STAFFING        (CMS File: Regulatory reported HPRD & turnover)
--   5. SILVER.SILVER_CMS_BENCHMARKS_STATE_NATIONAL (CMS File: State & national benchmarks)
--------------------------------------------------------------------------------
CREATE OR REPLACE VIEW GOLD.GOLD_MART_STAFFING_METRICS AS
SELECT
    m.STATE,
    m.COUNTY_NAME,
    m.PROVIDER_ID,
    m.PROVIDER_NAME                                             AS MASTER_PROVIDER_NAME,
    cms_p.PROVIDER_NAME                                         AS CMS_PROVIDER_NAME,
    
    -- Internal Daily Staffing & Census Metrics (from Master CSV)
    f.WORK_DATE,
    f.CALENDAR_QUARTER,
    f.RESIDENT_CENSUS,
    f.RN_HOURS,
    f.LPN_HOURS,
    f.CNA_HOURS,
    f.MEDAIDE_HOURS,
    f.TOTAL_DIRECT_CARE_HOURS,
    f.RN_HPRD                                                   AS MASTER_RN_HPRD,
    f.TOTAL_NURSING_HPRD                                        AS MASTER_TOTAL_NURSING_HPRD,
    
    -- Regulatory CMS Reported Staffing Ratios (from CMS Files)
    cms_s.REPORTED_RN_HPRD                                      AS CMS_RN_HPRD,
    cms_s.REPORTED_LPN_HPRD                                     AS CMS_LPN_HPRD,
    cms_s.REPORTED_NURSE_AIDE_HPRD                              AS CMS_AIDE_HPRD,
    cms_s.REPORTED_TOTAL_NURSE_HPRD                             AS CMS_TOTAL_NURSE_HPRD,
    
    -- State & National Benchmarks Comparison
    b.REPORTED_TOTAL_NURSE_HPRD                                 AS STATE_AVG_NURSE_HPRD,
    ROUND(f.TOTAL_NURSING_HPRD - b.REPORTED_TOTAL_NURSE_HPRD, 2) AS VARIANCE_FROM_STATE_AVG,
    
    -- Turnover & Quality Audit Flags
    cms_s.NURSING_STAFF_TURNOVER_PCT,
    f.IS_ZERO_CENSUS,
    f.IS_HIGH_RN_HOURS,
    f.IS_HIGH_CNA_HOURS
FROM SILVER.SILVER_MASTER_DIM_PROVIDER m
LEFT JOIN SILVER.SILVER_MASTER_FACT_DAILY_STAFFING f ON m.PROVIDER_ID = f.PROVIDER_ID
LEFT JOIN SILVER.SILVER_CMS_DIM_PROVIDER cms_p ON m.PROVIDER_ID = cms_p.CCN
LEFT JOIN SILVER.SILVER_CMS_FACT_STAFFING cms_s ON m.PROVIDER_ID = cms_s.CCN
LEFT JOIN SILVER.SILVER_CMS_BENCHMARKS_STATE_NATIONAL b ON m.STATE = b.STATE_OR_NATION;


--------------------------------------------------------------------------------
-- 2. GOLD_MART_FACILITY_METRICS
-- Description: Measures bed capacity, average daily census, occupancy rates, and staffing strain.
--
-- Silver Tables Used:
--   1. SILVER.SILVER_MASTER_DIM_PROVIDER      (Master CSV: Provider dimension)
--   2. SILVER.SILVER_MASTER_FACT_DAILY_STAFFING (Master CSV: Daily resident census & direct care hours)
--   3. SILVER.SILVER_CMS_DIM_PROVIDER         (CMS File: Certified beds & ownership attributes)
--------------------------------------------------------------------------------
CREATE OR REPLACE VIEW GOLD.GOLD_MART_FACILITY_METRICS AS
SELECT
    m.STATE,
    m.COUNTY_NAME,
    m.PROVIDER_ID,
    COALESCE(m.PROVIDER_NAME, cms_p.PROVIDER_NAME)             AS PROVIDER_NAME,
    
    -- Daily Average Census & Bed Capacity Metrics
    AVG(f.RESIDENT_CENSUS)                                      AS AVG_DAILY_CENSUS,
    AVG(f.TOTAL_DIRECT_CARE_HOURS)                              AS AVG_DAILY_CARE_HOURS,
    
    -- CMS Facility Attributes
    cms_p.OWNERSHIP_TYPE,
    cms_p.CERTIFIED_BEDS,
    
    -- Bed Utilization / Occupancy Rate (CMS Certified Beds vs Master Census)
    ROUND(
        (AVG(f.RESIDENT_CENSUS) / NULLIF(cms_p.CERTIFIED_BEDS, 0)) * 100, 2
    )                                                           AS BED_OCCUPANCY_RATE_PCT,
    
    -- Operational Risk Category
    CASE 
        WHEN (AVG(f.RESIDENT_CENSUS) / NULLIF(cms_p.CERTIFIED_BEDS, 0)) >= 0.85 
         AND AVG(f.TOTAL_NURSING_HPRD) < 3.5 THEN 'CRITICAL_UNDERSTAFFED_HIGH_LOAD'
        WHEN (AVG(f.RESIDENT_CENSUS) / NULLIF(cms_p.CERTIFIED_BEDS, 0)) >= 0.85 THEN 'HIGH_OCCUPANCY'
        WHEN AVG(f.TOTAL_NURSING_HPRD) < 3.5 THEN 'BELOW_TARGET_STAFFING'
        ELSE 'OPTIMAL'
    END                                                         AS FACILITY_OPERATIONAL_STATUS
FROM SILVER.SILVER_MASTER_DIM_PROVIDER m
LEFT JOIN SILVER.SILVER_MASTER_FACT_DAILY_STAFFING f ON m.PROVIDER_ID = f.PROVIDER_ID
LEFT JOIN SILVER.SILVER_CMS_DIM_PROVIDER cms_p ON m.PROVIDER_ID = cms_p.CCN
GROUP BY m.STATE, m.COUNTY_NAME, m.PROVIDER_ID, COALESCE(m.PROVIDER_NAME, cms_p.PROVIDER_NAME), cms_p.OWNERSHIP_TYPE, cms_p.CERTIFIED_BEDS;


--------------------------------------------------------------------------------
-- 3. GOLD_MART_QUALITY_METRICS
-- Description: Analyzes star ratings, quality scores, inspection health citations, and staffing correlations.
--
-- Silver Tables Used:
--   1. SILVER.SILVER_MASTER_DIM_PROVIDER      (Master CSV: Provider dimension)
--   2. SILVER.SILVER_CMS_DIM_PROVIDER         (CMS File: Star ratings)
--   3. SILVER.SILVER_CMS_FACT_QUALITY_MEASURES (CMS File: Quality measures & readmissions)
--   4. SILVER.SILVER_CMS_FACT_STAFFING        (CMS File: HPRD & turnover context for correlation)
--   5. SILVER.SILVER_CMS_FACT_HEALTH_CITATIONS(CMS File: Deficiency citations log)
--------------------------------------------------------------------------------
CREATE OR REPLACE VIEW GOLD.GOLD_MART_QUALITY_METRICS AS
SELECT
    m.STATE,
    m.COUNTY_NAME,
    m.PROVIDER_ID,
    COALESCE(m.PROVIDER_NAME, cms_p.PROVIDER_NAME)             AS PROVIDER_NAME,
    
    -- Star Ratings
    cms_p.OVERALL_RATING,
    cms_p.HEALTH_INSPECTION_RATING,
    cms_p.QM_RATING,
    cms_p.STAFFING_RATING,
    
    -- Quality Measures & Readmission Rates
    qm.MEASURE_CODE,
    qm.MEASURE_DESCRIPTION,
    qm.RESIDENT_TYPE,
    qm.OBSERVED_SCORE                                           AS READMISSION_OR_QUALITY_OBSERVED_RATE,
    qm.EXPECTED_SCORE                                           AS READMISSION_OR_QUALITY_EXPECTED_RATE,
    qm.ADJUSTED_SCORE                                           AS READMISSION_OR_QUALITY_ADJUSTED_RATE,
    
    -- Total Health Citations
    COALESCE(cit.TOTAL_CITATIONS, 0)                            AS TOTAL_HEALTH_CITATIONS,
    
    -- Staffing Ratios for Correlation Analysis
    cms_s.REPORTED_TOTAL_NURSE_HPRD                             AS CMS_TOTAL_NURSE_HPRD,
    cms_s.NURSING_STAFF_TURNOVER_PCT
FROM SILVER.SILVER_MASTER_DIM_PROVIDER m
LEFT JOIN SILVER.SILVER_CMS_DIM_PROVIDER cms_p ON m.PROVIDER_ID = cms_p.CCN
LEFT JOIN SILVER.SILVER_CMS_FACT_QUALITY_MEASURES qm ON m.PROVIDER_ID = qm.CCN
LEFT JOIN SILVER.SILVER_CMS_FACT_STAFFING cms_s ON m.PROVIDER_ID = cms_s.CCN
LEFT JOIN (
    SELECT CCN, COUNT(*) AS TOTAL_CITATIONS 
    FROM SILVER.SILVER_CMS_FACT_HEALTH_CITATIONS 
    GROUP BY CCN
) cit ON m.PROVIDER_ID = cit.CCN;


/*
What Is Missing & WhyShift Timestamps (Morning / Afternoon / Night):Public CMS staffing datasets (and PBJ daily staffing files) aggregate hours to a single 24-hour day total (HRS_RN, HRS_LPN, HRS_CNA).Missing Source Data: You would need raw timecard / badge swipe logs (e.g., Kronos, ADP, or internal hospital EHR shift exports) that capture clock-in and clock-out timestamps.Payroll Costs & Wages:CMS nursing home datasets intentionally exclude private financial wage records.Missing Source Data: You would need internal general ledger (GL) payroll records or Bureau of Labor Statistics (BLS) wage estimates by state/ZIP code.Hospital / Facility Revenue:Nursing home CMS public datasets report quality, staffing, and compliance rather than complete P&L revenue statements.Missing Source Data: You would need CMS Cost Reports (Form CMS-2540-10) or internal general ledger financial statements.Recommended Course of ActionTo answer Nurse Attrition, Quality Correlations, & Fines: You have all required data across NH_ProviderInfo_Oct2024.csv, NH_Penalties_Oct2024.csv, and NH_QualityMsr_Claims_Oct2024.csv.   For Payroll Costs & Shift Breakdowns: Communicate to your project stakeholders or instructor that these specific metrics are out-of-scope based on the available CMS files, or request access to internal timecard/payroll tables.   
*/

-- SELECT 
--     distance,
--     source_object_name AS UPSTREAM_SOURCE,
--     source_object_domain AS SOURCE_TYPE,
--     target_object_name AS DOWNSTREAM_TARGET,
--     target_object_domain AS TARGET_TYPE
-- FROM TABLE(
--     SNOWFLAKE.CORE.GET_LINEAGE(
--         'HEALTHCARE_DB.GOLD.GOLD_MART_STAFFING_METRICS', 
--         'TABLE', 
--         'UPSTREAM',
--         5 -- Retrieves up to 5 hops back across Gold -> Silver -> Bronze -> Stage
--     )
-- )
-- ORDER BY distance ASC;