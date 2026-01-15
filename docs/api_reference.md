# API Reference

## Overview

The Clinical Trial Screening API provides RESTful endpoints for patient eligibility screening.

**Base URL:** `http://localhost:8000/api`

**Authentication:** JWT Bearer Token (optional, configurable)

## Endpoints

### Health Check

Check API status and dependencies.

```
GET /api/health
```

**Response:**

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "dependencies": {
    "database": "connected",
    "llm": "available",
    "embeddings": "loaded"
  }
}
```

---

### Screen Patient

Perform eligibility screening for a patient against a clinical trial.

```
POST /api/screen
```

**Request Body:**

```json
{
  "trial_id": "string",
  "patient": {
    "patient_id": "string",
    "age": "integer",
    "sex": "string (Male|Female|Other)",
    "diagnoses": ["string"],
    "medications": ["string"],
    "labs": {
      "lab_name": "number"
    },
    "medical_history": ["string"],
    "allergies": ["string"]
  },
  "options": {
    "confidence_threshold": "number (0-1)",
    "include_narrative": "boolean",
    "include_evidence": "boolean"
  }
}
```

**Response:**

```json
{
  "screening_id": "uuid",
  "trial_id": "string",
  "patient_id": "string",
  "decision": "ELIGIBLE | INELIGIBLE | UNCERTAIN",
  "confidence": {
    "score": "number (0-1)",
    "interpretation": "HIGH | MODERATE | LOW | VERY_LOW",
    "calibrated": "boolean"
  },
  "criteria_breakdown": [
    {
      "criterion_id": "string",
      "criterion_type": "INCLUSION | EXCLUSION",
      "criterion_text": "string",
      "status": "MATCH | NO_MATCH | UNCERTAIN | MISSING_DATA",
      "evidence": "string",
      "confidence": "number"
    }
  ],
  "narrative": "string",
  "recommendations": ["string"],
  "metadata": {
    "processing_time_ms": "integer",
    "model_used": "string",
    "timestamp": "ISO8601"
  }
}
```

**Status Codes:**

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Invalid request |
| 404 | Trial not found |
| 500 | Server error |

---

### List Trials

Get list of available clinical trials.

```
GET /api/trials
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status (active, completed, recruiting) |
| `condition` | string | Filter by medical condition |
| `limit` | integer | Max results (default: 50) |
| `offset` | integer | Pagination offset |

**Response:**

```json
{
  "trials": [
    {
      "trial_id": "string",
      "title": "string",
      "condition": "string",
      "status": "string",
      "phase": "string",
      "criteria_count": {
        "inclusion": "integer",
        "exclusion": "integer"
      }
    }
  ],
  "total": "integer",
  "limit": "integer",
  "offset": "integer"
}
```

---

### Get Trial Details

Get detailed information about a specific trial.

```
GET /api/trials/{trial_id}
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `trial_id` | string | Trial identifier (NCT number) |

**Response:**

```json
{
  "trial_id": "string",
  "title": "string",
  "description": "string",
  "condition": "string",
  "status": "string",
  "phase": "string",
  "sponsor": "string",
  "criteria": {
    "inclusion": [
      {
        "id": "string",
        "text": "string",
        "category": "string"
      }
    ],
    "exclusion": [
      {
        "id": "string",
        "text": "string",
        "category": "string"
      }
    ]
  },
  "metadata": {
    "created_at": "ISO8601",
    "updated_at": "ISO8601"
  }
}
```

---

### Get Screening History

Retrieve past screening results.

```
GET /api/screenings
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `patient_id` | string | Filter by patient |
| `trial_id` | string | Filter by trial |
| `decision` | string | Filter by decision |
| `from_date` | ISO8601 | Start date |
| `to_date` | ISO8601 | End date |
| `limit` | integer | Max results |

**Response:**

```json
{
  "screenings": [
    {
      "screening_id": "uuid",
      "trial_id": "string",
      "patient_id": "string",
      "decision": "string",
      "confidence": "number",
      "timestamp": "ISO8601"
    }
  ],
  "total": "integer"
}
```

---

### Get Screening Details

Get full details of a specific screening.

```
GET /api/screenings/{screening_id}
```

**Response:** Same as POST /api/screen response

---

## WebSocket API

### Real-time Screening

Connect for real-time screening updates.

```
WS /api/ws/screen
```

**Message Format (Send):**

```json
{
  "action": "screen",
  "trial_id": "string",
  "patient": { ... }
}
```

**Message Format (Receive):**

```json
{
  "type": "progress | result | error",
  "step": "string",
  "data": { ... }
}
```

**Progress Steps:**
1. `extracting_criteria`
2. `profiling_patient`
3. `retrieving_context`
4. `matching_criteria`
5. `calculating_confidence`
6. `generating_explanation`
7. `complete`

---

## Error Responses

All error responses follow this format:

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": { ... }
  }
}
```

**Error Codes:**

| Code | Description |
|------|-------------|
| `INVALID_REQUEST` | Malformed request body |
| `TRIAL_NOT_FOUND` | Trial ID does not exist |
| `PATIENT_DATA_INVALID` | Patient data validation failed |
| `LLM_ERROR` | Language model error |
| `DATABASE_ERROR` | Database connection error |
| `RATE_LIMIT` | Too many requests |

---

## Rate Limiting

| Endpoint | Limit |
|----------|-------|
| `/api/screen` | 100/hour |
| `/api/trials` | 1000/hour |
| Other | 500/hour |

**Rate Limit Headers:**

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1704067200
```

---

## Examples

### cURL

```bash
# Screen a patient
curl -X POST http://localhost:8000/api/screen \
  -H "Content-Type: application/json" \
  -d '{
    "trial_id": "NCT06864546",
    "patient": {
      "patient_id": "PT001",
      "age": 58,
      "diagnoses": ["Type 2 Diabetes"]
    }
  }'
```

### Python

```python
import requests

response = requests.post(
    "http://localhost:8000/api/screen",
    json={
        "trial_id": "NCT06864546",
        "patient": {
            "patient_id": "PT001",
            "age": 58,
            "diagnoses": ["Type 2 Diabetes"]
        }
    }
)

result = response.json()
print(f"Decision: {result['decision']}")
print(f"Confidence: {result['confidence']['score']:.0%}")
```

### JavaScript

```javascript
const response = await fetch('http://localhost:8000/api/screen', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    trial_id: 'NCT06864546',
    patient: {
      patient_id: 'PT001',
      age: 58,
      diagnoses: ['Type 2 Diabetes']
    }
  })
});

const result = await response.json();
console.log(`Decision: ${result.decision}`);
```

---

## OpenAPI Specification

Full OpenAPI 3.0 specification available at:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **JSON:** http://localhost:8000/openapi.json
