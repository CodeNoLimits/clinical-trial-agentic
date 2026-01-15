"""
Criteria Extractor Agent

Extracts and structures eligibility criteria from clinical trial protocols.
This is Step 1 of the 6-step screening workflow.
"""

import os
import json
from typing import Dict, Any, List, Optional

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None

try:
    from langchain_openai import ChatOpenAI
except ImportError:
    ChatOpenAI = None

from langchain_core.messages import SystemMessage, HumanMessage

from .prompts.system_prompts import CRITERIA_EXTRACTOR_PROMPT


class CriteriaExtractorAgent:
    """
    Agent responsible for extracting eligibility criteria from trial protocols.

    Parses inclusion and exclusion criteria into structured format with:
    - Criterion ID
    - Type (inclusion/exclusion)
    - Category (demographic, clinical, laboratory, etc.)
    - Original text
    - Normalized version
    - Required data points
    - Comparison operator
    """

    def __init__(self, model_name: Optional[str] = None):
        """Initialize the criteria extractor agent."""
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

    async def extract(self, protocol_text: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract eligibility criteria from protocol text.

        Args:
            protocol_text: Full protocol document or eligibility section

        Returns:
            Dictionary with 'inclusion_criteria' and 'exclusion_criteria' lists
        """
        if self.llm is None:
            # Fallback to rule-based extraction if no LLM
            return self._extract_rule_based(protocol_text)

        messages = [
            SystemMessage(content=CRITERIA_EXTRACTOR_PROMPT),
            HumanMessage(content=f"""
Extract all eligibility criteria from the following clinical trial protocol:

{protocol_text}

Return a JSON object with 'inclusion_criteria' and 'exclusion_criteria' arrays.
Each criterion should have:
- criterion_id: string (INC_001, EXC_001, etc.)
- type: "inclusion" or "exclusion"
- category: "DEMOGRAPHIC" | "CLINICAL" | "LABORATORY" | "MEDICATION" | "MEDICAL_HISTORY" | "LIFESTYLE"
- text: original criterion text
- normalized: standardized version with explicit values
- required_data_points: list of patient data fields needed
- comparison_operator: "eq" | "gt" | "lt" | "gte" | "lte" | "contains" | "not_contains" | "range"

Return ONLY valid JSON, no markdown formatting.
""")
        ]

        try:
            response = await self.llm.ainvoke(messages)
            content = response.content

            # Clean up response if needed
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            result = json.loads(content.strip())
            return result

        except Exception as e:
            print(f"LLM extraction failed: {e}, falling back to rule-based")
            return self._extract_rule_based(protocol_text)

    def _extract_rule_based(self, protocol_text: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Rule-based extraction fallback when LLM is unavailable.

        Args:
            protocol_text: Protocol text

        Returns:
            Extracted criteria
        """
        import re

        inclusion_criteria = []
        exclusion_criteria = []

        lines = protocol_text.split('\n')
        current_section = None
        criterion_counter = {"inclusion": 0, "exclusion": 0}

        for line in lines:
            line_upper = line.upper().strip()

            # Detect section
            if "INCLUSION" in line_upper and "CRITERIA" in line_upper:
                current_section = "inclusion"
                continue
            elif "EXCLUSION" in line_upper and "CRITERIA" in line_upper:
                current_section = "exclusion"
                continue

            # Skip empty lines
            if not line.strip():
                continue

            # Extract numbered items
            match = re.match(r'^\s*(\d+[\.\)]|\-|\•)\s*(.+)$', line)
            if match and current_section:
                criterion_text = match.group(2).strip()

                if len(criterion_text) < 10:  # Skip too short
                    continue

                criterion_counter[current_section] += 1
                prefix = "INC" if current_section == "inclusion" else "EXC"
                criterion_id = f"{prefix}_{criterion_counter[current_section]:03d}"

                # Determine category
                category = self._categorize_criterion(criterion_text)

                criterion = {
                    "criterion_id": criterion_id,
                    "type": current_section,
                    "category": category,
                    "text": criterion_text,
                    "normalized": criterion_text,
                    "required_data_points": self._extract_data_points(criterion_text),
                    "comparison_operator": self._detect_operator(criterion_text)
                }

                if current_section == "inclusion":
                    inclusion_criteria.append(criterion)
                else:
                    exclusion_criteria.append(criterion)

        return {
            "inclusion_criteria": inclusion_criteria,
            "exclusion_criteria": exclusion_criteria
        }

    def _categorize_criterion(self, text: str) -> str:
        """Categorize a criterion based on its content."""
        text_lower = text.lower()

        if any(w in text_lower for w in ["age", "sex", "gender", "male", "female", "race"]):
            return "DEMOGRAPHIC"
        elif any(w in text_lower for w in ["hba1c", "glucose", "egfr", "creatinine", "alt", "ast", "lab"]):
            return "LABORATORY"
        elif any(w in text_lower for w in ["metformin", "insulin", "medication", "drug", "therapy", "treatment"]):
            return "MEDICATION"
        elif any(w in text_lower for w in ["history", "prior", "previous", "past"]):
            return "MEDICAL_HISTORY"
        elif any(w in text_lower for w in ["pregnant", "smoking", "alcohol", "lifestyle"]):
            return "LIFESTYLE"
        else:
            return "CLINICAL"

    def _extract_data_points(self, text: str) -> List[str]:
        """Extract required patient data points from criterion text."""
        data_points = []
        text_lower = text.lower()

        mapping = {
            "age": "age",
            "hba1c": "lab_hba1c",
            "egfr": "lab_egfr",
            "glucose": "lab_glucose",
            "creatinine": "lab_creatinine",
            "metformin": "medication_metformin",
            "insulin": "medication_insulin",
            "pregnant": "pregnancy_status",
            "diabetes": "diagnosis_diabetes",
            "bmi": "bmi",
        }

        for keyword, data_point in mapping.items():
            if keyword in text_lower:
                data_points.append(data_point)

        return data_points if data_points else ["general"]

    def _detect_operator(self, text: str) -> str:
        """Detect comparison operator from criterion text."""
        text_lower = text.lower()

        if "between" in text_lower or "-" in text_lower:
            return "range"
        elif any(w in text_lower for w in ["≥", ">=", "at least", "minimum"]):
            return "gte"
        elif any(w in text_lower for w in ["≤", "<=", "at most", "maximum"]):
            return "lte"
        elif any(w in text_lower for w in [">", "greater than", "more than"]):
            return "gt"
        elif any(w in text_lower for w in ["<", "less than"]):
            return "lt"
        elif any(w in text_lower for w in ["no ", "not ", "without", "absence"]):
            return "not_contains"
        else:
            return "contains"
