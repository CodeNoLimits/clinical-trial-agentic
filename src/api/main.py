"""
FastAPI Application - Clinical Trial Screening API

Main entry point for the REST API providing:
- POST /screen - Screen a patient for trial eligibility
- GET /trials - List available trials
- GET /results/{id} - Get screening results
- GET /health - Health check endpoint
"""

import os
from typing import List, Optional
from datetime import datetime
from contextlib import asynccontextmanager

# Load environment variables FIRST - before any other imports
from pathlib import Path
from dotenv import load_dotenv

# Find .env file relative to this file (project root)
_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)
else:
    load_dotenv()  # Try default locations

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from ..agents.supervisor import SupervisorAgent
from ..database.chromadb_client import ChromaDBClient


# =============================================================================
# PYDANTIC SCHEMAS
# =============================================================================

class PatientData(BaseModel):
    """Patient data input schema."""
    patient_id: str = Field(..., description="Unique patient identifier")
    age: int = Field(..., ge=0, le=150, description="Patient age in years")
    sex: str = Field(..., pattern="^(male|female|other)$", description="Patient sex")
    diagnoses: List[dict] = Field(default=[], description="List of diagnoses")
    medications: List[dict] = Field(default=[], description="Current medications")
    lab_values: List[dict] = Field(default=[], description="Laboratory values")
    medical_history: List[str] = Field(default=[], description="Medical history items")
    lifestyle: dict = Field(default={}, description="Lifestyle factors")


class ScreeningRequest(BaseModel):
    """Screening request schema."""
    patient: PatientData
    trial_id: str = Field(..., description="Trial ID to screen against")
    trial_protocol: Optional[str] = Field(None, description="Optional custom protocol text")


class CriterionResult(BaseModel):
    """Single criterion matching result."""
    criterion_id: str
    criterion_text: str
    patient_value: str
    match_status: str
    confidence: float
    reasoning: str


class ScreeningResult(BaseModel):
    """Screening result schema."""
    screening_id: str
    trial_id: str
    patient_id: str
    decision: str = Field(..., pattern="^(ELIGIBLE|INELIGIBLE|UNCERTAIN)$")
    confidence: float = Field(..., ge=0, le=1)
    confidence_level: str
    requires_human_review: bool
    explainability_table: List[CriterionResult]
    clinical_narrative: str
    processing_time_ms: int
    timestamp: str


class TrialInfo(BaseModel):
    """Trial information schema."""
    trial_id: str
    title: str
    condition: str
    document_count: int


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    database_status: str
    timestamp: str


# =============================================================================
# APPLICATION SETUP
# =============================================================================

# Store for screening results (in production, use a proper database)
_results_store: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print("Starting Clinical Trial Screening API...")
    app.state.agent = SupervisorAgent()
    app.state.db = ChromaDBClient()
    print("API ready!")

    yield

    # Shutdown
    print("Shutting down...")


app = FastAPI(
    title="Clinical Trial Eligibility Screening API",
    description="""
    AI-powered clinical trial eligibility screening system using RAG and multi-agent architecture.

    ## Features
    - Patient eligibility screening against trial protocols
    - Explainable AI decisions with confidence scoring
    - FDA/EMA compliant audit trails

    ## Architecture
    - LangGraph-based supervisor agent with 6 screening steps
    - ChromaDB vector database with hybrid RAG retrieval
    - Self-consistency confidence scoring

    ## Authors
    Meléa & David (CodeNoLimits)
    """,
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:8501").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# ENDPOINTS
# =============================================================================

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Returns system status including database connectivity.
    """
    try:
        db_stats = app.state.db.get_collection_stats()
        db_status = f"OK ({db_stats['trials']} trials indexed)"
    except Exception as e:
        db_status = f"Error: {str(e)}"

    return HealthResponse(
        status="healthy",
        version="1.0.0",
        database_status=db_status,
        timestamp=datetime.now().isoformat()
    )


@app.post("/screen", response_model=ScreeningResult, tags=["Screening"])
async def screen_patient(
    request: ScreeningRequest,
    background_tasks: BackgroundTasks
):
    """
    Screen a patient for clinical trial eligibility.

    This endpoint runs the full 6-step screening workflow:
    1. Extract eligibility criteria from trial protocol
    2. Analyze patient profile
    3. Query RAG for medical context
    4. Match patient to criteria
    5. Calculate confidence score
    6. Generate AI explainability table

    Returns:
        ScreeningResult with decision, confidence, and explainability
    """
    start_time = datetime.now()

    # Get trial protocol
    if request.trial_protocol:
        protocol = request.trial_protocol
    else:
        # Retrieve from database
        trial_docs = app.state.db.get_trial_by_id(request.trial_id)
        if not trial_docs.get("documents"):
            raise HTTPException(
                status_code=404,
                detail=f"Trial {request.trial_id} not found in database"
            )
        protocol = "\n\n".join(trial_docs["documents"])

    # Run screening
    try:
        result = await app.state.agent.screen_patient(
            patient_data=request.patient.model_dump(),
            trial_protocol=protocol,
            trial_id=request.trial_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Screening failed: {str(e)}"
        )

    # Calculate processing time
    processing_time = int((datetime.now() - start_time).total_seconds() * 1000)

    # Generate screening ID
    screening_id = f"SCR-{datetime.now().strftime('%Y%m%d%H%M%S')}-{request.patient.patient_id}"

    # Format result
    screening_result = ScreeningResult(
        screening_id=screening_id,
        trial_id=request.trial_id,
        patient_id=request.patient.patient_id,
        decision=result.get("decision", "UNCERTAIN"),
        confidence=result.get("confidence", 0.0),
        confidence_level=result.get("confidence_level", "UNKNOWN"),
        requires_human_review=result.get("requires_human_review", True),
        explainability_table=[
            CriterionResult(
                criterion_id=row.get("criterion_id", ""),
                criterion_text=row.get("criterion_text", ""),
                patient_value=str(row.get("patient_value", "")),
                match_status=row.get("match_status", "UNKNOWN"),
                confidence=row.get("confidence", 0.0),
                reasoning=row.get("reasoning", "")
            )
            for row in result.get("explainability_table", [])
        ],
        clinical_narrative=result.get("clinical_narrative", ""),
        processing_time_ms=processing_time,
        timestamp=datetime.now().isoformat()
    )

    # Store result (background task in production)
    _results_store[screening_id] = screening_result.model_dump()

    return screening_result


@app.get("/screen/{screening_id}", response_model=ScreeningResult, tags=["Screening"])
async def get_screening_result(screening_id: str):
    """
    Retrieve a previous screening result by ID.

    Args:
        screening_id: The screening ID returned from POST /screen
    """
    if screening_id not in _results_store:
        raise HTTPException(
            status_code=404,
            detail=f"Screening result {screening_id} not found"
        )

    return ScreeningResult(**_results_store[screening_id])


@app.get("/trials", response_model=List[TrialInfo], tags=["Trials"])
async def list_trials():
    """
    List all clinical trials in the database.

    Returns:
        List of trial information including ID, title, and document count
    """
    try:
        # Get all unique trial IDs from the collection
        results = app.state.db.trials.get(include=["metadatas"])

        trials = {}
        for metadata in results.get("metadatas", []):
            if metadata:
                trial_id = metadata.get("trial_id", "unknown")
                if trial_id not in trials:
                    trials[trial_id] = {
                        "trial_id": trial_id,
                        "title": metadata.get("title", ""),
                        "condition": metadata.get("condition", ""),
                        "document_count": 1
                    }
                else:
                    trials[trial_id]["document_count"] += 1

        return [TrialInfo(**info) for info in trials.values()]

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving trials: {str(e)}"
        )


@app.get("/trials/{trial_id}", tags=["Trials"])
async def get_trial_details(trial_id: str):
    """
    Get detailed information about a specific trial.

    Args:
        trial_id: Trial identifier (NCT number or custom ID)
    """
    trial_docs = app.state.db.get_trial_by_id(trial_id)

    if not trial_docs.get("documents"):
        raise HTTPException(
            status_code=404,
            detail=f"Trial {trial_id} not found"
        )

    return {
        "trial_id": trial_id,
        "document_count": len(trial_docs["documents"]),
        "sections": list(set(
            m.get("section", "unknown")
            for m in trial_docs.get("metadatas", [])
            if m
        )),
        "full_text": "\n\n".join(trial_docs["documents"])
    }


@app.delete("/trials/{trial_id}", tags=["Trials"])
async def delete_trial(trial_id: str):
    """
    Delete a trial from the database.

    Args:
        trial_id: Trial identifier to delete
    """
    try:
        app.state.db.delete_trial(trial_id)
        return {"message": f"Trial {trial_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting trial: {str(e)}"
        )


# =============================================================================
# RUN SERVER
# =============================================================================

def run_server():
    """Run the API server."""
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("API_RELOAD", "true").lower() == "true"

    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        reload=reload
    )


if __name__ == "__main__":
    run_server()
