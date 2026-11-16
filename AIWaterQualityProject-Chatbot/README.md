
# AI Water Quality Chatbot

An AI-powered water quality analysis system for Pakistan, combining conversational AI, Retrieval-Augmented Generation (RAG), pre-trained machine learning models, dataset analysis, and automated report generation.

The system helps users understand water quality parameters, evaluate them against WHO and Pakistan National Standards for Drinking Water Quality (NSDWQ), explore dataset insights, obtain ML-based predictions, and generate detailed water quality reports.

> **Project Scope:** This repository focuses on the standalone AI chatbot and report-generation agents. The classification, WQI regression, and forecasting models were developed previously. This project integrates these existing trained models without retraining them.

---

## Project Maintainer

**Ali Hassan Azad**

GitHub: [@alihassanazad245](https://github.com/alihassanazad245)

---

## Features

### 1. AI Water Quality Chatbot

Ask questions in natural language and receive intelligent, context-aware responses.

The chatbot automatically routes questions through different workflows:

| Workflow | Purpose |
|---|---|
| Report-aware Chat | Answers follow-up questions using previously generated reports. |
| Tool / Hybrid | Uses trained ML models to analyse actual water-quality measurements. |
| RAG | Retrieves relevant WHO / NSDWQ standards and methodology information. |

The chatbot uses four main information sources:

- **Standards RAG:** WHO and Pakistan NSDWQ water-quality limits.
- **Methodology RAG:** WQI calculations, labelling rules, risk scores, and methodology rules.
- **Dataset Analysis:** Statistical insights, averages, rankings, class distributions, and limit exceedances.
- **ML Predictions:** Predictions from existing classification, regression, and forecasting models.

### 2. Automated Water Quality Report Generation

The report-generation agent creates structured Markdown (`.md`) and Word (`.docx`) reports for water samples.

Reports include:

- Sample information and input parameters.
- Input features compared with relevant standards.
- Feature engineering details.
- Water-quality classification and class probabilities.
- WQI regression results.
- Five-year risk-score forecasting.
- Summary and conclusion.
- Prioritised recommendations for NSDWQ violations.

### 3. Report-Aware Follow-up Questions

After generating a report, users can continue the conversation and ask questions about its contents.

For example, the chatbot can retrieve the reported pH value, explain classification results, or answer questions directly using the generated report.

---

## Example Questions

Try asking the chatbot questions like:

```text
What are the health risks of drinking groundwater
with high nitrate levels for children?

What is the WHO limit for arsenic?

How is Water_Quality_Class derived from the
penalties in Table 1?

What is the average arsenic and TDS in Lahore?

How many groundwater samples are classified
as Very Poor?

Which cities have the highest mean arsenic?

Predict the water quality for pH 7.2, TDS 450,
Nitrate 12 and Arsenic 0.01.

Generate a water quality report for a new sample.
```

---

## System Architecture

The application uses two LangGraph-based agents: a chatbot agent and a report-generation agent.

Both agents connect to a shared model-inference layer that provides access to the existing trained ML models.

```text
                      python src/main.py
                              |
             +----------------+----------------+
             |                                 |
       CHATBOT AGENT                      REPORT AGENT
        (LangGraph)                        (LangGraph)
             |                                 |
      Question Router                    Request Parsing
             |                                 |
     +-------+--------+                   Data Fetching
     |       |        |                        |
   Report  Tool /    RAG                 Template Selection
  Context  Hybrid     |                        |
     |       |    Standards +              Narrative Draft
 Report Q&A ML    Methodology                    |
             |        |                      QA Check
             |   Dataset Facts                   |
             |        |                     Export MD + DOCX
             +--------+
                  |
           Shared ModelRunner
                  |
       +----------+----------+
       |          |          |
 Classification Regression Forecasting
     Model       Model       Model
```

---

## Pre-trained Machine Learning Models

The following models are integrated into the system. They were developed previously and are not retrained by this application.

| Task | Model File | Description |
|---|---|---|
| Water Quality Classification | `Classification/Models/final_model.pkl` | Tuned Gradient Boosting model with Random Forest and Decision Tree fallbacks. |
| WQI Prediction | `Regression/Models/catboost_initial.pkl` | CatBoost regression model. |
| Risk Score Forecasting | `Forecasting/Models/arima_model.pkl` | Population-level risk forecast, not a sample-specific prediction. |

---

## Knowledge Base & ChromaDB

The system uses ChromaDB for storing and retrieving relevant information.

| Collection | Content |
|---|---|
| `water_standards` | WHO and Pakistan NSDWQ parameter limits. |
| `methodology_rules` | Methodology PDF content, including WQI rules and Table 1. |
| `query_cache_<hash>` | Cached query embeddings for individual embedding models. |

The default embedding model is:

`models/gemini-embedding-001`

It can be customised using the `EMBEDDING_MODEL` environment variable.

---

## Installation & Setup

### Requirements

- Python 3.10 or later.
- Google Gemini API key.
- Dependencies listed in `requirements.txt`.

### 1. Clone the Repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd AI-Water-Quality-Chatbot
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root directory.

```env
GOOGLE_API_KEY=your_api_key_here
```

Alternatively, you can use `GEMINI_API_KEY` as the environment variable name.

**Important:** Never upload your `.env` file or expose your API key publicly.

### 4. Build the Vector Database

Run the following commands during the initial setup or whenever the source documents change.

```bash
# Ingest WHO and Pakistan NSDWQ standards
python src/main.py --ingest

# Ingest methodology PDF rules and Table 1
python src/main.py --ingest-pdf

# Ingest both sources
python src/main.py --ingest-all
```

To preview methodology PDF chunks without an API key:

```bash
python -m src.foundation.pdf_rag --preview
```

---

## Usage

### Start Interactive Chatbot

```bash
python src/main.py --chat
```

### Start Chatbot with an Initial Question

```bash
python src/main.py --chat "What is the WHO limit for arsenic?"
```

### Generate a Water Quality Report

```bash
python src/main.py
```

The default command asks for a report request. Press Enter to use the built-in demo sample.

### Generate a Report Using a Single Command

```bash
python src/main.py --report "Generate a report for Lahore groundwater: pH 7.2, TDS 450, Arsenic 0.01"
```

### Run Combined Demo

```bash
python src/main.py --all
```

To exit interactive chat, type:

```text
exit
```

or

```text
quit
```

**Data Handling:** Missing input parameters are never invented. Missing model inputs are imputed using training-data information and displayed in the feature-engineering table. Missing sample metadata is reported as `Not provided`.

---

## Configuration

The following environment variables can be used to customise the Gemini and embedding configuration.

| Variable | Default | Purpose |
|---|---|---|
| `GEMINI_MODEL` | `gemini-3.8-flash` | Primary chat and report-generation model. |
| `GEMINI_FALLBACK_MODELS` | `gemini-3.6-flash,gemini-3.1-flash-lite` | Ordered fallback models for transient errors. |
| `GEMINI_FALLBACK_MODEL` | None | Legacy single-fallback setting. |
| `EMBEDDING_MODEL` | `models/gemini-embedding-001` | Embedding model used by ChromaDB. |

---

## Reliability & Safety

- **Gemini Model Failover:** Automatically attempts configured fallback models when transient errors occur, including timeouts, rate limits, server errors, and empty responses.
- **Graceful Degradation:** If AI generation is unavailable, the chatbot can still return retrieved standards, methodology, and dataset information where available.
- **Report Generation Fallback:** Uses a local model-based summary when Gemini report generation fails.
- **API Key Protection:** Sensitive API keys are redacted from user-facing error messages.
- **Retrieval Fallback:** If the methodology collection has not been ingested, the system reports the limitation and continues using other available information sources.

---

## Testing

Run the automated chatbot workflow tests:

```bash
python -m unittest tests.test_chatbot_workflows
```

The test suite includes 16 tests covering:

- Model selection and failover.
- Error-message redaction.
- Retrieval fallback behaviour.
- Report-grounded follow-up answers.
- Report-generation fallback behaviour.

---

## Project Structure

```text
.
├── src/
│   ├── main.py
│   ├── agents/
│   │   ├── chatbot/
│   │   │   └── Chatbot workflows, routing,
│   │   │       retrieval, dataset and generation
│   │   └── reporter/
│   │       └── Report generation, parsing,
│   │           QA and document export
│   └── foundation/
│       ├── inference.py
│       ├── vector_store.py
│       ├── pdf_rag.py
│       ├── dataset.py
│       ├── rules.py
│       └── templates/
│
├── Data/
│   └── Standards/
│
├── chroma_db/
├── reports/
├── tests/
│
├── Classification/
├── Regression/
├── Forecasting/
│
├── GeminiUtils/
├── MODEL_AND_AGENT_CONNECTION.txt
└── requirements.txt
```

---

## Related Project

### AI Water Quality – AquaVision

This repository is part of the broader AI-based Water Quality project.

The related **AI-Water-Quality-AquaVision** repository contains the integrated application, combining frontend, backend, and chatbot functionality.

While this repository focuses on the standalone AI chatbot and report-generation system, AquaVision provides the broader integrated application experience.

---

## Author

**Ali Hassan Azad**

GitHub: [@alihassanazad245](https://github.com/alihassanazad245)

*Building AI-powered solutions for smarter water quality analysis.*
