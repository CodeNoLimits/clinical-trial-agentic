# Clinical Trial Eligibility Screening

Welcome to the documentation for the **Agentic Clinical Trial Screening System**.

## Overview

This system uses a multi-agent architecture powered by LangGraph to automate clinical trial eligibility screening with:

- **High Accuracy**: >93% target accuracy
- **Explainability**: FDA/EMA compliant decision documentation
- **Confidence Scoring**: Calibrated probability scores
- **RAG Integration**: Hybrid retrieval for medical context

## Quick Start

```bash
# Clone the repository
git clone https://github.com/codenolimits/clinical-trial-agentic.git
cd clinical-trial-agentic

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Launch the UI
streamlit run src/ui/app.py
```

## Architecture

The system implements a 6-step agentic workflow:

1. **Criteria Extraction** - Parse trial protocols
2. **Patient Profiling** - Structure patient data
3. **RAG Retrieval** - Enrich with medical context
4. **Eligibility Matching** - Criterion-by-criterion evaluation
5. **Confidence Scoring** - Self-consistency based scoring
6. **Explainability** - Generate documentation

## Quick Links

| Section | Description |
|---------|-------------|
| [Architecture](architecture.md) | Technical architecture details |
| [User Guide](user_guide.md) | How to use the system |
| [API Reference](api_reference.md) | REST API documentation |
| [University Report](university_report/introduction.md) | Academic documentation |

## Features

### Multi-Agent Orchestration

```
Supervisor Agent
    |
    +-- Criteria Extractor Agent
    +-- Patient Profiler Agent
    +-- Knowledge Agent (RAG)
    +-- Eligibility Matcher Agent
    +-- Confidence Scorer
    +-- Explainability Generator
```

### Hybrid RAG System

- **BM25**: Exact term matching for medical terminology
- **Dense Retrieval**: Semantic similarity with embeddings
- **RRF Fusion**: Reciprocal Rank Fusion for optimal results

### Confidence Scoring

- Self-consistency across 5 generations
- Temperature scaling calibration
- Missing data penalty adjustment

### Explainability

- Criterion-level decision breakdown
- Evidence source citations
- Clinical narrative generation
- Audit trail for compliance

## Team

- **Melea**: Medical domain expertise & clinical validation
- **David (CodeNoLimits)**: Technical architecture & implementation
- **Claude Code**: Development assistance

## License

This project is developed for academic and research purposes.

---

*Built with LangGraph, ChromaDB, FastAPI, and Streamlit*
