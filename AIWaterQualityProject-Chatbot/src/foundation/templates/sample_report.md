*Water Quality Analysis & Prediction Report* — *Single Sample Test Report*

---

# WATER QUALITY TEST REPORT

**Machine Learning–Based Classification, WQI Regression & 5-Year Risk Forecast**

## Sample Information

| | | | |
|---|---|---|---|
| **Sample ID** | {{ sample_id }} | **Sampling Date** | {{ sampling_date }} |
| **Province** | {{ province }} | **City** | {{ city }} |
| **Resource Type** | {{ resource_type }} | **Sampling Location** | {{ sampling_location }} |
| **Collected By** | {{ collected_by }} | **Report Date** | {{ report_date }} |
| **Laboratory** | {{ laboratory }} | **Report No.** | {{ report_no }} |

## Table 1: Input Features (Raw Sample Measurements)

*Enter laboratory-measured values for the single sample. Remark: Within / Exceeds permissible limit.*

| S.No. | Parameter | Unit | Measured Value | Permissible Limit | Remark |
|:---:|---|:---:|:---:|:---:|:---:|
{% for p in input_features %}| {{ loop.index }} | {{ p.parameter }} | {{ p.unit }} | {{ p.value }} | {{ p.limit }} | {{ p.remark }} |
{% endfor %}

## Table 2: Feature Engineering

*Shows raw input and the corresponding engineered / transformed value for each feature.*

| S.No. | Feature | Transformation / Method Applied | Input Value | Engineered Value |
|:---:|---|---|:---:|:---:|
{% for f in feature_engineering %}| {{ loop.index }} | {{ f.feature }} | {{ f.method }} | {{ f.input_value }} | {{ f.engineered_value }} |
{% endfor %}

*Missing model inputs are imputed from the corresponding model's training data. The five-year forecast is based on the historical risk-score series, not this sample alone.*

## Table 3: Classification Results

*3a. Predicted classes*

| Classification Target | Model Used | Predicted Class | Confidence (%) | Actual Class |
|---|---|:---:|:---:|:---:|
| **WQI Category** | {{ wqi_category_model }} | {{ wqi_category }} | {{ wqi_category_confidence }} | {{ wqi_category_actual }} |
| **Water Quality Class** | {{ final_class_model }} | {{ final_class }} | {{ final_class_confidence }} | {{ final_class_actual }} |
| **Microbial Status** | {{ microbial_model }} | {{ microbial }} | {{ microbial_confidence }} | {{ microbial_actual }} |
| **Risk Category** | {{ risk_category_model }} | {{ risk_category }} | {{ risk_category_confidence }} | {{ risk_category_actual }} |

*3b. Class probability distribution (primary target)*

| Class | Predicted Probability | Rank |
|---|:---:|:---:|
{% for c in class_probabilities %}| **{{ c.class_name }}** | {{ c.probability }} | {{ c.rank }} |
{% endfor %}

## Table 4: WQI Regression Results

*4a. Predicted vs. actual WQI*

| Item | Value | Remark |
|---|:---:|---|
| **Regression Model Used** | {{ regression_model }} | {{ regression_model_remark }} |
| **Actual WQI** | {{ actual_wqi }} | {{ actual_wqi_remark }} |
| **Predicted WQI** | {{ wqi_score }} | {{ predicted_wqi_remark }} |
| **Absolute Error** | {{ absolute_error }} | {{ absolute_error_remark }} |
| **WQI Category (Predicted)** | {{ wqi_category }} | {{ wqi_category_remark }} |

*4b. Model performance metrics*

| R² Score | RMSE | MAE | MAPE (%) |
|:---:|:---:|:---:|:---:|
| {{ r2_score }} | {{ rmse }} | {{ mae }} | {{ mape }} |

## Table 5: 5-Year Risk Score Forecast

*5a. Forecasted risk score*

| Forecast Year | Forecast Period | Predicted Risk Score | Confidence Interval | Risk Category | Trend (↑ / ↓ / →) |
|---|:---:|:---:|:---:|:---:|:---:|
{% for f in forecast_values %}| **Year {{ f.year }}** | {{ f.period }} | {{ f.predicted_risk_score }} | {{ f.confidence_interval }} | {{ f.risk_category }} | {{ f.trend }} |
{% endfor %}

*5b. Forecasting model details*

| Forecasting Model | Training Period | Evaluation Metric |
|---|:---:|:---:|
| {{ forecast_model }} | {{ training_period }} | {{ forecast_metric }} |

## Summary & Conclusion

*Key findings for this sample*

| Parameter | Result | Interpretation |
|---|:---:|---|
| **Predicted WQI** | {{ wqi_score }} | {{ wqi_interpretation }} |
| **Water Quality Class** | {{ final_class }} | {{ final_class_interpretation }} |
| **Microbial Status** | {{ microbial }} | {{ microbial_interpretation }} |
| **Current Risk Category** | {{ risk_category }} | {{ risk_interpretation }} |
| **5-Year Risk Trend** | {{ risk_trend }} | {{ risk_trend_interpretation }} |

**Summary:**

{{ narrative }}

*Narrative source: {{ narrative_source }}*

**Conclusion:**

{{ conclusion }}

**Key Concerns:**

{{ key_concerns }}

## Recommendations

| S.No. | Recommendation | Category | Priority | Timeline |
|:---:|---|---|:---:|:---:|
{% for r in recommendations %}| {{ loop.index }} | {{ r.text }} | {{ r.category }} | {{ r.priority }} | {{ r.timeline }} |
{% endfor %}

*Priority: High / Medium / Low. Timeline: Immediate / Short-term / Long-term.*

---

| **Prepared By** | **Reviewed By** | **Approved By** |
|:---:|:---:|:---:|
| Awais,Alishba,Ali | Alina_Baber | {{ approved_by }} |
| *Name / Signature / Date* | *Name / Signature / Date* | *Name / Signature / Date* |