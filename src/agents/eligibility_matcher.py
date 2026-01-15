"""
Eligibility Matcher Agent

Matches patient profile against eligibility criteria.
This is Step 4 of the 6-step screening workflow.
"""

import os
import json
import re
from typing import Dict, Any, List, Optional, Tuple

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None

try:
    from langchain_openai import ChatOpenAI
except ImportError:
    ChatOpenAI = None

from langchain_core.messages import SystemMessage, HumanMessage

from .prompts.system_prompts import ELIGIBILITY_MATCHER_PROMPT


class EligibilityMatcherAgent:
    """
    Agent responsible for matching patient data to eligibility criteria.

    For each criterion, determines:
    - Match status (MATCH, NO_MATCH, UNCERTAIN, MISSING_DATA)
    - Confidence score
    - Reasoning
    - Evidence from patient data
    """

    def __init__(self, model_name: Optional[str] = None):
        """Initialize the eligibility matcher agent."""
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

    async def match(
        self,
        patient_profile: Dict[str, Any],
        inclusion_criteria: List[Dict[str, Any]],
        exclusion_criteria: List[Dict[str, Any]],
        medical_context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Match patient profile against all eligibility criteria.

        Args:
            patient_profile: Structured patient profile
            inclusion_criteria: List of inclusion criteria
            exclusion_criteria: List of exclusion criteria
            medical_context: Optional RAG-retrieved medical context

        Returns:
            List of matching results for each criterion
        """
        all_criteria = (
            [{"type": "inclusion", **c} for c in inclusion_criteria] +
            [{"type": "exclusion", **c} for c in exclusion_criteria]
        )

        if self.llm:
            return await self._match_with_llm(
                patient_profile, all_criteria, medical_context
            )
        else:
            return self._match_rule_based(patient_profile, all_criteria)

    async def _match_with_llm(
        self,
        patient_profile: Dict[str, Any],
        criteria: List[Dict[str, Any]],
        medical_context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Match using LLM for complex reasoning."""

        messages = [
            SystemMessage(content=ELIGIBILITY_MATCHER_PROMPT),
            HumanMessage(content=f"""
Match the patient to each eligibility criterion:

PATIENT PROFILE:
{json.dumps(patient_profile, indent=2)}

MEDICAL CONTEXT:
{json.dumps(medical_context or {}, indent=2)}

ELIGIBILITY CRITERIA:
{json.dumps(criteria, indent=2)}

For each criterion, return:
- criterion_id
- criterion_text
- type (inclusion/exclusion)
- patient_data_used: {{field, value, source}}
- match_status: MATCH | NO_MATCH | UNCERTAIN | MISSING_DATA
- confidence: 0.0-1.0
- reasoning: step-by-step clinical reasoning
- evidence: specific data points from patient profile
- concerns: any flags or concerns

Return as a JSON array of matching results. Return ONLY valid JSON.
""")
        ]

        try:
            response = await self.llm.ainvoke(messages)
            content = response.content

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            results = json.loads(content.strip())

            # Ensure it's a list
            if isinstance(results, dict):
                results = results.get("matching_results", [results])

            return results

        except Exception as e:
            print(f"LLM matching failed: {e}, using rule-based")
            return self._match_rule_based(patient_profile, criteria)

    def _match_rule_based(
        self,
        patient_profile: Dict[str, Any],
        criteria: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Rule-based matching without LLM."""

        results = []

        for criterion in criteria:
            result = self._evaluate_criterion(patient_profile, criterion)
            results.append(result)

        return results

    def _evaluate_criterion(
        self,
        patient_profile: Dict[str, Any],
        criterion: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate a single criterion against patient profile.

        Args:
            patient_profile: Patient profile
            criterion: Single criterion to evaluate

        Returns:
            Matching result
        """
        criterion_text = criterion.get("text", "").lower()
        criterion_type = criterion.get("type", "inclusion")
        category = criterion.get("category", "CLINICAL")

        result = {
            "criterion_id": criterion.get("criterion_id", ""),
            "criterion_text": criterion.get("text", ""),
            "type": criterion_type,
            "patient_data_used": {},
            "match_status": "UNCERTAIN",
            "confidence": 0.5,
            "reasoning": "",
            "evidence": [],
            "concerns": []
        }

        # Age check
        if "age" in criterion_text:
            age = patient_profile.get("demographics", {}).get("age")
            if age:
                result["patient_data_used"] = {"field": "age", "value": age}
                age_match = self._check_age_criterion(criterion_text, age)
                result["match_status"] = "MATCH" if age_match else "NO_MATCH"
                result["confidence"] = 1.0
                result["reasoning"] = f"Patient age ({age}) {'meets' if age_match else 'does not meet'} criterion"
                result["evidence"] = [f"Patient age: {age}"]
            else:
                result["match_status"] = "MISSING_DATA"
                result["reasoning"] = "Patient age not provided"

        # HbA1c check
        elif "hba1c" in criterion_text:
            hba1c = self._get_lab_value(patient_profile, "hba1c")
            if hba1c is not None:
                result["patient_data_used"] = {"field": "lab_hba1c", "value": hba1c}
                hba1c_match = self._check_range_criterion(criterion_text, hba1c)
                result["match_status"] = "MATCH" if hba1c_match else "NO_MATCH"
                result["confidence"] = 0.95
                result["reasoning"] = f"Patient HbA1c ({hba1c}%) {'within' if hba1c_match else 'outside'} required range"
                result["evidence"] = [f"Patient HbA1c: {hba1c}%"]
            else:
                result["match_status"] = "MISSING_DATA"
                result["reasoning"] = "HbA1c value not provided"

        # eGFR check
        elif "egfr" in criterion_text:
            egfr = self._get_lab_value(patient_profile, "egfr")
            if egfr is not None:
                result["patient_data_used"] = {"field": "lab_egfr", "value": egfr}
                egfr_match = self._check_threshold_criterion(criterion_text, egfr)
                result["match_status"] = "MATCH" if egfr_match else "NO_MATCH"
                result["confidence"] = 0.95
                result["reasoning"] = f"Patient eGFR ({egfr}) {'meets' if egfr_match else 'does not meet'} criterion"
                result["evidence"] = [f"Patient eGFR: {egfr}"]
            else:
                result["match_status"] = "MISSING_DATA"
                result["reasoning"] = "eGFR value not provided"

        # Diabetes type check
        elif "type 1 diabetes" in criterion_text or "type 2 diabetes" in criterion_text:
            diagnoses = patient_profile.get("diagnoses", [])
            has_t1d = any("type 1" in d.get("condition", "").lower() for d in diagnoses)
            has_t2d = any("type 2" in d.get("condition", "").lower() for d in diagnoses)

            if "type 1 diabetes" in criterion_text:
                # Usually exclusion - patient should NOT have T1D
                if criterion_type == "exclusion":
                    result["match_status"] = "MATCH" if has_t1d else "NO_MATCH"
                    result["reasoning"] = f"Patient {'has' if has_t1d else 'does not have'} Type 1 Diabetes"
                else:
                    result["match_status"] = "MATCH" if has_t1d else "NO_MATCH"
            elif "type 2 diabetes" in criterion_text:
                result["match_status"] = "MATCH" if has_t2d else "NO_MATCH"
                result["reasoning"] = f"Patient {'has' if has_t2d else 'does not have'} Type 2 Diabetes"

            result["confidence"] = 0.95 if (has_t1d or has_t2d) else 0.7
            result["patient_data_used"] = {"field": "diagnoses", "value": [d.get("condition") for d in diagnoses]}

        # Medication check (e.g., metformin)
        elif any(med in criterion_text for med in ["metformin", "insulin"]):
            medications = patient_profile.get("medications", [])
            med_names = [m.get("drug_name", "").lower() for m in medications]

            if "metformin" in criterion_text:
                has_metformin = any("metformin" in m for m in med_names)
                result["patient_data_used"] = {"field": "medications", "value": med_names}

                if criterion_type == "inclusion":
                    result["match_status"] = "MATCH" if has_metformin else "NO_MATCH"
                else:
                    result["match_status"] = "MATCH" if has_metformin else "NO_MATCH"

                result["confidence"] = 0.9
                result["reasoning"] = f"Patient {'is' if has_metformin else 'is not'} on metformin"

            elif "insulin" in criterion_text:
                has_insulin = any("insulin" in m for m in med_names)
                result["patient_data_used"] = {"field": "medications", "value": med_names}

                if criterion_type == "exclusion":
                    # Exclusion: should NOT be on insulin
                    result["match_status"] = "MATCH" if has_insulin else "NO_MATCH"
                else:
                    result["match_status"] = "MATCH" if has_insulin else "NO_MATCH"

                result["confidence"] = 0.9
                result["reasoning"] = f"Patient {'is' if has_insulin else 'is not'} on insulin"

        # Pregnancy check
        elif "pregnant" in criterion_text or "pregnancy" in criterion_text:
            lifestyle = patient_profile.get("lifestyle", {})
            pregnancy_status = lifestyle.get("pregnancy_status", "").lower()
            sex = patient_profile.get("demographics", {}).get("sex", "").lower()

            if sex == "male":
                result["match_status"] = "NO_MATCH"  # Males can't be pregnant
                result["confidence"] = 1.0
                result["reasoning"] = "Patient is male, pregnancy not applicable"
            elif pregnancy_status in ["pregnant", "yes", "true"]:
                result["match_status"] = "MATCH" if criterion_type == "inclusion" else "MATCH"
                result["confidence"] = 0.95
                result["reasoning"] = "Patient is pregnant"
            elif pregnancy_status in ["not_pregnant", "no", "false", "not_applicable"]:
                result["match_status"] = "NO_MATCH" if criterion_type == "exclusion" else "NO_MATCH"
                result["confidence"] = 0.95
                result["reasoning"] = "Patient is not pregnant"
            else:
                result["match_status"] = "UNCERTAIN"
                result["confidence"] = 0.5
                result["reasoning"] = "Pregnancy status unclear"

            result["patient_data_used"] = {"field": "pregnancy_status", "value": pregnancy_status}

        return result

    def _check_age_criterion(self, criterion_text: str, age: int) -> bool:
        """Check if age meets criterion."""
        # Extract age range from text like "Age 18-75 years"
        match = re.search(r'(\d+)\s*[-–to]+\s*(\d+)', criterion_text)
        if match:
            min_age, max_age = int(match.group(1)), int(match.group(2))
            return min_age <= age <= max_age

        # Check for minimum age
        match = re.search(r'(?:≥|>=|at least|minimum)\s*(\d+)', criterion_text)
        if match:
            return age >= int(match.group(1))

        # Check for maximum age
        match = re.search(r'(?:≤|<=|at most|maximum)\s*(\d+)', criterion_text)
        if match:
            return age <= int(match.group(1))

        return True  # Default to match if can't parse

    def _check_range_criterion(self, criterion_text: str, value: float) -> bool:
        """Check if value is within a specified range."""
        # Extract range like "between 7.0% and 10.0%"
        match = re.search(r'between\s*([\d.]+)\s*%?\s*and\s*([\d.]+)', criterion_text)
        if match:
            min_val, max_val = float(match.group(1)), float(match.group(2))
            return min_val <= value <= max_val

        # Extract range like "7.0-10.0%"
        match = re.search(r'([\d.]+)\s*[-–]\s*([\d.]+)\s*%?', criterion_text)
        if match:
            min_val, max_val = float(match.group(1)), float(match.group(2))
            return min_val <= value <= max_val

        return True

    def _check_threshold_criterion(self, criterion_text: str, value: float) -> bool:
        """Check if value meets a threshold criterion."""
        # Check for >= or ≥
        match = re.search(r'(?:≥|>=)\s*([\d.]+)', criterion_text)
        if match:
            return value >= float(match.group(1))

        # Check for <= or ≤
        match = re.search(r'(?:≤|<=)\s*([\d.]+)', criterion_text)
        if match:
            return value <= float(match.group(1))

        # Check for >
        match = re.search(r'>\s*([\d.]+)', criterion_text)
        if match:
            return value > float(match.group(1))

        # Check for <
        match = re.search(r'<\s*([\d.]+)', criterion_text)
        if match:
            return value < float(match.group(1))

        return True

    def _get_lab_value(self, patient_profile: Dict[str, Any], test_name: str) -> Optional[float]:
        """Get a lab value from patient profile."""
        for lab in patient_profile.get("lab_values", []):
            if test_name.lower() in lab.get("test_name", "").lower():
                return lab.get("value")
        return None
