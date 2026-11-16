*Water Quality Analysis & Prediction Report* — *Single Sample Test Report*

---

# WATER QUALITY TEST REPORT

**Machine Learning–Based Classification, WQI Regression & 5-Year Risk Forecast**

## Sample Information

| | | | |
|---|---|---|---|
| **Sample ID** | TANK-04-SMP | **Sampling Date** | 2026-11-10 |
| **Province** | Sindh | **City** | Karachi |
| **Resource Type** | Desalinated / Ground Inflow | **Sampling Location** | Karachi - Tanker 04 - Karachi Coastal Reservoir |
| **Collected By** | AquaVision Autonomous IoT Telemetry | **Report Date** | 2026-11-10 |
| **Laboratory** | National Water Quality Laboratory (Simulated) | **Report No.** | REP-20261110-5050F4 |

## Table 1: Input Features (Raw Sample Measurements)

*Enter laboratory-measured values for the single sample. Remark: Within / Exceeds permissible limit.*

| S.No. | Parameter | Unit | Measured Value | Permissible Limit | Remark |
|:---:|---|:---:|:---:|:---:|:---:|
| 1 | pH |  | 7.15 | 6.5–8.5 | Within reported limit |
| 2 | Turbidity | NTU | 2.5 | 5.0 | Within reported limit |
| 3 | TDS | mg/L | 465.0 | 1000.0 | Within reported limit |
| 4 | Chloride | mg/L | 210.0 | 250.0 | Within reported limit |
| 5 | Sulfate | mg/L | 98.0 | 250.0 | Within reported limit |
| 6 | Nitrate | mg/L | 14.0 | 50.0 | Within reported limit |
| 7 | Arsenic | mg/L | 0.009 | 0.05 | Within reported limit |
| 8 | Lead | mg/L | 0.006 | 0.05 | Within reported limit |
| 9 | EC | µS/cm | 530.0 | Not specified | Within reported limit |
| 10 | Hardness | mg/L | 190.0 | Not specified | Within reported limit |
| 11 | Total Coliform | CFU/100 mL | 0.0 | 0 (absence expected) | Within reported limit |


## Table 2: Feature Engineering

*Shows raw input and the corresponding engineered / transformed value for each feature.*

| S.No. | Feature | Transformation / Method Applied | Input Value | Engineered Value |
|:---:|---|---|:---:|:---:|
| 1 | Classification: Total Coliform | IQR capping + StandardScaler | 0.0 | -0.5796 |
| 2 | Classification: Arsenic (mg/L) | IQR capping + StandardScaler | 0.009 | 1.8909 |
| 3 | Classification: TDS (mg/L) | IQR capping + StandardScaler | 465.0 | -0.5685 |
| 4 | Classification: Potassium (mg/L) | Training median imputation + IQR capping + StandardScaler | Not provided | -0.4060 |
| 5 | Classification: Sodium (mg/L) | Training median imputation + IQR capping + StandardScaler | Not provided | -0.4385 |
| 6 | Classification: Magnesium (mg/L) | Training median imputation + IQR capping + StandardScaler | Not provided | -0.3943 |
| 7 | Classification: Nitrate (mg/L) | IQR capping + StandardScaler | 14.0 | 0.7290 |
| 8 | Classification: Turbidity (NTU) | IQR capping + StandardScaler | 2.5 | 1.0919 |
| 9 | Classification: Calcium (mg/L) | Training median imputation + IQR capping + StandardScaler | Not provided | -0.3571 |
| 10 | Classification: Chloride (mg/L) | IQR capping + StandardScaler | 210.0 | 0.2986 |
| 11 | Classification: EC (µS/cm) | IQR capping + StandardScaler | 530.0 | -0.7483 |
| 12 | Classification: Hardness (mg/L) | IQR capping + StandardScaler | 190.0 | -0.7307 |
| 13 | Regression: Arsenic (mg/L) | StandardScaler | 0.009 | -0.0641 |
| 14 | Regression: Magnesium (mg/L) | Training median imputation + StandardScaler | Not provided | -0.2208 |
| 15 | Regression: Nitrate (mg/L) | StandardScaler | 14.0 | 0.2992 |
| 16 | Regression: Sodium (mg/L) | Training median imputation + StandardScaler | Not provided | -0.2626 |
| 17 | Regression: Calcium (mg/L) | Training median imputation + StandardScaler | Not provided | -0.2832 |
| 18 | Regression: Sulfate (mg/L) | StandardScaler | 98.0 | -0.3473 |
| 19 | Regression: Fluoride (mg/L) | Training median imputation + StandardScaler | Not provided | -0.2123 |
| 20 | Regression: Chloride (mg/L) | StandardScaler | 210.0 | -0.1465 |
| 21 | Regression: Resource Type_Drinking Water | One-hot encoding + StandardScaler | Desalinated / Ground Inflow | -0.1370 |
| 22 | Regression: Potassium (mg/L) | Training median imputation + StandardScaler | Not provided | -0.3572 |
| 23 | Regression: Resource Type_Tap Water | One-hot encoding + StandardScaler | Desalinated / Ground Inflow | -0.0926 |


*Missing model inputs are imputed from the corresponding model's training data. The five-year forecast is based on the historical risk-score series, not this sample alone.*

## Table 3: Classification Results

*3a. Predicted classes*

| Classification Target | Model Used | Predicted Class | Confidence (%) | Actual Class |
|---|---|:---:|:---:|:---:|
| **WQI Category** | CatBoost regression + WQI thresholds | Excellent | N/A (threshold-derived) | Not provided |
| **Water Quality Class** | Tuned Gradient Boosting | Good | 47.3% | Not provided |
| **Microbial Status** | Laboratory measurement / NSDWQ rule | Not detected | Not applicable | Not detected |
| **Risk Category** | NSDWQ violation risk rules | Marginally Safe | Rule-derived | Not provided |

*3b. Class probability distribution (primary target)*

| Class | Predicted Probability | Rank |
|---|:---:|:---:|
| **Good** | 47.3% | 1 |
| **Unsuitable** | 35.3% | 2 |
| **Excellent** | 12.9% | 3 |
| **Poor** | 3.5% | 4 |
| **Very Poor** | 1.1% | 5 |


## Table 4: WQI Regression Results

*4a. Predicted vs. actual WQI*

| Item | Value | Remark |
|---|:---:|---|
| **Regression Model Used** | CatBoost | Selected trained WQI regression model |
| **Actual WQI** | Not provided | No laboratory WQI value supplied |
| **Predicted WQI** | 22.39 | CatBoost single-sample estimate |
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
| **Predicted WQI** | 22.39 | Excellent category from predicted WQI 22.39 |
| **Water Quality Class** | Good | Classifier output: Good (47.3% confidence); confirm with laboratory results. |
| **Microbial Status** | Not detected | No microbial contamination was reported. |
| **Current Risk Category** | Marginally Safe | Marginally Safe rule-derived risk (score 0/6) from reported NSDWQ exceedances. |
| **5-Year Risk Trend** | Stable | ARIMA population risk forecast trend over the five-year horizon: stable. |

**Summary:**

**Water Quality Report: TANK-04-SMP**

**Report Details**
*   **Report No:** REP-20261110-5050F4
*   **Sampling Date:** 2026-11-10
*   **Location:** Karachi - Tanker 04 - Karachi Coastal Reservoir
*   **Resource Type:** Desalinated / Ground Inflow
*   **Collection Method:** AquaVision Autonomous IoT Telemetry

**Analytical Summary**
The water sample from Tanker 04 was analyzed by the National Water Quality Laboratory (Simulated). Key parameters include a pH of 7.15, Turbidity of 2.5 NTU, TDS of 465.0 mg/L, and Hardness of 190.0 mg/L. Chemical constituents measured include Chloride (210.0 mg/L), Sulfate (98.0 mg/L), Nitrate (14.0 mg/L), Arsenic (0.009 mg/L), and Lead (0.006 mg/L). Electrical Conductivity (EC) was recorded at 530.0 µS/cm. Microbial analysis indicates Total Coliform is 0.0, with a microbial status of "Not detected."

**Model Assessment**
The water quality classification, determined by a Tuned Gradient Boosting model, is estimated as "Good" (47.3% confidence). The calculated Water Quality Index (WQI) is 22.39, categorized as "Excellent." A CatBoost regression model (R² Score: 0.88) and an ARIMA forecast model (MAPE: 2.17) were utilized for analysis. The system assigns a risk category of "Marginally Safe" with a risk score of 0.

**Compliance and Health Implications**
There are no National Standards for Drinking Water Quality (NSDWQ) violations identified in this sample. Consequently, no specific health implications are reported.

*Note: Several parameters, including Fluoride, Iron, Cadmium, Chromium, Mercury, Calcium, Magnesium, Sodium, Potassium, and E. Coli, were not supplied for this analysis.*

*Narrative source: Gemini*

**Conclusion:**

The models estimate WQI 22.39 (Excellent) and classify the sample as Good with 47.3% confidence. These are screening estimates, not a substitute for a certified laboratory assessment.

**Key Concerns:**

No exceedances detected in the parameters reported; unmeasured parameters were not assessed.

## Recommendations

| S.No. | Recommendation | Category | Priority | Timeline |
|:---:|---|---|:---:|:---:|
| 1 | Continue routine monitoring and test any parameters not measured in this sample. | Monitoring | Low | Long-term |


*Priority: High / Medium / Low. Timeline: Immediate / Short-term / Long-term.*

---

| **Prepared By** | **Reviewed By** | **Approved By** |
|:---:|:---:|:---:|
| Awais,Alishba,Ali | Alina_Baber | Not assigned |
| *Name / Signature / Date* | *Name / Signature / Date* | *Name / Signature / Date* |

### Data completeness
No measurement was supplied for these WQI parameters: Fluoride, Iron, Cadmium, Chromium, Mercury, Calcium, Magnesium, Sodium, Potassium, E. Coli. Model features not supplied were imputed using training-data medians; see Table 2.