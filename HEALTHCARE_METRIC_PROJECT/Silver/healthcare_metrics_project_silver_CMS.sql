/*
The Silver Layer acts as the curated, business-conformed data layer.

Key Characteristics & Transformations in Silver
Deduplication: Eliminates duplicate rows across natural keys (e.g., CCN, PENALTY_DATE, MEASURE_CODE).

Data Cleansing & Standardization: Strips trailing whitespaces, standardizes state codes to uppercase, and converts blank strings or invalid text placeholders to SQL NULL.

Surrogate Keys: Generates unique primary keys (HASH or AUTOINCREMENT) for dimension and fact modeling.

Data Enriched Features: Derives helper metrics (e.g., total penalty cost flags, staffing compliance indicators).
*/

USE ROLE ACCOUNTADMIN;
USE WAREHOUSE COMPUTE_WH;
USE DATABASE HEALTHCARE_DB;
USE SCHEMA SILVER;

--------------------------------------------------------------------------------
-- 1. SILVER_DIM_PROVIDER (Nursing Home Provider Master Dimension)
--------------------------------------------------------------------------------
CREATE OR REPLACE TABLE SILVER.SILVER_DIM_PROVIDER AS
WITH deduped_providers AS (
    SELECT
        CCN,
        TRIM(PROVIDER_NAME)                                 AS PROVIDER_NAME,
        TRIM(PROVIDER_ADDRESS)                              AS PROVIDER_ADDRESS,
        TRIM(CITY)                                          AS CITY,
        UPPER(TRIM(STATE))                                  AS STATE,
        TRIM(ZIP_CODE)                                      AS ZIP_CODE,
        TELEPHONE_NUMBER,
        OWNERSHIP_TYPE,
        CERTIFIED_BEDS,
        AVG_RESIDENTS_PER_DAY,
        PROVIDER_TYPE,
        IS_HOSPITAL_BASED,
        LEGAL_BUSINESS_NAME,
        MEDICARE_MEDICAID_APPROVAL_DATE,
        AFFILIATED_ENTITY_NAME,
        IS_CCRC,
        SPECIAL_FOCUS_STATUS,
        HAS_ABUSE_ICON,
        OVERALL_RATING,
        HEALTH_INSPECTION_RATING,
        QM_RATING,
        STAFFING_RATING,
        LATITUDE,
        LONGITUDE,
        PROCESSING_DATE,
        ROW_NUMBER() OVER (
            PARTITION BY CCN 
            ORDER BY PROCESSING_DATE DESC, _INGESTED_AT DESC
        ) AS rn
    FROM BRONZE.BRONZE_NH_PROVIDER_INFO
    WHERE CCN IS NOT NULL
)
SELECT
    MD5(CCN)                                                AS PROVIDER_SK,
    CCN,
    PROVIDER_NAME,
    PROVIDER_ADDRESS,
    CITY,
    STATE,
    ZIP_CODE,
    TELEPHONE_NUMBER,
    OWNERSHIP_TYPE,
    CERTIFIED_BEDS,
    AVG_RESIDENTS_PER_DAY,
    PROVIDER_TYPE,
    IS_HOSPITAL_BASED,
    LEGAL_BUSINESS_NAME,
    MEDICARE_MEDICAID_APPROVAL_DATE,
    AFFILIATED_ENTITY_NAME,
    IS_CCRC,
    SPECIAL_FOCUS_STATUS,
    HAS_ABUSE_ICON,
    OVERALL_RATING,
    HEALTH_INSPECTION_RATING,
    QM_RATING,
    STAFFING_RATING,
    LATITUDE,
    LONGITUDE,
    PROCESSING_DATE,
    CURRENT_TIMESTAMP()                                     AS _UPDATED_AT
FROM deduped_providers
WHERE rn = 1;


--------------------------------------------------------------------------------
-- 2. SILVER_FACT_STAFFING (Staffing & Turnover Performance Fact)
--------------------------------------------------------------------------------
CREATE OR REPLACE TABLE SILVER.SILVER_FACT_STAFFING AS
SELECT
    MD5(CONCAT(p.CCN, '_', COALESCE(p.PROCESSING_DATE, CURRENT_DATE()))) AS STAFFING_FACT_KEY,
    MD5(p.CCN)                                                           AS PROVIDER_SK,
    p.CCN,
    p.REPORTED_NURSE_AIDE_HPRD,
    p.REPORTED_LPN_HPRD,
    p.REPORTED_RN_HPRD,
    p.REPORTED_LICENSED_HPRD,
    p.REPORTED_TOTAL_NURSE_HPRD,
    p.REPORTED_WEEKEND_TOTAL_NURSE_HPRD,
    p.REPORTED_WEEKEND_RN_HPRD,
    p.REPORTED_PT_HPRD,
    p.NURSING_STAFF_TURNOVER_PCT,
    p.RN_TURNOVER_PCT,
    p.ADMINISTRATORS_DEPARTED,
    p.ADJUSTED_TOTAL_NURSE_HPRD,
    -- Derived Staffing Ratio Comparison vs. Federal Target
    IFF(p.REPORTED_TOTAL_NURSE_HPRD >= 3.5, TRUE, FALSE)                  AS MEETS_RECOMMENDED_NURSING_HOURS,
    p.PROCESSING_DATE,
    CURRENT_TIMESTAMP()                                                  AS _UPDATED_AT
FROM BRONZE.BRONZE_NH_PROVIDER_INFO p
WHERE p.CCN IS NOT NULL;


--------------------------------------------------------------------------------
-- 3. SILVER_FACT_QUALITY_MEASURES (Claims-Based Quality Metrics)
--------------------------------------------------------------------------------
CREATE OR REPLACE TABLE SILVER.SILVER_FACT_QUALITY_MEASURES AS
WITH deduped_qm AS (
    SELECT
        CCN,
        MEASURE_CODE,
        TRIM(MEASURE_DESCRIPTION)                           AS MEASURE_DESCRIPTION,
        RESIDENT_TYPE,
        ADJUSTED_SCORE,
        OBSERVED_SCORE,
        EXPECTED_SCORE,
        IS_USED_IN_5STAR_RATING,
        MEASURE_PERIOD,
        PROCESSING_DATE,
        ROW_NUMBER() OVER (
            PARTITION BY CCN, MEASURE_CODE, MEASURE_PERIOD 
            ORDER BY PROCESSING_DATE DESC, _INGESTED_AT DESC
        ) AS rn
    FROM BRONZE.BRONZE_NH_QUALITY_MSR_CLAIMS
    WHERE CCN IS NOT NULL AND MEASURE_CODE IS NOT NULL
)
SELECT
    MD5(CONCAT(CCN, '_', MEASURE_CODE, '_', COALESCE(MEASURE_PERIOD, 'UNK'))) AS QM_FACT_KEY,
    MD5(CCN)                                                                 AS PROVIDER_SK,
    CCN,
    MEASURE_CODE,
    MEASURE_DESCRIPTION,
    RESIDENT_TYPE,
    ADJUSTED_SCORE,
    OBSERVED_SCORE,
    EXPECTED_SCORE,
    IS_USED_IN_5STAR_RATING,
    MEASURE_PERIOD,
    PROCESSING_DATE,
    CURRENT_TIMESTAMP()                                                      AS _UPDATED_AT
FROM deduped_qm
WHERE rn = 1;


--------------------------------------------------------------------------------
-- 4. SILVER_FACT_PENALTIES (Enforcement & Fines Fact)
--------------------------------------------------------------------------------
CREATE OR REPLACE TABLE SILVER.SILVER_FACT_PENALTIES AS
WITH deduped_penalties AS (
    SELECT
        CCN,
        PENALTY_DATE,
        PENALTY_TYPE,
        FINE_AMOUNT,
        PAYMENT_DENIAL_START_DATE,
        PAYMENT_DENIAL_LENGTH_DAYS,
        PROCESSING_DATE,
        ROW_NUMBER() OVER (
            PARTITION BY CCN, PENALTY_DATE, PENALTY_TYPE, COALESCE(FINE_AMOUNT, 0)
            ORDER BY _INGESTED_AT DESC
        ) AS rn
    FROM BRONZE.BRONZE_NH_PENALTIES
    WHERE CCN IS NOT NULL AND PENALTY_DATE IS NOT NULL
)
SELECT
    MD5(CONCAT(CCN, '_', PENALTY_DATE, '_', PENALTY_TYPE))  AS PENALTY_FACT_KEY,
    MD5(CCN)                                                AS PROVIDER_SK,
    CCN,
    PENALTY_DATE,
    PENALTY_TYPE,
    COALESCE(FINE_AMOUNT, 0)                                AS FINE_AMOUNT,
    PAYMENT_DENIAL_START_DATE,
    PAYMENT_DENIAL_LENGTH_DAYS,
    IFF(FINE_AMOUNT > 10000, 'HIGH_FINE', 'STANDARD_FINE')  AS FINE_SEVERITY_TIER,
    PROCESSING_DATE,
    CURRENT_TIMESTAMP()                                     AS _UPDATED_AT
FROM deduped_penalties
WHERE rn = 1;


--------------------------------------------------------------------------------
-- 5. SILVER_FACT_HEALTH_CITATIONS (Surveys & Deficiencies)
--------------------------------------------------------------------------------
CREATE OR REPLACE TABLE SILVER.SILVER_FACT_HEALTH_CITATIONS AS
WITH deduped_citations AS (
    SELECT
        CCN,
        SURVEY_DATE,
        DEFICIENCY_TAG_NUMBER,
        DEFICIENCY_PREFIX,
        DEFICIENCY_DESCRIPTION,
        SCOPE_SEVERITY_CODE,
        IS_DEFICIENCY_CORRECTED,
        CORRECTION_DATE,
        INSPECTION_CYCLE,
        STANDARD_DEFICIENCIES,
        COMPLAINT_DEFICIENCIES,
        INFECTION_CONTROL_DEFICIENCIES,
        PROCESSING_DATE,
        ROW_NUMBER() OVER (
            PARTITION BY CCN, SURVEY_DATE, DEFICIENCY_TAG_NUMBER
            ORDER BY _INGESTED_AT DESC
        ) AS rn
    FROM BRONZE.BRONZE_NH_HEALTH_CITATIONS
    WHERE CCN IS NOT NULL AND SURVEY_DATE IS NOT NULL
)
SELECT
    MD5(CONCAT(CCN, '_', SURVEY_DATE, '_', COALESCE(DEFICIENCY_TAG_NUMBER, 'UNTAGGED'))) AS CITATION_FACT_KEY,
    MD5(CCN)                                                                             AS PROVIDER_SK,
    CCN,
    SURVEY_DATE,
    DEFICIENCY_PREFIX,
    DEFICIENCY_TAG_NUMBER,
    DEFICIENCY_DESCRIPTION,
    SCOPE_SEVERITY_CODE,
    IS_DEFICIENCY_CORRECTED,
    CORRECTION_DATE,
    INSPECTION_CYCLE,
    STANDARD_DEFICIENCIES,
    COMPLAINT_DEFICIENCIES,
    INFECTION_CONTROL_DEFICIENCIES,
    -- Calculate Days to Correct Deficiency
    DATEDIFF('day', SURVEY_DATE, CORRECTION_DATE)                                         AS DAYS_TO_CORRECT,
    PROCESSING_DATE,
    CURRENT_TIMESTAMP()                                                                  AS _UPDATED_AT
FROM deduped_citations
WHERE rn = 1;


--------------------------------------------------------------------------------
-- 6. SILVER_BENCHMARKS_STATE_NATIONAL (State & US Benchmarks)
--------------------------------------------------------------------------------
CREATE OR REPLACE TABLE SILVER.SILVER_BENCHMARKS_STATE_NATIONAL AS
SELECT
    MD5(STATE_OR_NATION)                                    AS BENCHMARK_SK,
    STATE_OR_NATION,
    AVG_RESIDENTS_PER_DAY,
    REPORTED_NURSE_AIDE_HPRD,
    REPORTED_LPN_HPRD,
    REPORTED_RN_HPRD,
    REPORTED_LICENSED_HPRD,
    REPORTED_TOTAL_NURSE_HPRD,
    NURSING_STAFF_TURNOVER_PCT,
    RN_TURNOVER_PCT,
    AVG_FINES_COUNT,
    AVG_FINE_AMOUNT,
    PROCESSING_DATE,
    CURRENT_TIMESTAMP()                                     AS _UPDATED_AT
FROM BRONZE.BRONZE_NH_STATE_US_AVERAGES;

-- RENAME CSM FILE Tables
ALTER TABLE SILVER_DIM_PROVIDER RENAME TO SILVER_CMS_DIM_PROVIDER;
ALTER TABLE SILVER_FACT_STAFFING RENAME TO SILVER_CMS_FACT_STAFFING;
ALTER TABLE SILVER_FACT_QUALITY_MEASURES RENAME TO SILVER_CMS_FACT_QUALITY_MEASURES;
ALTER TABLE SILVER_FACT_PENALTIES RENAME TO SILVER_CMS_FACT_PENALTIES;
ALTER TABLE SILVER_FACT_HEALTH_CITATIONS RENAME TO SILVER_CMS_FACT_HEALTH_CITATIONS;
ALTER TABLE SILVER_BENCHMARKS_STATE_NATIONAL RENAME TO SILVER_CMS_BENCHMARKS_STATE_NATIONAL;