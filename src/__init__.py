"""
Clinical Trial Eligibility Screening - Agentic Architecture

This package implements an AI-powered clinical trial eligibility screening system
using RAG (Retrieval-Augmented Generation) and multi-agent architecture.

Architecture:
- Vector Database (ChromaDB) for protocol storage
- LangGraph-based supervisor agent with 6 screening steps
- Confidence scoring with self-consistency
- AI Explainability table for transparent decisions

Authors: Meléa & David (CodeNoLimits)
Date: 2026-01-15
"""

__version__ = "1.0.0"
__author__ = "Meléa & David (CodeNoLimits)"
