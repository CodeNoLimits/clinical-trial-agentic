"""
Patient Profiler Agent

Analyzes and structures patient data for eligibility matching.
This is Step 2 of the 6-step screening workflow.
"""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None

try:
    from langchain_openai import ChatOpenAI
except ImportError:
    ChatOpenAI = None

from langchain_core.messages import SystemMessage, HumanMessage

from .prompts.system_prompts import PATIENT_PROFILER_PROMPT


class PatientProfilerAgent:
    """
    Agent responsible for analyzing and structuring patient data.

    Creates a structured patient profile with:
    - Demographics (age, sex, race)
    - Diagnoses with ICD-10 codes
    - Current medications with dosages
    - Laboratory values with dates
    - Medical history
    - Lifestyle factors
    - Identified missing data
    """

    def __init__(self, model_name: Optional[str] = None):
        """Initialize the patient profiler agent."""
        provider = os.getenv("LLM_PROVIDER", "google")

        if provider == "google" and ChatGoogleGenerativeAI:
            self.llm = ChatGoogleGenerativeAI(
                model=model_name or os.getenv("LLM_MODEL", "gemini-2.0-flash"),
                google_api_key=os.getenv("GOOGLE_API_KEY"),
                temperature=0.1,
            )
        elif provider == "openai" and ChatOpenAI:
            self.llm = ChatOpenAI(
                model=model_name or os.getenv("LLM_MODEL", "gpt-4-turbo"),
                openai_api_key=os.getenv("OPENAI_API_KEY"),
                temperature=0.1,
            )
        else:
            self.llm = None

    async def profile(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a structured patient profile from raw patient data.

        Args:
            patient_data: Raw patient data dictionary

        Returns:
            Structured patient profile with all relevant medical entities
        """
        if self.llm is None:
            # Direct structuring without LLM
            return self._structure_patient_data(patient_data)

        messages = [
            SystemMessage(content=PATIENT_PROFILER_PROMPT),
            HumanMessage(content=f"""
Analyze the following patient data and create a structured profile:

{json.dumps(patient_data, indent=2)}

Return a JSON object with:
- patient_id: string
- demographics: {{age, sex, race, ethnicity}}
- diagnoses: [{{condition, icd10_code, stage, date_diagnosed}}]
- medications: [{{drug_name, generic_name, dose, frequency, start_date}}]
- lab_values: [{{test_name, value, unit, date, reference_range}}]
- medical_history: [string]
- lifestyle: {{smoking_status, alcohol_use, pregnancy_status}}
- missing_data: [string] - list of important fields that are missing

Return ONLY valid JSON, no markdown formatting.
""")
        ]

        try:
            response = await self.llm.ainvoke(messages)
            content = response.content

            # Clean up response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            return json.loads(content.strip())

        except Exception as e:
            print(f"LLM profiling failed: {e}, using direct structuring")
            return self._structure_patient_data(patient_data)

    def _structure_patient_data(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Structure patient data without LLM (direct mapping).

        Args:
            patient_data: Raw patient data

        Returns:
            Structured profile
        """
        profile = {
            "patient_id": patient_data.get("patient_id", "UNKNOWN"),
            "demographics": {},
            "diagnoses": [],
            "medications": [],
            "lab_values": [],
            "medical_history": [],
            "lifestyle": {},
            "missing_data": []
        }

        # Demographics
        profile["demographics"] = {
            "age": patient_data.get("age"),
            "sex": patient_data.get("sex"),
            "race": patient_data.get("race"),
            "ethnicity": patient_data.get("ethnicity")
        }

        if not profile["demographics"]["age"]:
            profile["missing_data"].append("age")
        if not profile["demographics"]["sex"]:
            profile["missing_data"].append("sex")

        # Diagnoses
        raw_diagnoses = patient_data.get("diagnoses", [])
        for dx in raw_diagnoses:
            if isinstance(dx, dict):
                profile["diagnoses"].append({
                    "condition": dx.get("condition", ""),
                    "icd10_code": dx.get("icd10", dx.get("icd10_code", "")),
                    "stage": dx.get("stage", ""),
                    "date_diagnosed": dx.get("date_diagnosed", dx.get("date", ""))
                })
            elif isinstance(dx, str):
                profile["diagnoses"].append({
                    "condition": dx,
                    "icd10_code": "",
                    "stage": "",
                    "date_diagnosed": ""
                })

        if not profile["diagnoses"]:
            profile["missing_data"].append("diagnoses")

        # Medications
        raw_medications = patient_data.get("medications", [])
        for med in raw_medications:
            if isinstance(med, dict):
                profile["medications"].append({
                    "drug_name": med.get("drug_name", med.get("name", "")),
                    "generic_name": med.get("generic_name", ""),
                    "dose": med.get("dose", med.get("dosage", "")),
                    "frequency": med.get("frequency", ""),
                    "start_date": med.get("start_date", "")
                })
            elif isinstance(med, str):
                profile["medications"].append({
                    "drug_name": med,
                    "generic_name": "",
                    "dose": "",
                    "frequency": "",
                    "start_date": ""
                })

        # Lab Values
        raw_labs = patient_data.get("lab_values", [])
        for lab in raw_labs:
            if isinstance(lab, dict):
                profile["lab_values"].append({
                    "test_name": lab.get("test", lab.get("test_name", "")),
                    "value": lab.get("value"),
                    "unit": lab.get("unit", ""),
                    "date": lab.get("date", ""),
                    "reference_range": lab.get("reference_range", "")
                })

        # Medical History
        raw_history = patient_data.get("medical_history", [])
        if isinstance(raw_history, list):
            profile["medical_history"] = raw_history
        elif isinstance(raw_history, str):
            profile["medical_history"] = [raw_history]

        # Lifestyle
        raw_lifestyle = patient_data.get("lifestyle", {})
        if isinstance(raw_lifestyle, dict):
            profile["lifestyle"] = {
                "smoking_status": raw_lifestyle.get("smoking_status", raw_lifestyle.get("smoking", "")),
                "alcohol_use": raw_lifestyle.get("alcohol_use", raw_lifestyle.get("alcohol", "")),
                "pregnancy_status": raw_lifestyle.get("pregnancy_status", raw_lifestyle.get("pregnancy", ""))
            }

        # Check for commonly needed missing data
        common_labs = ["hba1c", "egfr", "glucose"]
        found_labs = [l["test_name"].lower() for l in profile["lab_values"]]
        for lab in common_labs:
            if not any(lab in fl for fl in found_labs):
                profile["missing_data"].append(f"lab_{lab}")

        return profile

    def get_lab_value(self, profile: Dict[str, Any], test_name: str) -> Optional[float]:
        """
        Get a specific lab value from the patient profile.

        Args:
            profile: Patient profile
            test_name: Name of the lab test

        Returns:
            Lab value or None if not found
        """
        test_name_lower = test_name.lower()
        for lab in profile.get("lab_values", []):
            if test_name_lower in lab.get("test_name", "").lower():
                return lab.get("value")
        return None

    def has_diagnosis(self, profile: Dict[str, Any], condition: str) -> bool:
        """
        Check if patient has a specific diagnosis.

        Args:
            profile: Patient profile
            condition: Condition to check

        Returns:
            True if patient has the diagnosis
        """
        condition_lower = condition.lower()
        for dx in profile.get("diagnoses", []):
            if condition_lower in dx.get("condition", "").lower():
                return True
        return False

    def has_medication(self, profile: Dict[str, Any], drug_name: str) -> bool:
        """
        Check if patient is on a specific medication.

        Args:
            profile: Patient profile
            drug_name: Medication to check

        Returns:
            True if patient is on the medication
        """
        drug_lower = drug_name.lower()
        for med in profile.get("medications", []):
            if drug_lower in med.get("drug_name", "").lower():
                return True
            if drug_lower in med.get("generic_name", "").lower():
                return True
        return False
