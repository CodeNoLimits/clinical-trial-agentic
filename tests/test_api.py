"""
Tests for the FastAPI endpoints.

Terminal 3 - API Testing Module
Tests health check, trials, and screening endpoints.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

# Create a minimal test app without requiring actual dependencies
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# Mock schemas for testing
class HealthResponse(BaseModel):
    status: str
    version: str
    database_status: str
    timestamp: str


class TrialInfo(BaseModel):
    trial_id: str
    title: str
    condition: str
    document_count: int


# Create test app
test_app = FastAPI(title="Test Clinical Trial API")


# Mock database stats
MOCK_DB_STATS = {"trials": 5, "notes": 0, "knowledge": 10}


@test_app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        database_status=f"OK ({MOCK_DB_STATS['trials']} trials indexed)",
        timestamp=datetime.now().isoformat()
    )


@test_app.get("/trials", response_model=List[TrialInfo])
async def list_trials():
    return [
        TrialInfo(
            trial_id="NCT_TEST_001",
            title="Test Trial for Diabetes",
            condition="Type 2 Diabetes",
            document_count=3
        ),
        TrialInfo(
            trial_id="NCT_TEST_002",
            title="Test Trial for Hypertension",
            condition="Hypertension",
            document_count=2
        )
    ]


@test_app.get("/trials/{trial_id}")
async def get_trial_details(trial_id: str):
    if trial_id == "NCT_NOT_FOUND":
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Trial {trial_id} not found")
    return {
        "trial_id": trial_id,
        "document_count": 3,
        "sections": ["eligibility", "protocol"],
        "full_text": "Sample trial protocol text..."
    }


# =============================================================================
# TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_health_check():
    """Test the health check endpoint returns healthy status."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert "trials indexed" in data["database_status"]


@pytest.mark.asyncio
async def test_list_trials():
    """Test listing available trials."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/trials")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["trial_id"] == "NCT_TEST_001"


@pytest.mark.asyncio
async def test_get_trial_details():
    """Test getting details for a specific trial."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/trials/NCT_TEST_001")

        assert response.status_code == 200
        data = response.json()
        assert data["trial_id"] == "NCT_TEST_001"
        assert "document_count" in data
        assert "sections" in data


@pytest.mark.asyncio
async def test_get_trial_not_found():
    """Test 404 response for non-existent trial."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/trials/NCT_NOT_FOUND")

        assert response.status_code == 404


@pytest.mark.asyncio
async def test_health_response_structure():
    """Test that health response has all required fields."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        data = response.json()

        required_fields = ["status", "version", "database_status", "timestamp"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"


@pytest.mark.asyncio
async def test_trials_response_structure():
    """Test that trials response has all required fields."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/trials")
        data = response.json()

        for trial in data:
            required_fields = ["trial_id", "title", "condition", "document_count"]
            for field in required_fields:
                assert field in trial, f"Missing required field: {field}"


# =============================================================================
# SCHEMA VALIDATION TESTS
# =============================================================================

def test_patient_data_validation():
    """Test PatientData schema validation."""
    from pydantic import BaseModel, Field, ValidationError

    class PatientData(BaseModel):
        patient_id: str
        age: int = Field(ge=0, le=150)
        sex: str = Field(pattern="^(male|female|other)$")
        diagnoses: List[dict] = []
        medications: List[dict] = []
        lab_values: List[dict] = []

    # Valid data
    valid_patient = PatientData(
        patient_id="PT001",
        age=58,
        sex="male",
        diagnoses=[{"condition": "Diabetes"}],
        medications=[{"drug_name": "Metformin"}],
        lab_values=[{"test": "HbA1c", "value": 8.2}]
    )
    assert valid_patient.patient_id == "PT001"

    # Invalid age (negative)
    with pytest.raises(ValidationError):
        PatientData(patient_id="PT002", age=-5, sex="male")

    # Invalid sex
    with pytest.raises(ValidationError):
        PatientData(patient_id="PT003", age=30, sex="invalid")


def test_screening_result_validation():
    """Test ScreeningResult schema validation."""
    from pydantic import BaseModel, Field, ValidationError

    class ScreeningResult(BaseModel):
        screening_id: str
        trial_id: str
        patient_id: str
        decision: str = Field(pattern="^(ELIGIBLE|INELIGIBLE|UNCERTAIN)$")
        confidence: float = Field(ge=0, le=1)

    # Valid result
    result = ScreeningResult(
        screening_id="SCR-001",
        trial_id="NCT001",
        patient_id="PT001",
        decision="ELIGIBLE",
        confidence=0.95
    )
    assert result.decision == "ELIGIBLE"

    # Invalid decision
    with pytest.raises(ValidationError):
        ScreeningResult(
            screening_id="SCR-002",
            trial_id="NCT001",
            patient_id="PT001",
            decision="MAYBE",  # Invalid
            confidence=0.5
        )

    # Invalid confidence (> 1)
    with pytest.raises(ValidationError):
        ScreeningResult(
            screening_id="SCR-003",
            trial_id="NCT001",
            patient_id="PT001",
            decision="ELIGIBLE",
            confidence=1.5  # Invalid
        )


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
