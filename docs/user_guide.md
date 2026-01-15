# User Guide

## Getting Started

### Prerequisites

- Python 3.9+
- API key (Google Gemini or OpenAI)
- 4GB+ RAM recommended

### Installation

```bash
# Clone repository
git clone https://github.com/codenolimits/clinical-trial-agentic.git
cd clinical-trial-agentic

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: .\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Configuration

Edit `.env` file:

```env
# LLM API (choose one)
GOOGLE_API_KEY=your_gemini_key
# or
OPENAI_API_KEY=your_openai_key

# Vector Database
CHROMADB_HOST=localhost
CHROMADB_PORT=8001

# Embedding Model
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

## Using the Web Interface

### Launch

```bash
streamlit run src/ui/app.py --server.port 8501
```

Open http://localhost:8501 in your browser.

### Screening a Patient

#### Step 1: Select a Trial

Choose from available clinical trials in the dropdown menu.

#### Step 2: Enter Patient Data

**Option A: Form Input**

Fill in the form fields:
- Patient ID
- Age
- Sex
- Diagnoses (comma-separated)
- Medications (comma-separated)
- Lab values

**Option B: JSON Input**

Paste patient data in JSON format:

```json
{
  "patient_id": "PT001",
  "age": 58,
  "sex": "Male",
  "diagnoses": ["Type 2 Diabetes Mellitus"],
  "medications": ["Metformin 1000mg BID"],
  "labs": {
    "HbA1c": 8.2,
    "eGFR": 75
  }
}
```

#### Step 3: Run Screening

Click "Run Screening" button.

#### Step 4: Review Results

The system displays:

1. **Decision Banner**
   - Green: ELIGIBLE
   - Red: INELIGIBLE
   - Yellow: UNCERTAIN

2. **Confidence Score**
   - Percentage (0-100%)
   - Interpretation (High/Moderate/Low/Very Low)

3. **Criterion Breakdown**
   - Table with each criterion
   - Status per criterion
   - Evidence and notes

4. **Clinical Narrative**
   - Readable summary
   - Suitable for documentation

## Using the API

### Start the API Server

```bash
uvicorn src.api.main:app --reload --port 8000
```

### Endpoints

#### Screen a Patient

```bash
POST /api/screen
Content-Type: application/json

{
  "trial_id": "NCT06864546",
  "patient": {
    "patient_id": "PT001",
    "age": 58,
    "diagnoses": ["Type 2 Diabetes"],
    "labs": {"HbA1c": 8.2}
  }
}
```

**Response:**

```json
{
  "decision": "ELIGIBLE",
  "confidence": 0.92,
  "confidence_interpretation": "HIGH",
  "criteria_breakdown": [...],
  "narrative": "...",
  "timestamp": "2026-01-15T18:00:00Z"
}
```

#### List Trials

```bash
GET /api/trials
```

#### Get Trial Details

```bash
GET /api/trials/NCT06864546
```

### API Documentation

Interactive docs available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Interpreting Results

### Decision Types

| Decision | Meaning | Action |
|----------|---------|--------|
| ELIGIBLE | Patient meets criteria | Proceed to enrollment |
| INELIGIBLE | Patient fails criteria | Document reason |
| UNCERTAIN | Insufficient data | Human review required |

### Confidence Levels

| Level | Range | Interpretation |
|-------|-------|----------------|
| HIGH | 85-100% | Strong confidence |
| MODERATE | 70-84% | Reasonable confidence |
| LOW | 50-69% | Review recommended |
| VERY LOW | <50% | Human review required |

### Criterion Status

| Status | Meaning |
|--------|---------|
| MATCH | Patient meets criterion |
| NO_MATCH | Patient fails criterion |
| UNCERTAIN | Cannot determine |
| MISSING_DATA | Required data not available |

## Best Practices

### Patient Data Quality

1. **Complete Data**: Provide all available patient information
2. **Standardized Terms**: Use standard medical terminology
3. **Recent Labs**: Include recent laboratory values
4. **Medication List**: Include current medications with doses

### Reviewing Results

1. **Always review UNCERTAIN decisions** with a clinician
2. **Check confidence scores** - low scores indicate uncertainty
3. **Review criterion breakdown** for specific issues
4. **Use narrative** for documentation

### When to Override

The system is a decision support tool. Override when:

- Clinical context not captured in data
- Recent changes not reflected
- Edge cases requiring clinical judgment

## Troubleshooting

### Common Issues

**"API key not found"**
- Check `.env` file exists
- Verify API key is correct

**"No trials available"**
- Run database initialization: `python src/database/init_db.py`
- Ingest trial data: `python src/database/ingest_trials.py`

**"Screening timeout"**
- Check LLM API connectivity
- Reduce patient data complexity

**"Low confidence scores"**
- Provide more complete patient data
- Check for ambiguous diagnoses

### Getting Help

- Check logs: `logs/screening.log`
- API health: `GET /api/health`
- Contact support team

## Example Workflow

### Scenario: Diabetes Trial Screening

1. **Receive patient referral** for diabetes trial

2. **Gather patient data**:
   ```json
   {
     "patient_id": "PT001",
     "age": 58,
     "diagnoses": ["Type 2 Diabetes Mellitus", "Hypertension"],
     "medications": ["Metformin 1000mg BID", "Lisinopril 10mg QD"],
     "labs": {"HbA1c": 8.2, "eGFR": 75, "ALT": 28}
   }
   ```

3. **Run screening** via UI or API

4. **Review result**:
   - Decision: ELIGIBLE (92% confidence)
   - All inclusion criteria met
   - No exclusion criteria triggered

5. **Document** using generated narrative

6. **Proceed** with enrollment process
