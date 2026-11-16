*Water Quality Analysis & Prediction Report* — *Single Sample Test Report*

---

# WATER QUALITY TEST REPORT

**Machine Learning–Based Classification, WQI Regression & 5-Year Risk Forecast**

## Sample Information

| | | | |
|---|---|---|---|
| **Sample ID** | TANK-01-SMP | **Sampling Date** | 2026-11-09 |
| **Province** | Punjab | **City** | Lahore |
| **Resource Type** | Groundwater | **Sampling Location** | Lahore - Tanker 01 - Lahore Central |
| **Collected By** | AquaVision Autonomous IoT Telemetry | **Report Date** | 2026-11-09 |
| **Laboratory** | National Water Quality Laboratory (Simulated) | **Report No.** | REP-20261109-B8C919 |

## Table 1: Input Features (Raw Sample Measurements)

*Enter laboratory-measured values for the single sample. Remark: Within / Exceeds permissible limit.*

| S.No. | Parameter | Unit | Measured Value | Permissible Limit | Remark |
|:---:|---|:---:|:---:|:---:|:---:|
| 1 | pH |  | 7.35 | 6.5–8.5 | Within reported limit |
| 2 | Turbidity | NTU | 2.1 | 5.0 | Within reported limit |
| 3 | TDS | mg/L | 420.0 | 1000.0 | Within reported limit |
| 4 | Chloride | mg/L | 95.0 | 250.0 | Within reported limit |
| 5 | Sulfate | mg/L | 80.0 | 250.0 | Within reported limit |
| 6 | Nitrate | mg/L | 11.5 | 50.0 | Within reported limit |
| 7 | Fluoride | mg/L | 0.7 | 1.5 | Within reported limit |
| 8 | Arsenic | mg/L | 0.008 | 0.05 | Within reported limit |
| 9 | Iron | mg/L | 0.12 | 0.3 | Within reported limit |
| 10 | Lead | mg/L | 0.004 | 0.05 | Within reported limit |
| 11 | Cadmium | mg/L | 0.0008 | 0.01 | Within reported limit |
| 12 | Chromium | mg/L | 0.01 | 0.05 | Within reported limit |
| 13 | Mercury | mg/L | 0.0004 | 0.001 | Within reported limit |
| 14 | EC | µS/cm | 480.0 | Not specified | Within reported limit |
| 15 | Hardness | mg/L | 145.0 | Not specified | Within reported limit |
| 16 | Calcium | mg/L | 38.0 | Not specified | Within reported limit |
| 17 | Magnesium | mg/L | 28.0 | Not specified | Within reported limit |
| 18 | Sodium | mg/L | 90.0 | Not specified | Within reported limit |
| 19 | Potassium | mg/L | 9.5 | Not specified | Within reported limit |
| 20 | Total Coliform | CFU/100 mL | 0.0 | 0 (absence expected) | Within reported limit |


## Table 2: Feature Engineering

*Shows raw input and the corresponding engineered / transformed value for each feature.*

| S.No. | Feature | Transformation / Method Applied | Input Value | Engineered Value |
|:---:|---|---|:---:|:---:|
| 1 | Classification: Total Coliform | IQR capping + StandardScaler | 0.0 | -0.5796 |
| 2 | Classification: Arsenic (mg/L) | IQR capping + StandardScaler | 0.008 | 1.8909 |
| 3 | Classification: TDS (mg/L) | IQR capping + StandardScaler | 420.0 | -0.6309 |
| 4 | Classification: Potassium (mg/L) | IQR capping + StandardScaler | 9.5 | -0.0697 |
| 5 | Classification: Sodium (mg/L) | IQR capping + StandardScaler | 90.0 | -0.5028 |
| 6 | Classification: Magnesium (mg/L) | IQR capping + StandardScaler | 28.0 | -0.5781 |
| 7 | Classification: Nitrate (mg/L) | IQR capping + StandardScaler | 11.5 | 0.4269 |
| 8 | Classification: Turbidity (NTU) | IQR capping + StandardScaler | 2.1 | 0.7299 |
| 9 | Classification: Calcium (mg/L) | IQR capping + StandardScaler | 38.0 | -0.7303 |
| 10 | Classification: Chloride (mg/L) | IQR capping + StandardScaler | 95.0 | -0.3803 |
| 11 | Classification: EC (µS/cm) | IQR capping + StandardScaler | 480.0 | -0.8480 |
| 12 | Classification: Hardness (mg/L) | IQR capping + StandardScaler | 145.0 | -0.9540 |
| 13 | Regression: Arsenic (mg/L) | StandardScaler | 0.008 | -0.0643 |
| 14 | Regression: Magnesium (mg/L) | StandardScaler | 28.0 | -0.2460 |
| 15 | Regression: Nitrate (mg/L) | StandardScaler | 11.5 | 0.1272 |
| 16 | Regression: Sodium (mg/L) | StandardScaler | 90.0 | -0.2746 |
| 17 | Regression: Calcium (mg/L) | StandardScaler | 38.0 | -0.3814 |
| 18 | Regression: Sulfate (mg/L) | StandardScaler | 80.0 | -0.3940 |
| 19 | Regression: Fluoride (mg/L) | StandardScaler | 0.7 | 0.4009 |
| 20 | Regression: Chloride (mg/L) | StandardScaler | 95.0 | -0.2103 |
| 21 | Regression: Resource Type_Drinking Water | One-hot encoding + StandardScaler | Groundwater | -0.1370 |
| 22 | Regression: Potassium (mg/L) | StandardScaler | 9.5 | -0.1798 |
| 23 | Regression: Resource Type_Tap Water | One-hot encoding + StandardScaler | Groundwater | -0.0926 |


*Missing model inputs are imputed from the corresponding model's training data. The five-year forecast is based on the historical risk-score series, not this sample alone.*

## Table 3: Classification Results

*3a. Predicted classes*

| Classification Target | Model Used | Predicted Class | Confidence (%) | Actual Class |
|---|---|:---:|:---:|:---:|
| **WQI Category** | CatBoost regression + WQI thresholds | Excellent | N/A (threshold-derived) | Not provided |
| **Water Quality Class** | Tuned Gradient Boosting | Good | 62.9% | Not provided |
| **Microbial Status** | Laboratory measurement / NSDWQ rule | Not detected | Not applicable | Not detected |
| **Risk Category** | NSDWQ violation risk rules | Marginally Safe | Rule-derived | Not provided |

*3b. Class probability distribution (primary target)*

| Class | Predicted Probability | Rank |
|---|:---:|:---:|
| **Good** | 62.9% | 1 |
| **Unsuitable** | 22.2% | 2 |
| **Poor** | 8.3% | 3 |
| **Excellent** | 5.8% | 4 |
| **Very Poor** | 0.8% | 5 |


## Table 4: WQI Regression Results

*4a. Predicted vs. actual WQI*

| Item | Value | Remark |
|---|:---:|---|
| **Regression Model Used** | CatBoost | Selected trained WQI regression model |
| **Actual WQI** | Not provided | No laboratory WQI value supplied |
| **Predicted WQI** | 21.59 | CatBoost single-sample estimate |
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
| **Predicted WQI** | 21.59 | Excellent category from predicted WQI 21.59 |
| **Water Quality Class** | Good | Classifier output: Good (62.9% confidence); confirm with laboratory results. |
| **Microbial Status** | Not detected | No microbial contamination was reported. |
| **Current Risk Category** | Marginally Safe | Marginally Safe rule-derived risk (score 0/6) from reported NSDWQ exceedances. |
| **5-Year Risk Trend** | Stable | ARIMA population risk forecast trend over the five-year horizon: stable. |

**Summary:**

**Water Quality Report: Tanker 01 - Lahore Central**

**Report Details**
*   **Report No:** REP-20261109-B8C919
*   **Sampling Date:** 2026-11-09
*   **Location:** Lahore - Tanker 01 - Lahore Central (Groundwater)
*   **Collection Method:** AquaVision Autonomous IoT Telemetry

**Analytical Summary**
The groundwater sample collected from Tanker 01 in Lahore Central was analyzed for physicochemical and microbial parameters. Key measurements include a pH of 7.35, TDS of 420.0 mg/L, and an Electrical Conductivity (EC) of 480.0 µS/cm. Microbial analysis confirmed that Total Coliform was not detected (0.0 CFU/100mL). No violations of National Standards for Drinking Water Quality (NSDWQ) were identified in this sample.

**Model-Based Assessment**
Water quality classification was performed using a Tuned Gradient Boosting model, which categorized the water as "Good" with a confidence level of 62.9%. The calculated Water Quality Index (WQI) is 21.59. A CatBoost regression model (R² Score: 0.883) and an ARIMA forecast model (trained on 145 monthly observations from 2013–2025) were utilized to support these findings. The overall risk score is 0, classified as "Marginally Safe."

*Note: The classification and WQI results are model estimates based on the provided feature engineering inputs.*

*Narrative source: Gemini*

**Conclusion:**

The models estimate WQI 21.59 (Excellent) and classify the sample as Good with 62.9% confidence. These are screening estimates, not a substitute for a certified laboratory assessment.

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
No measurement was supplied for these WQI parameters: E. Coli. Model features not supplied were imputed using training-data medians; see Table 2.