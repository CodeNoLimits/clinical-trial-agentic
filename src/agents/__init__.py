"""
Agents Module - LangGraph-based Multi-Agent System

This module implements the 6-step screening process using specialized agents:
1. CriteriaExtractor - Extract eligibility criteria from trial protocols
2. PatientProfiler - Analyze and structure patient data
3. KnowledgeAgent - Query RAG for medical context
4. EligibilityMatcher - Match patient to criteria
5. ConfidenceScorer - Calculate confidence scores
6. ExplanationGenerator - Generate AI explainability table

The SupervisorAgent orchestrates all agents using LangGraph.
"""

from .supervisor import SupervisorAgent, create_screening_workflow
from .criteria_extractor import CriteriaExtractorAgent
from .patient_profiler import PatientProfilerAgent
from .knowledge_agent import KnowledgeAgent
from .eligibility_matcher import EligibilityMatcherAgent

__all__ = [
    "SupervisorAgent",
    "create_screening_workflow",
    "CriteriaExtractorAgent",
    "PatientProfilerAgent",
    "KnowledgeAgent",
    "EligibilityMatcherAgent",
]
