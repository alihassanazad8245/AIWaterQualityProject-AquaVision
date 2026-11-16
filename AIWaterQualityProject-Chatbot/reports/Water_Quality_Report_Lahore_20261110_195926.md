*Water Quality Analysis & Prediction Report* — *Single Sample Test Report*

---

# WATER QUALITY TEST REPORT

**Machine Learning–Based Classification, WQI Regression & 5-Year Risk Forecast**

## Sample Information

| | | | |
|---|---|---|---|
| **Sample ID** | TANK-01-SMP | **Sampling Date** | 2026-11-10 |
| **Province** | Punjab | **City** | Lahore |
| **Resource Type** | Groundwater | **Sampling Location** | Lahore - Tanker 01 - Lahore Central |
| **Collected By** | AquaVision Autonomous IoT Telemetry | **Report Date** | 2026-11-10 |
| **Laboratory** | National Water Quality Laboratory (Simulated) | **Report No.** | REP-20261110-C97866 |

## Table 1: Input Features (Raw Sample Measurements)

*Enter laboratory-measured values for the single sample. Remark: Within / Exceeds permissible limit.*

| S.No. | Parameter | Unit | Measured Value | Permissible Limit | Remark |
|:---:|---|:---:|:---:|:---:|:---:|
| 1 | pH |  | 7.35 | 6.5–8.5 | Within reported limit |
| 2 | Turbidity | NTU | 2.2 | 5.0 | Within reported limit |
| 3 | TDS | mg/L | 420.0 | 1000.0 | Within reported limit |
| 4 | Chloride | mg/L | 95.0 | 250.0 | Within reported limit |
| 5 | Sulfate | mg/L | 80.0 | 250.0 | Within reported limit |
| 6 | Nitrate | mg/L | 11.5 | 50.0 | Within reported limit |
| 7 | Arsenic | mg/L | 0.008 | 0.05 | Within reported limit |
| 8 | Lead | mg/L | 0.004 | 0.05 | Within reported limit |
| 9 | EC | µS/cm | 480.0 | Not specified | Within reported limit |
| 10 | Hardness | mg/L | 145.0 | Not specified | Within reported limit |
| 11 | Total Coliform | CFU/100 mL | 0.0 | 0 (absence expected) | Within reported limit |


## Table 2: Feature Engineering

*Shows raw input and the corresponding engineered / transformed value for each feature.*

| S.No. | Feature | Transformation / Method Applied | Input Value | Engineered Value |
|:---:|---|---|:---:|:---:|
| 1 | Classification: Total Coliform | IQR capping + StandardScaler | 0.0 | -0.5796 |
| 2 | Classification: Arsenic (mg/L) | IQR capping + StandardScaler | 0.008 | 1.8909 |
| 3 | Classification: TDS (mg/L) | IQR capping + StandardScaler | 420.0 | -0.6309 |
| 4 | Classification: Potassium (mg/L) | Training median imputation + IQR capping + StandardScaler | Not provided | -0.4060 |
| 5 | Classification: Sodium (mg/L) | Training median imputation + IQR capping + StandardScaler | Not provided | -0.4385 |
| 6 | Classification: Magnesium (mg/L) | Training median imputation + IQR capping + StandardScaler | Not provided | -0.3943 |
| 7 | Classification: Nitrate (mg/L) | IQR capping + StandardScaler | 11.5 | 0.4269 |
| 8 | Classification: Turbidity (NTU) | IQR capping + StandardScaler | 2.2 | 0.8204 |
| 9 | Classification: Calcium (mg/L) | Training median imputation + IQR capping + StandardScaler | Not provided | -0.3571 |
| 10 | Classification: Chloride (mg/L) | IQR capping + StandardScaler | 95.0 | -0.3803 |
| 11 | Classification: EC (µS/cm) | IQR capping + StandardScaler | 480.0 | -0.8480 |
| 12 | Classification: Hardness (mg/L) | IQR capping + StandardScaler | 145.0 | -0.9540 |
| 13 | Regression: Arsenic (mg/L) | StandardScaler | 0.008 | -0.0643 |
| 14 | Regression: Magnesium (mg/L) | Training median imputation + StandardScaler | Not provided | -0.2208 |
| 15 | Regression: Nitrate (mg/L) | StandardScaler | 11.5 | 0.1272 |
| 16 | Regression: Sodium (mg/L) | Training median imputation + StandardScaler | Not provided | -0.2626 |
| 17 | Regression: Calcium (mg/L) | Training median imputation + StandardScaler | Not provided | -0.2832 |
| 18 | Regression: Sulfate (mg/L) | StandardScaler | 80.0 | -0.3940 |
| 19 | Regression: Fluoride (mg/L) | Training median imputation + StandardScaler | Not provided | -0.2123 |
| 20 | Regression: Chloride (mg/L) | StandardScaler | 95.0 | -0.2103 |
| 21 | Regression: Resource Type_Drinking Water | One-hot encoding + StandardScaler | Groundwater | -0.1370 |
| 22 | Regression: Potassium (mg/L) | Training median imputation + StandardScaler | Not provided | -0.3572 |
| 23 | Regression: Resource Type_Tap Water | One-hot encoding + StandardScaler | Groundwater | -0.0926 |


*Missing model inputs are imputed from the corresponding model's training data. The five-year forecast is based on the historical risk-score series, not this sample alone.*

## Table 3: Classification Results

*3a. Predicted classes*

| Classification Target | Model Used | Predicted Class | Confidence (%) | Actual Class |
|---|---|:---:|:---:|:---:|
| **WQI Category** | CatBoost regression + WQI thresholds | Excellent | N/A (threshold-derived) | Not provided |
| **Water Quality Class** | Tuned Gradient Boosting | Good | 45.8% | Not provided |
| **Microbial Status** | Laboratory measurement / NSDWQ rule | Not detected | Not applicable | Not detected |
| **Risk Category** | NSDWQ violation risk rules | Marginally Safe | Rule-derived | Not provided |

*3b. Class probability distribution (primary target)*

| Class | Predicted Probability | Rank |
|---|:---:|:---:|
| **Good** | 45.8% | 1 |
| **Unsuitable** | 41.0% | 2 |
| **Excellent** | 8.6% | 3 |
| **Poor** | 3.7% | 4 |
| **Very Poor** | 1.0% | 5 |


## Table 4: WQI Regression Results

*4a. Predicted vs. actual WQI*

| Item | Value | Remark |
|---|:---:|---|
| **Regression Model Used** | CatBoost | Selected trained WQI regression model |
| **Actual WQI** | Not provided | No laboratory WQI value supplied |
| **Predicted WQI** | 20.96 | CatBoost single-sample estimate |
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
| **Predicted WQI** | 20.96 | Excellent category from predicted WQI 20.96 |
| **Water Quality Class** | Good | Classifier output: Good (45.8% confidence); confirm with laboratory results. |
| **Microbial Status** | Not detected | No microbial contamination was reported. |
| **Current Risk Category** | Marginally Safe | Marginally Safe rule-derived risk (score 0/6) from reported NSDWQ exceedances. |
| **5-Year Risk Trend** | Stable | ARIMA population risk forecast trend over the five-year horizon: stable. |

**Summary:**

The CatBoost regression model estimates a WQI of 20.96 (Excellent). The Tuned Gradient Boosting classifier assigns Good with 45.8% confidence. No NSDWQ exceedances were identified among the parameters reported for this sample. The measured-parameter interpretation is limited because these WQI parameters were not supplied: Fluoride, Iron, Cadmium, Chromium, Mercury, Calcium, Magnesium, Sodium, Potassium, E. Coli. The five-year risk forecast is a separate population time-series forecast and is not a sample-specific prediction.

*Narrative source: Local model-based summary (Gemini request failed)*

**Conclusion:**

The models estimate WQI 20.96 (Excellent) and classify the sample as Good with 45.8% confidence. These are screening estimates, not a substitute for a certified laboratory assessment.

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