<div align="center">

# 🏥 Snowflake Healthcare Analytics Platform

[![Snowflake](https://img.shields.io/badge/Snowflake-29B5E8?style=for-the-badge&logo=snowflake&logoColor=white)](https://www.snowflake.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Python](https://img.shields.io/badge/Python-3.9%252B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)

An end-to-end healthcare data platform and multi-page interactive analytics application built natively within **Snowflake**, utilizing a Medallion architecture for robust data transformation.

</div>

---

## 🧭 Overview

The **Healthcare Metrics Project** is designed to provide comprehensive, real-time visibility into hospital and healthcare network performance. It processes multi-source data through a structured Medallion pipeline (`RAW` $\rightarrow$ `BRONZE` $\rightarrow$ `SILVER` $\rightarrow$ `GOLD`), tracks critical operational and clinical benchmarks, and exposes them through a high-performance Streamlit dashboard deployed directly inside Snowflake.

---

## 🏗️ Data Architecture (`HEALTHCARE_DB`)

The project operates out of a centralized Snowflake database structured into dedicated functional schemas following modern data modeling standards:

| Schema | Layer Role | Description |
| :--- | :--- | :--- |
| **`RAW`** | Ingestion | Landing zone for raw CSV, JSON, and CMS datasets. |
| **`BRONZE`** | Cleansing | Initial structural formatting, typing, and light hygiene. |
| **`SILVER`** | Enrichment | Intermediate transformations, entity resolution, and business logic joins. |
| **`GOLD`** | Serving | Production-ready, aggregated data marts optimized for analytics and reporting. |

### Key Gold Layer Marts
* **`GOLD_MART_STAFFING_METRICS`**: Tracks nurse-to-patient ratios, direct-care hours per patient day (HPRD), and working hours.
* **`GOLD_MART_FACILITY_METRICS`**: Monitors facility capacity, occupancy rates, and patient volume throughput.
* **`GOLD_MART_QUALITY_METRICS`**: Evaluates patient care quality indicators and regulatory compliance metrics.

---

## 🖥️ Streamlit Dashboard Structure

The interactive frontend features a modular multi-page layout built for seamless stakeholder navigation:

* 🏠 **`0_Home_Overview.py`**: Global state management, state-level filtering (e.g., California), and executive metric summaries.
* 👩‍⚕️ **`1_Staffing_and_Nurse_Hours.py`**: Deep dive into staffing distributions and workforce trends.
* 🛏️ **`2_Facility_Metrics_and_Occupancy.py`**: Hospital bed capacity and utilization analytics.
* ⭐ **`3_Quality_Metrics.py`**: Clinical care standards and safety performance indicators.
* 💰 **`4_Cost_Metrics.py`**: Financial breakdowns and operational expense tracking.
* 📈 **`5_Operational_Metrics.py`**: General hospital throughput and efficiency diagnostics.

---

## 🚀 Quick Start & Deployment

### 1. **Data Ingestion**
- `healthcare_metric_project_data_ingestion.sql`

### 2. **Raw Layer**
- `healthcare_metrics_project_raw_CMS.sql`
- `healthcare_metrics_project_raw_master.sql`

### 3. **Bronze Layer**
- `healthcare_metrics_project_bronze_CMS.sql`
- `healthcare_metrics_project_bronze_master.sql`

### 4. **Silver Layer**
- `healthcare_metrics_project_silver_CMS.sql`
- `healthcare_metrics_project_silver_master.sql`

### 5. **Gold Layer**
- `healthcare_metrics_project_gold.sql`

These scripts establish the project's data pipeline from **data ingestion through the Raw, Bronze, Silver, and Gold layers**, including CMS-specific processing and final analytical marts.

### 6. **Launch the Dashboard**

Open Snowsight and navigate to your workspace or Streamlit app interface. Select `0_Home_Overview.py` as the entrypoint file and run the application.

---
