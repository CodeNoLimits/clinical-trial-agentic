"""
Streamlit Application - Clinical Trial Eligibility Screening UI

Main entry point for the web interface providing:
- Patient data input (form or JSON)
- Trial selection from database
- Real-time screening execution
- Interactive results visualization
- AI explainability table display

Run with: streamlit run src/ui/app.py
"""

import os
import sys
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Note: nest_asyncio removed - incompatible with uvloop on Streamlit Cloud
# Using synchronous approach instead

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load .env only if it exists (local dev), otherwise rely on st.secrets
from dotenv import load_dotenv
env_file = PROJECT_ROOT / ".env"
if env_file.exists():
    load_dotenv(env_file)


# =============================================================================
# API KEY MANAGEMENT - SECURE MULTI-SOURCE LOADING
# =============================================================================

def get_api_key() -> str:
    """
    Get Google API key from multiple sources (in priority order):
    1. Streamlit secrets (for cloud deployment - PRIORITY)
    2. Environment variable (.env file for local dev)
    3. Session state (user input in sidebar)
    4. Direct GOOGLE_API_KEY secret

    NEVER returns mock data - raises error if no key found.
    """
    # Source 1: Streamlit secrets (PRIORITY for Streamlit Cloud)
    try:
        # Try nested format first
        api_key = st.secrets.get("google", {}).get("api_key")
        if api_key and api_key != "your_gemini_api_key_here":
            os.environ["GOOGLE_API_KEY"] = api_key
            return api_key
        # Try direct GOOGLE_API_KEY
        api_key = st.secrets.get("GOOGLE_API_KEY")
        if api_key and api_key != "your_gemini_api_key_here":
            os.environ["GOOGLE_API_KEY"] = api_key
            return api_key
    except Exception:
        pass

    # Source 2: Environment variable (local dev)
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key and api_key != "your_gemini_api_key_here":
        return api_key

    # Source 3: Session state (user entered via sidebar)
    if "google_api_key" in st.session_state and st.session_state.google_api_key:
        os.environ["GOOGLE_API_KEY"] = st.session_state.google_api_key
        return st.session_state.google_api_key

    return None


def init_api_key_sidebar():
    """Initialize API key input in sidebar if needed."""
    api_key = get_api_key()

    if not api_key:
        st.sidebar.error("API Key Required")
        st.sidebar.markdown("---")
        user_key = st.sidebar.text_input(
            "Google API Key",
            type="password",
            help="Enter your Google Gemini API key. Contact Melea for fallback key.",
            key="api_key_input"
        )
        if user_key:
            st.session_state.google_api_key = user_key
            os.environ["GOOGLE_API_KEY"] = user_key
            st.sidebar.success("API Key configured!")
            st.rerun()
        else:
            st.sidebar.warning("Screening requires a valid API key. No mock data will be used.")
        return False

    st.sidebar.success("API Key configured")
    return True


# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="Clinical Trial Eligibility Screening",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stApp {
        max-width: 1400px;
        margin: 0 auto;
    }
    .eligibility-eligible {
        background-color: #28a745;
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        font-size: 24px;
    }
    .eligibility-ineligible {
        background-color: #dc3545;
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        font-size: 24px;
    }
    .eligibility-uncertain {
        background-color: #ffc107;
        color: black;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        font-size: 24px;
    }
    .confidence-high { color: #28a745; }
    .confidence-moderate { color: #17a2b8; }
    .confidence-low { color: #ffc107; }
    .confidence-very-low { color: #dc3545; }
    .metric-card {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================

if "screening_result" not in st.session_state:
    st.session_state.screening_result = None

if "patient_data" not in st.session_state:
    st.session_state.patient_data = None


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_eligibility_class(decision: str) -> str:
    """Get CSS class for eligibility decision."""
    return f"eligibility-{decision.lower()}"


def get_confidence_class(level: str) -> str:
    """Get CSS class for confidence level."""
    return f"confidence-{level.lower().replace('_', '-')}"


def create_confidence_gauge(confidence: float) -> go.Figure:
    """Create a gauge chart for confidence score."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=confidence * 100,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Confidence Score"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 70], 'color': "#dc3545"},
                {'range': [70, 80], 'color': "#ffc107"},
                {'range': [80, 90], 'color': "#17a2b8"},
                {'range': [90, 100], 'color': "#28a745"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 80
            }
        }
    ))
    fig.update_layout(height=300)
    return fig


def create_criteria_chart(results: list) -> go.Figure:
    """Create a bar chart showing criteria match status."""
    if not results:
        return None

    df = pd.DataFrame(results)

    # Map status to numeric for coloring
    status_map = {
        "MATCH": 1,
        "NO_MATCH": -1,
        "UNCERTAIN": 0,
        "MISSING_DATA": 0
    }

    df["status_num"] = df["match_status"].map(status_map)

    # Create color mapping
    colors = df["match_status"].map({
        "MATCH": "#28a745",
        "NO_MATCH": "#dc3545",
        "UNCERTAIN": "#ffc107",
        "MISSING_DATA": "#6c757d"
    })

    fig = go.Figure(go.Bar(
        y=df["criterion_id"],
        x=df["confidence"],
        orientation='h',
        marker_color=colors,
        text=df["match_status"],
        textposition='auto',
    ))

    fig.update_layout(
        title="Criteria Evaluation Results",
        xaxis_title="Confidence",
        yaxis_title="Criterion",
        height=max(400, len(results) * 30),
        showlegend=False
    )

    return fig


def run_screening(patient_data: dict, trial_protocol: str, trial_id: str) -> dict:
    """Run the screening workflow (synchronous wrapper for Streamlit)."""
    try:
        from src.agents.supervisor import SupervisorAgent
        agent = SupervisorAgent()

        # Create async coroutine
        async def _async_screen():
            return await agent.screen_patient(
                patient_data=patient_data,
                trial_protocol=trial_protocol,
                trial_id=trial_id
            )

        # Run in a new event loop (safe for Streamlit)
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(_async_screen())
        finally:
            loop.close()

        return result
    except Exception as e:
        st.error(f"Screening error: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return None


# =============================================================================
# SIDEBAR - API KEY CHECK
# =============================================================================

api_key_valid = init_api_key_sidebar()


# =============================================================================
# SIDEBAR - TRIAL SELECTION
# =============================================================================

st.sidebar.title("Trial Selection")

# Option to select from database or upload
trial_source = st.sidebar.radio(
    "Trial Protocol Source",
    ["Enter Trial ID", "Paste Protocol Text", "Upload File"]
)

trial_id = ""
trial_protocol = ""

if trial_source == "Enter Trial ID":
    trial_id = st.sidebar.text_input(
        "Trial ID (NCT Number)",
        placeholder="e.g., NCT12345678"
    )
    st.sidebar.info("Protocol will be retrieved from database")

elif trial_source == "Paste Protocol Text":
    trial_id = st.sidebar.text_input(
        "Trial ID",
        placeholder="e.g., NCT12345678"
    )
    trial_protocol = st.sidebar.text_area(
        "Protocol Text",
        height=300,
        placeholder="Paste the clinical trial protocol here..."
    )

else:  # Upload File
    trial_id = st.sidebar.text_input(
        "Trial ID",
        placeholder="e.g., NCT12345678"
    )
    uploaded_file = st.sidebar.file_uploader(
        "Upload Protocol",
        type=["md", "txt", "json"]
    )
    if uploaded_file:
        trial_protocol = uploaded_file.read().decode("utf-8")
        st.sidebar.success(f"Loaded: {uploaded_file.name}")


# =============================================================================
# MAIN CONTENT
# =============================================================================

st.title("Clinical Trial Eligibility Screening")
st.markdown("""
**Agentic AI System** for automated patient-trial matching with explainable decisions.

This system uses:
- **RAG** (Retrieval-Augmented Generation) for medical context
- **Multi-agent architecture** with 6-step screening process
- **Self-consistency** confidence scoring
- **AI Explainability** tables for transparent decisions
""")

# Tabs for different input methods
tab1, tab2, tab3 = st.tabs(["Patient Form", "JSON Input", "Batch Processing"])


# =============================================================================
# TAB 1: PATIENT FORM
# =============================================================================

with tab1:
    st.header("Patient Information")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Demographics")
        patient_id = st.text_input("Patient ID", value="PT001")
        age = st.number_input("Age", min_value=0, max_value=120, value=55)
        sex = st.selectbox("Sex", ["male", "female", "other"])

        st.subheader("Diagnoses")
        diagnosis_condition = st.text_input(
            "Primary Condition",
            placeholder="e.g., Type 2 Diabetes Mellitus"
        )
        diagnosis_icd10 = st.text_input(
            "ICD-10 Code",
            placeholder="e.g., E11.9"
        )

    with col2:
        st.subheader("Current Medications")
        medication_name = st.text_input(
            "Medication Name",
            placeholder="e.g., Metformin"
        )
        medication_dose = st.text_input(
            "Dose",
            placeholder="e.g., 1000mg twice daily"
        )

        st.subheader("Lab Values")
        lab_test = st.text_input(
            "Test Name",
            placeholder="e.g., HbA1c"
        )
        lab_value = st.number_input("Value", value=8.0, format="%.1f")
        lab_unit = st.text_input("Unit", placeholder="e.g., %")

    # Build patient data from form
    if st.button("Build Patient Profile", key="build_form"):
        patient_data = {
            "patient_id": patient_id,
            "age": age,
            "sex": sex,
            "diagnoses": [],
            "medications": [],
            "lab_values": [],
            "medical_history": [],
            "lifestyle": {}
        }

        if diagnosis_condition:
            patient_data["diagnoses"].append({
                "condition": diagnosis_condition,
                "icd10": diagnosis_icd10 or ""
            })

        if medication_name:
            patient_data["medications"].append({
                "drug_name": medication_name,
                "dose": medication_dose or ""
            })

        if lab_test:
            patient_data["lab_values"].append({
                "test": lab_test,
                "value": lab_value,
                "unit": lab_unit or ""
            })

        st.session_state.patient_data = patient_data
        st.success("Patient profile built!")
        st.json(patient_data)


# =============================================================================
# TAB 2: JSON INPUT
# =============================================================================

with tab2:
    st.header("JSON Patient Data")

    json_template = """{
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
    ],
    "medical_history": ["Hypertension"],
    "lifestyle": {
        "smoking_status": "never",
        "alcohol_use": "occasional"
    }
}"""

    json_input = st.text_area(
        "Patient Data (JSON)",
        value=json_template,
        height=400
    )

    if st.button("Parse JSON", key="parse_json"):
        try:
            patient_data = json.loads(json_input)
            st.session_state.patient_data = patient_data
            st.success("JSON parsed successfully!")
            st.json(patient_data)
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON: {str(e)}")


# =============================================================================
# TAB 3: BATCH PROCESSING
# =============================================================================

with tab3:
    st.header("Batch Processing")
    st.info("Upload a CSV or JSON file with multiple patients for batch screening.")

    batch_file = st.file_uploader(
        "Upload Patient Batch",
        type=["csv", "json"],
        key="batch_upload"
    )

    if batch_file:
        if batch_file.name.endswith(".csv"):
            df = pd.read_csv(batch_file)
            st.dataframe(df)
            st.info(f"Loaded {len(df)} patients")
        else:
            batch_data = json.loads(batch_file.read().decode("utf-8"))
            if isinstance(batch_data, list):
                st.info(f"Loaded {len(batch_data)} patients")
            st.json(batch_data)


# =============================================================================
# SCREENING EXECUTION
# =============================================================================

st.divider()
st.header("Run Screening")

col1, col2 = st.columns([2, 1])

with col1:
    if st.session_state.patient_data:
        st.success("Patient data loaded")
        with st.expander("View Patient Data"):
            st.json(st.session_state.patient_data)
    else:
        st.warning("Please enter patient data above")

with col2:
    if trial_id:
        st.success(f"Trial: {trial_id}")
    else:
        st.warning("Please select/enter a trial")

# Run screening button
if st.button("Run Eligibility Screening", type="primary", use_container_width=True):
    if not api_key_valid:
        st.error("API Key required. Please enter your Google API key in the sidebar. No mock data will be used.")
    elif not st.session_state.patient_data:
        st.error("Please enter patient data first")
    elif not trial_id:
        st.error("Please enter a trial ID")
    else:
        with st.spinner("Running 6-step screening workflow..."):
            # Use default protocol if not provided
            if not trial_protocol:
                trial_protocol = """
                CLINICAL TRIAL: """ + trial_id + """

                INCLUSION CRITERIA:
                1. Age 18-75 years
                2. Diagnosis of Type 2 Diabetes Mellitus
                3. HbA1c between 7.0% and 10.0%
                4. Currently on stable metformin therapy

                EXCLUSION CRITERIA:
                1. Type 1 Diabetes
                2. Pregnant or nursing women
                3. Severe renal impairment (eGFR < 30 mL/min)
                """

            # Run screening (now synchronous)
            result = run_screening(
                st.session_state.patient_data,
                trial_protocol,
                trial_id
            )

            if result:
                st.session_state.screening_result = result


# =============================================================================
# RESULTS DISPLAY
# =============================================================================

if st.session_state.screening_result:
    result = st.session_state.screening_result
    st.divider()
    st.header("Screening Results")

    # Decision banner
    decision = result.get("decision", "UNCERTAIN")
    confidence = result.get("confidence", 0.0)
    confidence_level = result.get("confidence_level", "UNKNOWN")

    st.markdown(
        f'<div class="{get_eligibility_class(decision)}">'
        f'{decision}'
        f'</div>',
        unsafe_allow_html=True
    )

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Confidence", f"{confidence:.0%}")
    with col2:
        st.metric("Confidence Level", confidence_level)
    with col3:
        review_status = "Required" if result.get("requires_human_review") else "Not Required"
        st.metric("Human Review", review_status)
    with col4:
        st.metric("Trial ID", result.get("trial_id", "N/A"))

    # Tabs for detailed results
    result_tab1, result_tab2, result_tab3 = st.tabs([
        "Confidence Analysis",
        "AI Explainability Table",
        "Clinical Narrative"
    ])

    with result_tab1:
        col1, col2 = st.columns(2)

        with col1:
            # Confidence gauge
            fig = create_confidence_gauge(confidence)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Review reasons
            if result.get("requires_human_review"):
                st.warning("Human Review Required")
                st.markdown("**Reasons:**")
                for reason in result.get("errors", []):
                    st.markdown(f"- {reason}")

            # Processing info
            st.markdown("**Processing Information:**")
            st.markdown(f"- Started: {result.get('processing_started', 'N/A')}")
            st.markdown(f"- Completed: {result.get('processing_completed', 'N/A')}")
            st.markdown(f"- Steps: {', '.join(result.get('completed_steps', []))}")

    with result_tab2:
        st.subheader("Criterion-by-Criterion Analysis")

        explainability_data = result.get("explainability_table", [])

        if explainability_data:
            # Create DataFrame
            df = pd.DataFrame(explainability_data)

            # Style the dataframe
            def style_status(val):
                colors = {
                    "MATCH": "background-color: #28a745; color: white",
                    "NO_MATCH": "background-color: #dc3545; color: white",
                    "UNCERTAIN": "background-color: #ffc107; color: black",
                    "MISSING_DATA": "background-color: #6c757d; color: white"
                }
                return colors.get(val, "")

            styled_df = df.style.applymap(
                style_status,
                subset=["match_status"] if "match_status" in df.columns else []
            )

            st.dataframe(styled_df, use_container_width=True)

            # Criteria chart
            fig = create_criteria_chart(explainability_data)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No explainability data available")

    with result_tab3:
        st.subheader("Clinical Documentation")

        narrative = result.get("clinical_narrative", "")
        if narrative:
            st.markdown(narrative)
        else:
            st.info("No clinical narrative generated")

        # Export options
        st.divider()
        st.subheader("Export Results")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("Export as JSON"):
                st.download_button(
                    "Download JSON",
                    json.dumps(result, indent=2),
                    f"screening_{trial_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    "application/json"
                )

        with col2:
            if st.button("Export as CSV"):
                df = pd.DataFrame(explainability_data)
                csv = df.to_csv(index=False)
                st.download_button(
                    "Download CSV",
                    csv,
                    f"screening_{trial_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    "text/csv"
                )

        with col3:
            if st.button("Generate Report"):
                st.info("PDF report generation coming soon...")


# =============================================================================
# FOOTER
# =============================================================================

st.divider()
st.markdown("""
---
**Clinical Trial Eligibility Screening System** | Version 1.0.0

Built with LangGraph, ChromaDB, and Streamlit

Authors: Meléa & David (CodeNoLimits) | 2026
""")
