*Water Quality Analysis & Prediction Report* — *Single Sample Test Report*

---

# WATER QUALITY TEST REPORT

**Machine Learning–Based Classification, WQI Regression & 5-Year Risk Forecast**

## Sample Information

| | | | |
|---|---|---|---|
| **Sample ID** | TANK-02-SMP | **Sampling Date** | 2026-11-10 |
| **Province** | Punjab | **City** | Rawalpindi |
| **Resource Type** | Surface Water | **Sampling Location** | Rawalpindi - Tanker 02 - Rawalpindi Filtration Unit |
| **Collected By** | AquaVision Autonomous IoT Telemetry | **Report Date** | 2026-11-10 |
| **Laboratory** | National Water Quality Laboratory (Simulated) | **Report No.** | REP-20261110-AA2827 |

## Table 1: Input Features (Raw Sample Measurements)

*Enter laboratory-measured values for the single sample. Remark: Within / Exceeds permissible limit.*

| S.No. | Parameter | Unit | Measured Value | Permissible Limit | Remark |
|:---:|---|:---:|:---:|:---:|:---:|
| 1 | pH |  | 7.85 | 6.5–8.5 | Within reported limit |
| 2 | Turbidity | NTU | 3.9 | 5.0 | Within reported limit |
| 3 | TDS | mg/L | 540.0 | 1000.0 | Within reported limit |
| 4 | Chloride | mg/L | 180.0 | 250.0 | Within reported limit |
| 5 | Sulfate | mg/L | 130.0 | 250.0 | Within reported limit |
| 6 | Nitrate | mg/L | 22.0 | 50.0 | Within reported limit |
| 7 | Arsenic | mg/L | 0.015 | 0.05 | Within reported limit |
| 8 | Lead | mg/L | 0.008 | 0.05 | Within reported limit |
| 9 | EC | µS/cm | 610.0 | Not specified | Within reported limit |
| 10 | Hardness | mg/L | 280.0 | Not specified | Within reported limit |
| 11 | Total Coliform | CFU/100 mL | 1.0 | 0 (absence expected) | Within reported limit |


## Table 2: Feature Engineering

*Shows raw input and the corresponding engineered / transformed value for each feature.*

| S.No. | Feature | Transformation / Method Applied | Input Value | Engineered Value |
|:---:|---|---|:---:|:---:|
| 1 | Classification: Total Coliform | IQR capping + StandardScaler | 1.0 | -0.1157 |
| 2 | Classification: Arsenic (mg/L) | IQR capping + StandardScaler | 0.015 | 1.8909 |
| 3 | Classification: TDS (mg/L) | IQR capping + StandardScaler | 540.0 | -0.4645 |
| 4 | Classification: Potassium (mg/L) | Training median imputation + IQR capping + StandardScaler | Not provided | -0.4060 |
| 5 | Classification: Sodium (mg/L) | Training median imputation + IQR capping + StandardScaler | Not provided | -0.4385 |
| 6 | Classification: Magnesium (mg/L) | Training median imputation + IQR capping + StandardScaler | Not provided | -0.3943 |
| 7 | Classification: Nitrate (mg/L) | IQR capping + StandardScaler | 22.0 | 1.6957 |
| 8 | Classification: Turbidity (NTU) | IQR capping + StandardScaler | 3.9 | 2.3590 |
| 9 | Classification: Calcium (mg/L) | Training median imputation + IQR capping + StandardScaler | Not provided | -0.3571 |
| 10 | Classification: Chloride (mg/L) | IQR capping + StandardScaler | 180.0 | 0.1215 |
| 11 | Classification: EC (µS/cm) | IQR capping + StandardScaler | 610.0 | -0.5888 |
| 12 | Classification: Hardness (mg/L) | IQR capping + StandardScaler | 280.0 | -0.2843 |
| 13 | Regression: Arsenic (mg/L) | StandardScaler | 0.015 | -0.0625 |
| 14 | Regression: Magnesium (mg/L) | Training median imputation + StandardScaler | Not provided | -0.2208 |
| 15 | Regression: Nitrate (mg/L) | StandardScaler | 22.0 | 0.8498 |
| 16 | Regression: Sodium (mg/L) | Training median imputation + StandardScaler | Not provided | -0.2626 |
| 17 | Regression: Calcium (mg/L) | Training median imputation + StandardScaler | Not provided | -0.2832 |
| 18 | Regression: Sulfate (mg/L) | StandardScaler | 130.0 | -0.2642 |
| 19 | Regression: Fluoride (mg/L) | Training median imputation + StandardScaler | Not provided | -0.2123 |
| 20 | Regression: Chloride (mg/L) | StandardScaler | 180.0 | -0.1632 |
| 21 | Regression: Resource Type_Drinking Water | One-hot encoding + StandardScaler | Surface Water | -0.1370 |
| 22 | Regression: Potassium (mg/L) | Training median imputation + StandardScaler | Not provided | -0.3572 |
| 23 | Regression: Resource Type_Tap Water | One-hot encoding + StandardScaler | Surface Water | -0.0926 |


*Missing model inputs are imputed from the corresponding model's training data. The five-year forecast is based on the historical risk-score series, not this sample alone.*

## Table 3: Classification Results

*3a. Predicted classes*

| Classification Target | Model Used | Predicted Class | Confidence (%) | Actual Class |
|---|---|:---:|:---:|:---:|
| **WQI Category** | CatBoost regression + WQI thresholds | Excellent | N/A (threshold-derived) | Not provided |
| **Water Quality Class** | Tuned Gradient Boosting | Very Poor | 97.7% | Not provided |
| **Microbial Status** | Laboratory measurement / NSDWQ rule | Contaminated | Not applicable | Contaminated |
| **Risk Category** | NSDWQ violation risk rules | Low | Rule-derived | Not provided |

*3b. Class probability distribution (primary target)*

| Class | Predicted Probability | Rank |
|---|:---:|:---:|
| **Very Poor** | 97.7% | 1 |
| **Unsuitable** | 1.1% | 2 |
| **Good** | 0.8% | 3 |
| **Excellent** | 0.4% | 4 |
| **Poor** | 0.1% | 5 |


## Table 4: WQI Regression Results

*4a. Predicted vs. actual WQI*

| Item | Value | Remark |
|---|:---:|---|
| **Regression Model Used** | CatBoost | Selected trained WQI regression model |
| **Actual WQI** | Not provided | No laboratory WQI value supplied |
| **Predicted WQI** | 23.77 | CatBoost single-sample estimate |
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
| **Predicted WQI** | 23.77 | Excellent category from predicted WQI 23.77 |
| **Water Quality Class** | Very Poor | Classifier output: Very Poor (97.7% confidence); confirm with laboratory results. |
| **Microbial Status** | Contaminated | Microbial contamination was reported. |
| **Current Risk Category** | Low | Low rule-derived risk (score 1/6) from reported NSDWQ exceedances. |
| **5-Year Risk Trend** | Stable | ARIMA population risk forecast trend over the five-year horizon: stable. |

**Summary:**

The CatBoost regression model estimates a WQI of 23.77 (Excellent). The Tuned Gradient Boosting classifier assigns Very Poor with 97.7% confidence. Reported measurements exceed these applicable limits: Microbial 1  (limit 0). The regression WQI category and classifier water-quality class differ substantially; verify both against laboratory measurements. The measured-parameter interpretation is limited because these WQI parameters were not supplied: Fluoride, Iron, Cadmium, Chromium, Mercury, Calcium, Magnesium, Sodium, Potassium, E. Coli. The five-year risk forecast is a separate population time-series forecast and is not a sample-specific prediction.

*Narrative source: Local model-based summary (Gemini request failed)*

**Conclusion:**

The models estimate WQI 23.77 (Excellent) and classify the sample as Very Poor with 97.7% confidence. These are screening estimates, not a substitute for a certified laboratory assessment.

**Key Concerns:**

Microbial (critical exceedance); Regression and classification outputs differ substantially; confirm the sample with laboratory results.

## Recommendations

| S.No. | Recommendation | Category | Priority | Timeline |
|:---:|---|---|:---:|:---:|
| 1 | Disinfect with chlorination, UV or boiling; inspect the source for sewage contamination. | Microbial | High | Immediate |


*Priority: High / Medium / Low. Timeline: Immediate / Short-term / Long-term.*

---

| **Prepared By** | **Reviewed By** | **Approved By** |
|:---:|:---:|:---:|
| Awais,Alishba,Ali | Alina_Baber | Not assigned |
| *Name / Signature / Date* | *Name / Signature / Date* | *Name / Signature / Date* |

### Data completeness
No measurement was supplied for these WQI parameters: Fluoride, Iron, Cadmium, Chromium, Mercury, Calcium, Magnesium, Sodium, Potassium, E. Coli. Model features not supplied were imputed using training-data medians; see Table 2.