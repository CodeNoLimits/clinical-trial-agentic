"""
Knowledge Agent

Queries the RAG system for medical context and knowledge.
This is Step 3 of the 6-step screening workflow.
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

from .prompts.system_prompts import KNOWLEDGE_AGENT_PROMPT


class KnowledgeAgent:
    """
    Agent responsible for retrieving medical context from the knowledge base.

    Queries the RAG system to retrieve:
    - Clinical guidelines for patient's conditions
    - Drug interaction information
    - Contraindication data
    - Disease staging criteria
    """

    def __init__(self, model_name: Optional[str] = None):
        """Initialize the knowledge agent."""
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

        # Initialize retriever
        self.retriever = None
        self._init_retriever()

    def _init_retriever(self):
        """Initialize the hybrid retriever."""
        try:
            from ..database.retrieval import HybridRetriever
            self.retriever = HybridRetriever()
        except Exception as e:
            print(f"Warning: Could not initialize retriever: {e}")
            self.retriever = None

    async def query(
        self,
        patient_profile: Dict[str, Any],
        trial_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Query the knowledge base for relevant medical context.

        Args:
            patient_profile: Structured patient profile
            trial_context: Optional trial-specific context

        Returns:
            Dictionary with retrieved medical context
        """
        # Build queries based on patient profile
        queries = self._build_queries(patient_profile)

        # Execute retrieval
        retrieved_context = []
        if self.retriever:
            for query in queries[:5]:  # Limit queries
                try:
                    results = await self.retriever.search(query, top_k=3)
                    retrieved_context.extend(results)
                except Exception as e:
                    print(f"Retrieval error for query '{query}': {e}")

        # Synthesize context if LLM available
        if self.llm and retrieved_context:
            return await self._synthesize_context(
                patient_profile, retrieved_context, queries
            )

        # Return raw context if no LLM
        return {
            "queries_executed": queries,
            "retrieved_context": retrieved_context,
            "drug_interactions": [],
            "relevant_guidelines": [],
            "potential_concerns": []
        }

    def _build_queries(self, patient_profile: Dict[str, Any]) -> List[str]:
        """
        Build search queries based on patient profile.

        Args:
            patient_profile: Patient profile

        Returns:
            List of search queries
        """
        queries = []

        # Queries for diagnoses
        for dx in patient_profile.get("diagnoses", []):
            condition = dx.get("condition", "")
            if condition:
                queries.append(f"Clinical guidelines for {condition}")
                queries.append(f"Eligibility criteria {condition}")

        # Queries for medications (drug interactions)
        medications = patient_profile.get("medications", [])
        drug_names = [m.get("drug_name", "") for m in medications if m.get("drug_name")]

        if len(drug_names) >= 2:
            queries.append(f"Drug interactions between {' and '.join(drug_names[:3])}")

        for drug in drug_names[:3]:
            queries.append(f"{drug} contraindications clinical trial")

        # Queries for lab values
        for lab in patient_profile.get("lab_values", []):
            test_name = lab.get("test_name", "")
            if test_name:
                queries.append(f"{test_name} eligibility criteria clinical trial")

        return queries

    async def _synthesize_context(
        self,
        patient_profile: Dict[str, Any],
        retrieved_context: List[Dict[str, Any]],
        queries: List[str]
    ) -> Dict[str, Any]:
        """
        Synthesize retrieved context using LLM.

        Args:
            patient_profile: Patient profile
            retrieved_context: Raw retrieved documents
            queries: Queries that were executed

        Returns:
            Synthesized medical context
        """
        context_text = "\n".join([
            f"- {ctx.get('document', str(ctx))[:500]}"
            for ctx in retrieved_context[:10]
        ])

        messages = [
            SystemMessage(content=KNOWLEDGE_AGENT_PROMPT),
            HumanMessage(content=f"""
Synthesize the following retrieved medical context for the patient:

Patient Profile Summary:
- Diagnoses: {[d.get('condition') for d in patient_profile.get('diagnoses', [])]}
- Medications: {[m.get('drug_name') for m in patient_profile.get('medications', [])]}
- Key Labs: {[(l.get('test_name'), l.get('value')) for l in patient_profile.get('lab_values', [])]}

Retrieved Context:
{context_text}

Queries Executed:
{queries}

Return a JSON object with:
- queries_executed: list of queries
- retrieved_context: summarized context items
- drug_interactions: any identified interactions
- relevant_guidelines: applicable clinical guidelines
- potential_concerns: any safety concerns identified

Return ONLY valid JSON.
""")
        ]

        try:
            response = await self.llm.ainvoke(messages)
            content = response.content

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            return json.loads(content.strip())

        except Exception as e:
            print(f"Context synthesis failed: {e}")
            return {
                "queries_executed": queries,
                "retrieved_context": [{"summary": str(ctx)[:200]} for ctx in retrieved_context[:5]],
                "drug_interactions": [],
                "relevant_guidelines": [],
                "potential_concerns": []
            }

    def check_drug_interaction(
        self,
        drug1: str,
        drug2: str,
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Check for interaction between two drugs in the retrieved context.

        Args:
            drug1: First drug name
            drug2: Second drug name
            context: Retrieved medical context

        Returns:
            Interaction info if found, None otherwise
        """
        interactions = context.get("drug_interactions", [])

        drug1_lower = drug1.lower()
        drug2_lower = drug2.lower()

        for interaction in interactions:
            drugs = interaction.get("drug_pair", [])
            if len(drugs) >= 2:
                if (drug1_lower in drugs[0].lower() and drug2_lower in drugs[1].lower()) or \
                   (drug2_lower in drugs[0].lower() and drug1_lower in drugs[1].lower()):
                    return interaction

        return None
