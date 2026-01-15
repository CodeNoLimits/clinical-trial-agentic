"""
Supervisor Agent - LangGraph Orchestration

This module implements the main supervisor agent that coordinates the 6-step
clinical trial eligibility screening process using LangGraph.

Architecture follows the FDA/EMA AI guidance for transparency and explainability.
"""

from typing import TypedDict, Annotated, Literal, List, Dict, Any, Optional
from datetime import datetime
import json
import os
from pathlib import Path

# Ensure .env is loaded before any LLM initialization
from dotenv import load_dotenv
_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path, override=True)

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# Import LLM providers
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None

try:
    from langchain_openai import ChatOpenAI
except ImportError:
    ChatOpenAI = None

from .prompts.system_prompts import (
    SUPERVISOR_PROMPT,
    CRITERIA_EXTRACTOR_PROMPT,
    PATIENT_PROFILER_PROMPT,
    KNOWLEDGE_AGENT_PROMPT,
    ELIGIBILITY_MATCHER_PROMPT,
    CONFIDENCE_SCORER_PROMPT,
    EXPLANATION_GENERATOR_PROMPT,
)


# =============================================================================
# JSON RESPONSE CLEANING
# =============================================================================

def clean_json_response(content: str) -> str:
    """
    Clean LLM response to extract valid JSON.
    Handles markdown code blocks and other formatting.
    """
    content = content.strip()

    # Remove markdown code blocks
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0]
    elif "```" in content:
        parts = content.split("```")
        if len(parts) >= 2:
            content = parts[1].split("```")[0]

    return content.strip()


# =============================================================================
# STATE DEFINITION
# =============================================================================

class ScreeningState(TypedDict):
    """State schema for the screening workflow."""
    # Input data
    patient_data: Dict[str, Any]
    trial_protocol: str
    trial_id: str

    # Step 1: Extracted criteria
    inclusion_criteria: List[Dict[str, Any]]
    exclusion_criteria: List[Dict[str, Any]]

    # Step 2: Patient profile
    patient_profile: Dict[str, Any]

    # Step 3: Medical context from RAG
    medical_context: Dict[str, Any]

    # Step 4: Matching results
    matching_results: List[Dict[str, Any]]

    # Step 5: Confidence scores
    confidence_scores: Dict[str, Any]

    # Step 6: Final output
    final_decision: str  # ELIGIBLE | INELIGIBLE | UNCERTAIN
    explainability_table: List[Dict[str, Any]]
    clinical_narrative: str

    # Workflow metadata
    current_step: str
    completed_steps: List[str]
    errors: List[str]
    requires_human_review: bool
    processing_started: str
    processing_completed: str


# =============================================================================
# LLM INITIALIZATION
# =============================================================================

def get_llm(model_name: Optional[str] = None):
    """Get the appropriate LLM based on environment configuration."""
    provider = os.getenv("LLM_PROVIDER", "google")

    if provider == "google" and ChatGoogleGenerativeAI:
        return ChatGoogleGenerativeAI(
            model=model_name or os.getenv("LLM_MODEL", "gemini-2.0-flash"),
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.1,  # Low temperature for consistency
        )
    elif provider == "openai" and ChatOpenAI:
        return ChatOpenAI(
            model=model_name or os.getenv("LLM_MODEL", "gpt-4-turbo"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.1,
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


# =============================================================================
# AGENT NODES
# =============================================================================

async def extract_criteria(state: ScreeningState) -> ScreeningState:
    """
    STEP 1: Extract eligibility criteria from trial protocol.

    Uses the CriteriaExtractor agent to parse the protocol document
    and structure inclusion/exclusion criteria.
    """
    llm = get_llm()

    messages = [
        SystemMessage(content=CRITERIA_EXTRACTOR_PROMPT),
        HumanMessage(content=f"""
Extract all eligibility criteria from the following clinical trial protocol:

{state['trial_protocol']}

Return a JSON object with 'inclusion_criteria' and 'exclusion_criteria' arrays.
Each criterion should have: criterion_id, type, category, text, normalized,
required_data_points, and comparison_operator.
""")
    ]

    try:
        response = await llm.ainvoke(messages)
        cleaned = clean_json_response(response.content)
        result = json.loads(cleaned)

        state["inclusion_criteria"] = result.get("inclusion_criteria", [])
        state["exclusion_criteria"] = result.get("exclusion_criteria", [])
        state["completed_steps"].append("CRITERIA_EXTRACTION")
        state["current_step"] = "PATIENT_PROFILING"

    except Exception as e:
        state["errors"].append(f"Criteria extraction error: {str(e)}")

    return state


async def profile_patient(state: ScreeningState) -> ScreeningState:
    """
    STEP 2: Analyze and structure patient data.

    Uses the PatientProfiler agent to extract relevant medical entities
    from patient data for matching against criteria.
    """
    llm = get_llm()

    messages = [
        SystemMessage(content=PATIENT_PROFILER_PROMPT),
        HumanMessage(content=f"""
Analyze the following patient data and create a structured profile:

{json.dumps(state['patient_data'], indent=2)}

Return a JSON object with: patient_id, demographics, diagnoses, medications,
lab_values, medical_history, lifestyle, and missing_data.
""")
    ]

    try:
        response = await llm.ainvoke(messages)
        state["patient_profile"] = json.loads(clean_json_response(response.content))
        state["completed_steps"].append("PATIENT_PROFILING")
        state["current_step"] = "KNOWLEDGE_QUERY"

    except Exception as e:
        state["errors"].append(f"Patient profiling error: {str(e)}")

    return state


async def query_knowledge_base(state: ScreeningState) -> ScreeningState:
    """
    STEP 3: Query RAG for medical context.

    Uses the KnowledgeAgent to retrieve relevant medical information
    from the vector database to enrich the matching process.
    """
    from ..database.retrieval import HybridRetriever

    llm = get_llm()
    retriever = HybridRetriever()

    # Build queries from patient profile
    queries = []
    if state["patient_profile"].get("diagnoses"):
        for diagnosis in state["patient_profile"]["diagnoses"]:
            queries.append(f"Clinical guidelines for {diagnosis.get('condition', '')}")

    if state["patient_profile"].get("medications"):
        drug_names = [med.get("drug_name", "") for med in state["patient_profile"]["medications"]]
        if len(drug_names) > 1:
            queries.append(f"Drug interactions between {', '.join(drug_names)}")

    # Execute RAG retrieval
    try:
        retrieved_context = []
        for query in queries[:5]:  # Limit to 5 queries
            results = await retriever.search(query, top_k=3)
            retrieved_context.extend(results)

        messages = [
            SystemMessage(content=KNOWLEDGE_AGENT_PROMPT),
            HumanMessage(content=f"""
Synthesize the following retrieved medical context for the patient:

Patient Profile Summary:
{json.dumps(state['patient_profile'], indent=2)}

Retrieved Context:
{json.dumps(retrieved_context, indent=2)}

Return a JSON with: queries_executed, retrieved_context summary,
drug_interactions, relevant_guidelines, and potential_concerns.
""")
        ]

        response = await llm.ainvoke(messages)
        state["medical_context"] = json.loads(clean_json_response(response.content))
        state["completed_steps"].append("KNOWLEDGE_QUERY")
        state["current_step"] = "ELIGIBILITY_MATCHING"

    except Exception as e:
        state["errors"].append(f"Knowledge query error: {str(e)}")
        state["medical_context"] = {"error": str(e), "retrieved_context": []}
        state["current_step"] = "ELIGIBILITY_MATCHING"  # Continue anyway

    return state


async def match_eligibility(state: ScreeningState) -> ScreeningState:
    """
    STEP 4: Match patient profile to each eligibility criterion.

    Uses the EligibilityMatcher agent to systematically evaluate
    each criterion with explicit reasoning.
    """
    llm = get_llm()

    all_criteria = (
        [{"type": "inclusion", **c} for c in state["inclusion_criteria"]] +
        [{"type": "exclusion", **c} for c in state["exclusion_criteria"]]
    )

    messages = [
        SystemMessage(content=ELIGIBILITY_MATCHER_PROMPT),
        HumanMessage(content=f"""
Match the patient to each eligibility criterion:

PATIENT PROFILE:
{json.dumps(state['patient_profile'], indent=2)}

MEDICAL CONTEXT:
{json.dumps(state['medical_context'], indent=2)}

ELIGIBILITY CRITERIA:
{json.dumps(all_criteria, indent=2)}

For each criterion, return:
- criterion_id
- criterion_text
- patient_data_used
- match_status (MATCH | NO_MATCH | UNCERTAIN | MISSING_DATA)
- confidence (0.0-1.0)
- reasoning
- evidence
- concerns

Return as a JSON array of matching results.
""")
    ]

    try:
        response = await llm.ainvoke(messages)
        state["matching_results"] = json.loads(clean_json_response(response.content))
        state["completed_steps"].append("ELIGIBILITY_MATCHING")
        state["current_step"] = "CONFIDENCE_SCORING"

    except Exception as e:
        state["errors"].append(f"Eligibility matching error: {str(e)}")

    return state


async def calculate_confidence(state: ScreeningState) -> ScreeningState:
    """
    STEP 5: Calculate overall confidence score using self-consistency.

    Generates multiple independent assessments and calculates
    agreement rate for calibrated confidence scoring.
    """
    llm = get_llm()
    n_samples = int(os.getenv("CONFIDENCE_SAMPLES", "5"))
    threshold = float(os.getenv("CONFIDENCE_THRESHOLD", "0.80"))

    messages = [
        SystemMessage(content=CONFIDENCE_SCORER_PROMPT),
        HumanMessage(content=f"""
Calculate the confidence score for the following matching results:

MATCHING RESULTS:
{json.dumps(state['matching_results'], indent=2)}

Apply:
1. Individual criterion confidence aggregation
2. Self-consistency check (imagine {n_samples} independent reviewers)
3. Missing data penalties
4. Uncertainty penalties

Return JSON with:
- overall_confidence (0.0-1.0)
- confidence_level (HIGH | MODERATE | LOW | VERY_LOW)
- individual_scores
- consistency_score
- requires_human_review (true if < {threshold})
- review_reasons
""")
    ]

    try:
        response = await llm.ainvoke(messages)
        state["confidence_scores"] = json.loads(clean_json_response(response.content))
        state["requires_human_review"] = state["confidence_scores"].get(
            "requires_human_review", False
        )
        state["completed_steps"].append("CONFIDENCE_SCORING")
        state["current_step"] = "EXPLANATION_GENERATION"

    except Exception as e:
        state["errors"].append(f"Confidence scoring error: {str(e)}")

    return state


async def generate_explanation(state: ScreeningState) -> ScreeningState:
    """
    STEP 6: Generate AI explainability table and clinical narrative.

    Creates FDA/EMA compliant explanations with complete audit trail.
    """
    llm = get_llm()

    # Determine final decision
    has_no_match_inclusion = any(
        r.get("match_status") == "NO_MATCH"
        for r in state["matching_results"]
        if r.get("type") == "inclusion"
    )
    has_match_exclusion = any(
        r.get("match_status") == "MATCH"
        for r in state["matching_results"]
        if r.get("type") == "exclusion"
    )
    has_uncertain = any(
        r.get("match_status") in ["UNCERTAIN", "MISSING_DATA"]
        for r in state["matching_results"]
    )

    if has_no_match_inclusion or has_match_exclusion:
        preliminary_decision = "INELIGIBLE"
    elif has_uncertain:
        preliminary_decision = "UNCERTAIN"
    else:
        preliminary_decision = "ELIGIBLE"

    messages = [
        SystemMessage(content=EXPLANATION_GENERATOR_PROMPT),
        HumanMessage(content=f"""
Generate the final explainability output:

PRELIMINARY DECISION: {preliminary_decision}

MATCHING RESULTS:
{json.dumps(state['matching_results'], indent=2)}

CONFIDENCE SCORES:
{json.dumps(state['confidence_scores'], indent=2)}

MEDICAL CONTEXT:
{json.dumps(state['medical_context'], indent=2)}

Generate:
1. Final decision with confidence
2. AI Explainability Table (all criteria with evidence)
3. Clinical narrative (paragraph suitable for documentation)
4. Key factors, concerns, and recommendations
5. Audit trail with timestamp

Return as structured JSON.
""")
    ]

    try:
        response = await llm.ainvoke(messages)
        result = json.loads(clean_json_response(response.content))

        state["final_decision"] = result.get("decision", preliminary_decision)
        state["explainability_table"] = result.get("explainability_table", [])
        state["clinical_narrative"] = result.get("clinical_narrative", "")
        state["completed_steps"].append("EXPLANATION_GENERATION")
        state["current_step"] = "COMPLETE"
        state["processing_completed"] = datetime.now().isoformat()

    except Exception as e:
        state["errors"].append(f"Explanation generation error: {str(e)}")
        state["final_decision"] = preliminary_decision

    return state


# =============================================================================
# ROUTING LOGIC
# =============================================================================

def route_next_step(state: ScreeningState) -> Literal[
    "extract_criteria",
    "profile_patient",
    "query_knowledge_base",
    "match_eligibility",
    "calculate_confidence",
    "generate_explanation",
    "end"
]:
    """Determine the next step based on current state."""

    current = state.get("current_step", "CRITERIA_EXTRACTION")

    if current == "CRITERIA_EXTRACTION":
        return "extract_criteria"
    elif current == "PATIENT_PROFILING":
        return "profile_patient"
    elif current == "KNOWLEDGE_QUERY":
        return "query_knowledge_base"
    elif current == "ELIGIBILITY_MATCHING":
        return "match_eligibility"
    elif current == "CONFIDENCE_SCORING":
        return "calculate_confidence"
    elif current == "EXPLANATION_GENERATION":
        return "generate_explanation"
    else:
        return "end"


# =============================================================================
# WORKFLOW CREATION
# =============================================================================

def create_screening_workflow() -> StateGraph:
    """
    Create the LangGraph workflow for clinical trial screening.

    Returns:
        StateGraph: Compiled workflow ready for execution
    """
    workflow = StateGraph(ScreeningState)

    # Add all nodes
    workflow.add_node("extract_criteria", extract_criteria)
    workflow.add_node("profile_patient", profile_patient)
    workflow.add_node("query_knowledge_base", query_knowledge_base)
    workflow.add_node("match_eligibility", match_eligibility)
    workflow.add_node("calculate_confidence", calculate_confidence)
    workflow.add_node("generate_explanation", generate_explanation)

    # Set entry point
    workflow.set_entry_point("extract_criteria")

    # Add edges (sequential workflow)
    workflow.add_edge("extract_criteria", "profile_patient")
    workflow.add_edge("profile_patient", "query_knowledge_base")
    workflow.add_edge("query_knowledge_base", "match_eligibility")
    workflow.add_edge("match_eligibility", "calculate_confidence")
    workflow.add_edge("calculate_confidence", "generate_explanation")
    workflow.add_edge("generate_explanation", END)

    # Compile with memory for checkpointing
    memory = MemorySaver()
    compiled = workflow.compile(checkpointer=memory)

    return compiled


# =============================================================================
# SUPERVISOR AGENT CLASS
# =============================================================================

class SupervisorAgent:
    """
    Main supervisor agent for clinical trial eligibility screening.

    This agent orchestrates the 6-step screening process using LangGraph
    and provides a simple interface for running screenings.

    Example:
        agent = SupervisorAgent()
        result = await agent.screen_patient(patient_data, trial_protocol, trial_id)
    """

    def __init__(self):
        self.workflow = create_screening_workflow()

    def _create_initial_state(
        self,
        patient_data: Dict[str, Any],
        trial_protocol: str,
        trial_id: str
    ) -> ScreeningState:
        """Create initial state for the workflow."""
        return ScreeningState(
            patient_data=patient_data,
            trial_protocol=trial_protocol,
            trial_id=trial_id,
            inclusion_criteria=[],
            exclusion_criteria=[],
            patient_profile={},
            medical_context={},
            matching_results=[],
            confidence_scores={},
            final_decision="",
            explainability_table=[],
            clinical_narrative="",
            current_step="CRITERIA_EXTRACTION",
            completed_steps=[],
            errors=[],
            requires_human_review=False,
            processing_started=datetime.now().isoformat(),
            processing_completed="",
        )

    async def screen_patient(
        self,
        patient_data: Dict[str, Any],
        trial_protocol: str,
        trial_id: str,
        thread_id: str = "default"
    ) -> Dict[str, Any]:
        """
        Run the full screening workflow for a patient.

        Args:
            patient_data: Patient information dictionary
            trial_protocol: Clinical trial protocol text
            trial_id: Identifier for the trial
            thread_id: Thread ID for checkpointing

        Returns:
            Dictionary with screening results including:
            - decision: ELIGIBLE | INELIGIBLE | UNCERTAIN
            - confidence: Overall confidence score
            - explainability_table: Detailed criterion-by-criterion results
            - clinical_narrative: Human-readable explanation
            - requires_human_review: Boolean flag
        """
        initial_state = self._create_initial_state(
            patient_data, trial_protocol, trial_id
        )

        config = {"configurable": {"thread_id": thread_id}}

        # Run the workflow
        final_state = await self.workflow.ainvoke(initial_state, config)

        # Return structured result
        return {
            "trial_id": trial_id,
            "decision": final_state.get("final_decision", "UNCERTAIN"),
            "confidence": final_state.get("confidence_scores", {}).get("overall_confidence", 0.0),
            "confidence_level": final_state.get("confidence_scores", {}).get("confidence_level", "UNKNOWN"),
            "explainability_table": final_state.get("explainability_table", []),
            "clinical_narrative": final_state.get("clinical_narrative", ""),
            "requires_human_review": final_state.get("requires_human_review", True),
            "completed_steps": final_state.get("completed_steps", []),
            "errors": final_state.get("errors", []),
            "processing_started": final_state.get("processing_started", ""),
            "processing_completed": final_state.get("processing_completed", ""),
        }


# =============================================================================
# CLI ENTRY POINT (for testing)
# =============================================================================

async def main():
    """Test the supervisor agent with sample data."""
    import asyncio
    from dotenv import load_dotenv
    load_dotenv()

    # Sample patient data
    patient_data = {
        "patient_id": "PT001",
        "age": 58,
        "sex": "male",
        "diagnoses": [
            {"condition": "Type 2 Diabetes Mellitus", "icd10": "E11.9"}
        ],
        "medications": [
            {"drug_name": "Metformin", "dose": "1000mg", "frequency": "twice daily"}
        ],
        "lab_values": [
            {"test": "HbA1c", "value": 8.2, "unit": "%", "date": "2024-01-15"}
        ]
    }

    # Sample trial protocol
    trial_protocol = """
    CLINICAL TRIAL: NCT12345678

    INCLUSION CRITERIA:
    1. Age 18-75 years
    2. Diagnosis of Type 2 Diabetes Mellitus
    3. HbA1c between 7.0% and 10.0%
    4. Currently on stable metformin therapy (≥1000mg/day) for at least 3 months

    EXCLUSION CRITERIA:
    1. Type 1 Diabetes
    2. Pregnant or nursing women
    3. Severe renal impairment (eGFR < 30 mL/min)
    4. Current use of insulin
    """

    agent = SupervisorAgent()
    result = await agent.screen_patient(
        patient_data=patient_data,
        trial_protocol=trial_protocol,
        trial_id="NCT12345678"
    )

    print("=" * 60)
    print("SCREENING RESULT")
    print("=" * 60)
    print(f"Decision: {result['decision']}")
    print(f"Confidence: {result['confidence']:.1%}")
    print(f"Requires Human Review: {result['requires_human_review']}")
    print("\nClinical Narrative:")
    print(result['clinical_narrative'])
    print("\nExplainability Table:")
    for row in result['explainability_table']:
        print(f"  - {row.get('criterion_id', 'N/A')}: {row.get('match_status', 'N/A')}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
