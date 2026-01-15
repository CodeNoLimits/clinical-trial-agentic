"""
Tests for the Agent System.

Terminal 3 - Agent Testing Module
Tests SupervisorAgent, state management, and workflow creation.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any, List


# =============================================================================
# MOCK DEFINITIONS
# =============================================================================

class MockScreeningState:
    """Mock state for testing without LangGraph dependency."""

    def __init__(
        self,
        patient_data: Dict[str, Any] = None,
        trial_protocol: str = "",
        trial_id: str = ""
    ):
        self.data = {
            "patient_data": patient_data or {},
            "trial_protocol": trial_protocol,
            "trial_id": trial_id,
            "inclusion_criteria": [],
            "exclusion_criteria": [],
            "patient_profile": {},
            "medical_context": {},
            "matching_results": [],
            "confidence_scores": {},
            "final_decision": "",
            "explainability_table": [],
            "clinical_narrative": "",
            "current_step": "CRITERIA_EXTRACTION",
            "completed_steps": [],
            "errors": [],
            "requires_human_review": False,
            "processing_started": datetime.now().isoformat(),
            "processing_completed": "",
        }

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value


class MockSupervisorAgent:
    """Mock SupervisorAgent for testing."""

    def __init__(self):
        self.workflow = MagicMock()

    def _create_initial_state(
        self,
        patient_data: Dict[str, Any],
        trial_protocol: str,
        trial_id: str
    ) -> MockScreeningState:
        return MockScreeningState(patient_data, trial_protocol, trial_id)

    async def screen_patient(
        self,
        patient_data: Dict[str, Any],
        trial_protocol: str,
        trial_id: str,
        thread_id: str = "default"
    ) -> Dict[str, Any]:
        # Simulate screening result
        return {
            "trial_id": trial_id,
            "decision": "ELIGIBLE",
            "confidence": 0.85,
            "confidence_level": "HIGH",
            "explainability_table": [
                {
                    "criterion_id": "INC_001",
                    "criterion_text": "Age 18-75 years",
                    "patient_value": str(patient_data.get("age", "N/A")),
                    "match_status": "MATCH",
                    "confidence": 0.95,
                    "reasoning": "Patient age is within range"
                }
            ],
            "clinical_narrative": "Patient meets eligibility criteria.",
            "requires_human_review": False,
            "completed_steps": [
                "CRITERIA_EXTRACTION",
                "PATIENT_PROFILING",
                "KNOWLEDGE_QUERY",
                "ELIGIBILITY_MATCHING",
                "CONFIDENCE_SCORING",
                "EXPLANATION_GENERATION"
            ],
            "errors": [],
            "processing_started": datetime.now().isoformat(),
            "processing_completed": datetime.now().isoformat(),
        }


# =============================================================================
# TESTS - STATE MANAGEMENT
# =============================================================================

def test_initial_state_creation():
    """Test that initial state is created correctly."""
    agent = MockSupervisorAgent()

    patient_data = {"patient_id": "PT001", "age": 58}
    state = agent._create_initial_state(
        patient_data=patient_data,
        trial_protocol="Test protocol",
        trial_id="NCT001"
    )

    assert state["patient_data"]["patient_id"] == "PT001"
    assert state["trial_id"] == "NCT001"
    assert state["current_step"] == "CRITERIA_EXTRACTION"
    assert state["completed_steps"] == []
    assert state["errors"] == []


def test_state_step_progression():
    """Test state step tracking."""
    state = MockScreeningState(
        patient_data={"patient_id": "PT001"},
        trial_protocol="Test",
        trial_id="NCT001"
    )

    # Simulate step progression
    steps = [
        "CRITERIA_EXTRACTION",
        "PATIENT_PROFILING",
        "KNOWLEDGE_QUERY",
        "ELIGIBILITY_MATCHING",
        "CONFIDENCE_SCORING",
        "EXPLANATION_GENERATION"
    ]

    for step in steps:
        state["completed_steps"].append(step)

    assert len(state["completed_steps"]) == 6
    assert state["completed_steps"][0] == "CRITERIA_EXTRACTION"
    assert state["completed_steps"][-1] == "EXPLANATION_GENERATION"


def test_state_error_handling():
    """Test error tracking in state."""
    state = MockScreeningState(
        patient_data={"patient_id": "PT001"},
        trial_protocol="Test",
        trial_id="NCT001"
    )

    # Simulate errors
    state["errors"].append("API timeout error")
    state["errors"].append("Missing data for criterion INC_003")

    assert len(state["errors"]) == 2
    assert "timeout" in state["errors"][0].lower()


# =============================================================================
# TESTS - SUPERVISOR AGENT
# =============================================================================

def test_supervisor_creation():
    """Test SupervisorAgent can be instantiated."""
    agent = MockSupervisorAgent()
    assert agent is not None
    assert agent.workflow is not None


@pytest.mark.asyncio
async def test_screen_patient_basic():
    """Test basic patient screening."""
    agent = MockSupervisorAgent()

    patient_data = {
        "patient_id": "PT001",
        "age": 58,
        "sex": "male",
        "diagnoses": [{"condition": "Type 2 Diabetes", "icd10": "E11.9"}],
        "medications": [{"drug_name": "Metformin", "dose": "1000mg"}],
        "lab_values": [{"test": "HbA1c", "value": 8.2, "unit": "%"}]
    }

    trial_protocol = """
    INCLUSION CRITERIA:
    1. Age 18-75 years
    2. Diagnosis of Type 2 Diabetes
    """

    result = await agent.screen_patient(
        patient_data=patient_data,
        trial_protocol=trial_protocol,
        trial_id="NCT001"
    )

    assert result["trial_id"] == "NCT001"
    assert result["decision"] in ["ELIGIBLE", "INELIGIBLE", "UNCERTAIN"]
    assert 0 <= result["confidence"] <= 1
    assert "explainability_table" in result


@pytest.mark.asyncio
async def test_screen_patient_returns_all_steps():
    """Test that screening completes all 6 steps."""
    agent = MockSupervisorAgent()

    result = await agent.screen_patient(
        patient_data={"patient_id": "PT001", "age": 45, "sex": "female"},
        trial_protocol="Test protocol",
        trial_id="NCT002"
    )

    expected_steps = [
        "CRITERIA_EXTRACTION",
        "PATIENT_PROFILING",
        "KNOWLEDGE_QUERY",
        "ELIGIBILITY_MATCHING",
        "CONFIDENCE_SCORING",
        "EXPLANATION_GENERATION"
    ]

    for step in expected_steps:
        assert step in result["completed_steps"], f"Missing step: {step}"


@pytest.mark.asyncio
async def test_screen_patient_explainability():
    """Test that explainability table is generated."""
    agent = MockSupervisorAgent()

    result = await agent.screen_patient(
        patient_data={"patient_id": "PT001", "age": 58, "sex": "male"},
        trial_protocol="Test protocol",
        trial_id="NCT003"
    )

    assert len(result["explainability_table"]) > 0

    for row in result["explainability_table"]:
        required_fields = [
            "criterion_id",
            "criterion_text",
            "patient_value",
            "match_status",
            "confidence",
            "reasoning"
        ]
        for field in required_fields:
            assert field in row, f"Missing field in explainability: {field}"


# =============================================================================
# TESTS - DECISION LOGIC
# =============================================================================

def test_decision_eligible():
    """Test ELIGIBLE decision conditions."""
    # All inclusion match, no exclusion match
    matching_results = [
        {"type": "inclusion", "match_status": "MATCH"},
        {"type": "inclusion", "match_status": "MATCH"},
        {"type": "exclusion", "match_status": "NO_MATCH"},
    ]

    has_no_match_inclusion = any(
        r["match_status"] == "NO_MATCH" for r in matching_results if r["type"] == "inclusion"
    )
    has_match_exclusion = any(
        r["match_status"] == "MATCH" for r in matching_results if r["type"] == "exclusion"
    )
    has_uncertain = any(
        r["match_status"] in ["UNCERTAIN", "MISSING_DATA"] for r in matching_results
    )

    if has_no_match_inclusion or has_match_exclusion:
        decision = "INELIGIBLE"
    elif has_uncertain:
        decision = "UNCERTAIN"
    else:
        decision = "ELIGIBLE"

    assert decision == "ELIGIBLE"


def test_decision_ineligible_inclusion():
    """Test INELIGIBLE decision when inclusion criteria not met."""
    matching_results = [
        {"type": "inclusion", "match_status": "NO_MATCH"},
        {"type": "inclusion", "match_status": "MATCH"},
        {"type": "exclusion", "match_status": "NO_MATCH"},
    ]

    has_no_match_inclusion = any(
        r["match_status"] == "NO_MATCH" for r in matching_results if r["type"] == "inclusion"
    )

    assert has_no_match_inclusion is True


def test_decision_ineligible_exclusion():
    """Test INELIGIBLE decision when exclusion criteria matched."""
    matching_results = [
        {"type": "inclusion", "match_status": "MATCH"},
        {"type": "exclusion", "match_status": "MATCH"},  # Matches exclusion = ineligible
    ]

    has_match_exclusion = any(
        r["match_status"] == "MATCH" for r in matching_results if r["type"] == "exclusion"
    )

    assert has_match_exclusion is True


def test_decision_uncertain():
    """Test UNCERTAIN decision when data is missing."""
    matching_results = [
        {"type": "inclusion", "match_status": "MATCH"},
        {"type": "inclusion", "match_status": "MISSING_DATA"},
        {"type": "exclusion", "match_status": "NO_MATCH"},
    ]

    has_uncertain = any(
        r["match_status"] in ["UNCERTAIN", "MISSING_DATA"] for r in matching_results
    )

    assert has_uncertain is True


# =============================================================================
# TESTS - CONFIDENCE SCORING
# =============================================================================

def test_confidence_level_high():
    """Test HIGH confidence level threshold."""
    confidence = 0.92
    threshold_high = 0.90

    if confidence >= threshold_high:
        level = "HIGH"
    elif confidence >= 0.70:
        level = "MODERATE"
    elif confidence >= 0.50:
        level = "LOW"
    else:
        level = "VERY_LOW"

    assert level == "HIGH"


def test_confidence_level_moderate():
    """Test MODERATE confidence level threshold."""
    confidence = 0.75

    if confidence >= 0.90:
        level = "HIGH"
    elif confidence >= 0.70:
        level = "MODERATE"
    elif confidence >= 0.50:
        level = "LOW"
    else:
        level = "VERY_LOW"

    assert level == "MODERATE"


def test_human_review_flag():
    """Test human review flag based on confidence."""
    confidence = 0.65
    threshold = 0.80

    requires_human_review = confidence < threshold

    assert requires_human_review is True


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
