*Water Quality Analysis & Prediction Report* — *Single Sample Test Report*

---

# WATER QUALITY TEST REPORT

**Machine Learning–Based Classification, WQI Regression & 5-Year Risk Forecast**

## Sample Information

| | | | |
|---|---|---|---|
| **Sample ID** | TANK-ALI-SMP | **Sampling Date** | 2026-11-09 |
| **Province** | Federal Capital | **City** | Islamabad |
| **Resource Type** | RO Filtration | **Sampling Location** | Islamabad - Hassan |
| **Collected By** | AquaVision Autonomous IoT Telemetry | **Report Date** | 2026-11-09 |
| **Laboratory** | National Water Quality Laboratory (Simulated) | **Report No.** | REP-20261109-46868B |

## Table 1: Input Features (Raw Sample Measurements)

*Enter laboratory-measured values for the single sample. Remark: Within / Exceeds permissible limit.*

| S.No. | Parameter | Unit | Measured Value | Permissible Limit | Remark |
|:---:|---|:---:|:---:|:---:|:---:|
| 1 | pH |  | 9.9 | 6.5–8.5 | Exceeds |
| 2 | Turbidity | NTU | 2.0 | 5.0 | Within reported limit |
| 3 | TDS | mg/L | 450.0 | 1000.0 | Within reported limit |
| 4 | Chloride | mg/L | 120.0 | 250.0 | Within reported limit |
| 5 | Sulfate | mg/L | 90.0 | 250.0 | Within reported limit |
| 6 | Nitrate | mg/L | 12.0 | 50.0 | Within reported limit |
| 7 | Arsenic | mg/L | 0.008 | 0.05 | Within reported limit |
| 8 | Lead | mg/L | 0.005 | 0.05 | Within reported limit |
| 9 | EC | µS/cm | 500.0 | Not specified | Within reported limit |
| 10 | Hardness | mg/L | 160.0 | Not specified | Within reported limit |
| 11 | Total Coliform | CFU/100 mL | 0.0 | 0 (absence expected) | Within reported limit |


## Table 2: Feature Engineering

*Shows raw input and the corresponding engineered / transformed value for each feature.*

| S.No. | Feature | Transformation / Method Applied | Input Value | Engineered Value |
|:---:|---|---|:---:|:---:|
| 1 | Classification: Total Coliform | IQR capping + StandardScaler | 0.0 | -0.5796 |
| 2 | Classification: Arsenic (mg/L) | IQR capping + StandardScaler | 0.008 | 1.8909 |
| 3 | Classification: TDS (mg/L) | IQR capping + StandardScaler | 450.0 | -0.5893 |
| 4 | Classification: Potassium (mg/L) | Training median imputation + IQR capping + StandardScaler | Not provided | -0.4060 |
| 5 | Classification: Sodium (mg/L) | Training median imputation + IQR capping + StandardScaler | Not provided | -0.4385 |
| 6 | Classification: Magnesium (mg/L) | Training median imputation + IQR capping + StandardScaler | Not provided | -0.3943 |
| 7 | Classification: Nitrate (mg/L) | IQR capping + StandardScaler | 12.0 | 0.4873 |
| 8 | Classification: Turbidity (NTU) | IQR capping + StandardScaler | 2.0 | 0.6394 |
| 9 | Classification: Calcium (mg/L) | Training median imputation + IQR capping + StandardScaler | Not provided | -0.3571 |
| 10 | Classification: Chloride (mg/L) | IQR capping + StandardScaler | 120.0 | -0.2327 |
| 11 | Classification: EC (µS/cm) | IQR capping + StandardScaler | 500.0 | -0.8081 |
| 12 | Classification: Hardness (mg/L) | IQR capping + StandardScaler | 160.0 | -0.8795 |
| 13 | Regression: Arsenic (mg/L) | StandardScaler | 0.008 | -0.0643 |
| 14 | Regression: Magnesium (mg/L) | Training median imputation + StandardScaler | Not provided | -0.2208 |
| 15 | Regression: Nitrate (mg/L) | StandardScaler | 12.0 | 0.1616 |
| 16 | Regression: Sodium (mg/L) | Training median imputation + StandardScaler | Not provided | -0.2626 |
| 17 | Regression: Calcium (mg/L) | Training median imputation + StandardScaler | Not provided | -0.2832 |
| 18 | Regression: Sulfate (mg/L) | StandardScaler | 90.0 | -0.3681 |
| 19 | Regression: Fluoride (mg/L) | Training median imputation + StandardScaler | Not provided | -0.2123 |
| 20 | Regression: Chloride (mg/L) | StandardScaler | 120.0 | -0.1965 |
| 21 | Regression: Resource Type_Drinking Water | One-hot encoding + StandardScaler | RO Filtration | -0.1370 |
| 22 | Regression: Potassium (mg/L) | Training median imputation + StandardScaler | Not provided | -0.3572 |
| 23 | Regression: Resource Type_Tap Water | One-hot encoding + StandardScaler | RO Filtration | -0.0926 |


*Missing model inputs are imputed from the corresponding model's training data. The five-year forecast is based on the historical risk-score series, not this sample alone.*

## Table 3: Classification Results

*3a. Predicted classes*

| Classification Target | Model Used | Predicted Class | Confidence (%) | Actual Class |
|---|---|:---:|:---:|:---:|
| **WQI Category** | CatBoost regression + WQI thresholds | Excellent | N/A (threshold-derived) | Not provided |
| **Water Quality Class** | Tuned Gradient Boosting | Unsuitable | 48.4% | Not provided |
| **Microbial Status** | Laboratory measurement / NSDWQ rule | Not detected | Not applicable | Not detected |
| **Risk Category** | NSDWQ violation risk rules | Marginally Safe | Rule-derived | Not provided |

*3b. Class probability distribution (primary target)*

| Class | Predicted Probability | Rank |
|---|:---:|:---:|
| **Unsuitable** | 48.4% | 1 |
| **Good** | 36.2% | 2 |
| **Excellent** | 9.9% | 3 |
| **Poor** | 4.3% | 4 |
| **Very Poor** | 1.2% | 5 |


## Table 4: WQI Regression Results

*4a. Predicted vs. actual WQI*

| Item | Value | Remark |
|---|:---:|---|
| **Regression Model Used** | CatBoost | Selected trained WQI regression model |
| **Actual WQI** | Not provided | No laboratory WQI value supplied |
| **Predicted WQI** | 22.32 | CatBoost single-sample estimate |
| **Absolute Error** | Not available | Cannot calculate without an actual WQI |
| **WQI Category (Predicted)** | Excellent | Based on the predicted WQI score |

*4b. Model performance metrics*

| R² Score | RMSE | MAE | MAPE (%) |
|:---:|:---:|:---:|:---:|
| 0.8833 | 7.9510 | 4.1658 | Not reported in saved regression evaluation |

## Table 5: 5-Year Risk Score Forecast

*5a. Forecasted risk score*

| Forecast Year | Forecast Period | Predicted Risk Score | Confidence Interval | Risk Category | Trend (↑ / ↓ / →) |
|---|:---:|:---:|:---:|:---:|:---:|
| **Year 1** | 2026-12 to 2027-11 | 0.85 | 0.00–2.61 | Marginally Safe | → |
| **Year 2** | 2027-12 to 2028-11 | 0.85 | 0.00–2.89 | Marginally Safe | → |
| **Year 3** | 2028-12 to 2029-11 | 0.85 | 0.00–3.14 | Marginally Safe | → |
| **Year 4** | 2029-12 to 2030-11 | 0.85 | 0.00–3.37 | Marginally Safe | → |
| **Year 5** | 2030-12 to 2031-11 | 0.85 | 0.00–3.58 | Marginally Safe | → |


*5b. Forecasting model details*

| Forecasting Model | Training Period | Evaluation Metric |
|---|:---:|:---:|
| ARIMA | 2013-01 to 2025-01 (145 monthly observations) | RMSE=0.1000; MAE=0.0186; MAPE=2.17% |

## Summary & Conclusion

*Key findings for this sample*

| Parameter | Result | Interpretation |
|---|:---:|---|
| **Predicted WQI** | 22.32 | Excellent category from predicted WQI 22.32 |
| **Water Quality Class** | Unsuitable | Classifier output: Unsuitable (48.4% confidence); confirm with laboratory results. |
| **Microbial Status** | Not detected | No microbial contamination was reported. |
| **Current Risk Category** | Marginally Safe | Marginally Safe rule-derived risk (score 0/6) from reported NSDWQ exceedances. |
| **5-Year Risk Trend** | Stable | ARIMA population risk forecast trend over the five-year horizon: stable. |

**Summary:**

**Water Quality Report Narrative**

**Report ID:** REP-20261109-46868B
**Location:** Islamabad - Hassan
**Resource Type:** RO Filtration
**Sampling Date:** 2026-11-09

**Technical Assessment**
The water sample (ID: TANK-ALI-SMP) was analyzed via AquaVision Autonomous IoT Telemetry. Key physicochemical parameters include a pH of 9.9, Turbidity of 2.0 NTU, TDS of 450.0 mg/L, and Hardness of 160.0 mg/L. Microbial analysis indicates a Total Coliform count of 0.0, with a microbial status of "Not detected."

**Model-Based Analysis**
The water quality was evaluated using a Tuned Gradient Boosting classification model, which assigned a Water Quality Index (WQI) of 22.32 (categorized as "Excellent"). However, the final classification model output indicates the water is "Unsuitable" with a confidence level of 48.4%. A CatBoost regression model was utilized for further analysis, yielding an R² score of 0.88. An ARIMA forecast model (trained on 145 monthly observations from 2013–2025) supports these findings with an RMSE of 0.1. The overall risk assessment is categorized as "Marginally Safe" (Risk Score: 0).

**Compliance and Health Implications**
The sample shows a violation of National Standards for Drinking Water Quality (NSDWQ) regarding pH. The measured pH of 9.9 exceeds the maximum permissible limit of 8.5. Elevated pH levels (alkalinity) can affect the taste of water and may cause skin or eye irritation upon contact.

*Note: The final water quality classification of "Unsuitable" is a model estimate based on the provided parameters and feature engineering processes.*

*Narrative source: Gemini*

**Conclusion:**

The models estimate WQI 22.32 (Excellent) and classify the sample as Unsuitable with 48.4% confidence. These are screening estimates, not a substitute for a certified laboratory assessment.

**Key Concerns:**

pH (moderate exceedance); Regression and classification outputs differ substantially; confirm the sample with laboratory results.

## Recommendations

| S.No. | Recommendation | Category | Priority | Timeline |
|:---:|---|---|:---:|:---:|
| 1 | Adjust pH using a treatment plan appropriate to the measured acidity or alkalinity. | pH | Medium | Short-term |


*Priority: High / Medium / Low. Timeline: Immediate / Short-term / Long-term.*

---

| **Prepared By** | **Reviewed By** | **Approved By** |
|:---:|:---:|:---:|
| Awais,Alishba,Ali | Alina_Baber | Not assigned |
| *Name / Signature / Date* | *Name / Signature / Date* | *Name / Signature / Date* |

### Data completeness
No measurement was supplied for these WQI parameters: Fluoride, Iron, Cadmium, Chromium, Mercury, Calcium, Magnesium, Sodium, Potassium, E. Coli. Model features not supplied were imputed using training-data medians; see Table 2.