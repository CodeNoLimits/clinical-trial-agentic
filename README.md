# Clinical Trial Eligibility Screening - Agentic Architecture

An AI-powered system for automated clinical trial patient eligibility screening using RAG (Retrieval-Augmented Generation) and multi-agent architecture.

## Overview

This system transforms traditional clinical trial screening from a manual, time-consuming process into an automated, transparent, and explainable AI workflow. Built with LangGraph for multi-agent orchestration and ChromaDB for vector storage.

### Key Features

- **RAG-based Retrieval**: Hybrid search (BM25 + Dense) for accurate medical context retrieval
- **6-Step Agentic Workflow**: Structured screening process with specialized agents
- **Self-Consistency Confidence Scoring**: Multiple assessments for reliable decisions
- **AI Explainability**: FDA/EMA compliant decision explanations
- **Modern UI**: Streamlit interface with real-time visualization

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│           CLINICAL TRIAL ELIGIBILITY - AGENTIC ARCHITECTURE              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   Patient Data ──┬──► Vector Database (ChromaDB)                        │
│                  │    ├── clinical_trials                                │
│                  │    ├── clinical_notes                                 │
│                  │    └── medical_knowledge                              │
│                  │                                                       │
│                  └──► RAG Retrieval (BM25 + Dense + RRF)                │
│                                    │                                     │
│                                    ▼                                     │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                    SUPERVISOR AGENT (LangGraph)                   │   │
│   │                                                                   │   │
│   │   Step 1: Extract eligibility criteria                           │   │
│   │   Step 2: Analyze patient profile                                │   │
│   │   Step 3: Query RAG for medical context                          │   │
│   │   Step 4: Match patient to criteria                              │   │
│   │   Step 5: Calculate confidence score                             │   │
│   │   Step 6: Generate AI explanation                                │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│                                    ▼                                     │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐      │
│   │   DECISION   │  │  CONFIDENCE  │  │  AI EXPLAINABILITY TABLE │      │
│   │  ELIGIBLE    │  │    SCORE     │  │  - Criterion details     │      │
│   │  INELIGIBLE  │  │   0-100%     │  │  - Evidence sources      │      │
│   │  UNCERTAIN   │  │   + Level    │  │  - Reasoning steps       │      │
│   └──────────────┘  └──────────────┘  └──────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────────┘
```

## Installation

### Prerequisites

- Python 3.11+
- Google API Key (for Gemini) or OpenAI API Key

### Quick Start

```bash
# Clone the repository
git clone https://github.com/codenolimits/clinical-trial-agentic.git
cd clinical-trial-agentic

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: .\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Initialize database
python -c "from src.database.chromadb_client import init_database; init_database()"

# Ingest trial protocols
python src/database/ingest_trials.py --melea

# Run the application
streamlit run src/ui/app.py
```

### Docker Installation

```bash
docker-compose up -d
```

## Usage

### Web Interface (Streamlit)

```bash
streamlit run src/ui/app.py
```

Access at `http://localhost:8501`

### REST API

```bash
uvicorn src.api.main:app --reload
```

API documentation at `http://localhost:8000/docs`

### Python SDK

```python
import asyncio
from src.agents.supervisor import SupervisorAgent

async def screen_patient():
    agent = SupervisorAgent()

    result = await agent.screen_patient(
        patient_data={
            "patient_id": "PT001",
            "age": 58,
            "sex": "male",
            "diagnoses": [{"condition": "Type 2 Diabetes"}],
            "medications": [{"drug_name": "Metformin", "dose": "1000mg"}],
            "lab_values": [{"test": "HbA1c", "value": 8.2, "unit": "%"}]
        },
        trial_protocol="...",  # Your protocol text
        trial_id="NCT12345678"
    )

    print(f"Decision: {result['decision']}")
    print(f"Confidence: {result['confidence']:.0%}")

asyncio.run(screen_patient())
```

## The 6-Step Screening Process

### Step 1: Criteria Extraction
Parses trial protocol to extract structured inclusion/exclusion criteria with categories (demographic, clinical, laboratory, medication, etc.).

### Step 2: Patient Profiling
Analyzes patient data to create structured profile with medical entities, diagnoses, medications, and lab values.

### Step 3: Medical Knowledge Retrieval
Queries the vector database using hybrid RAG to retrieve relevant medical context, guidelines, and drug interactions.

### Step 4: Eligibility Matching
Systematically matches patient profile against each criterion with explicit reasoning and evidence citation.

### Step 5: Confidence Scoring
Calculates confidence using:
- Individual criterion confidence aggregation
- Self-consistency across multiple assessments
- Missing data and uncertainty penalties

### Step 6: Explanation Generation
Produces FDA/EMA compliant outputs:
- AI Explainability Table (criterion-by-criterion)
- Clinical narrative for documentation
- Audit trail for regulatory compliance

## Project Structure

```
clinical-trial-agentic/
├── src/
│   ├── agents/           # LangGraph agents
│   │   ├── supervisor.py # Main orchestrator
│   │   └── prompts/      # System prompts
│   ├── database/         # Vector database & RAG
│   │   ├── chromadb_client.py
│   │   ├── embeddings.py
│   │   └── retrieval.py  # Hybrid search
│   ├── api/              # FastAPI REST API
│   ├── scoring/          # Confidence scoring
│   ├── explainability/   # AI explanations
│   └── ui/               # Streamlit interface
├── data/
│   └── trials/           # Trial protocols
├── tests/                # Unit tests
├── docs/                 # Documentation
└── SYNC_MULTI_TERMINAL.md # Multi-terminal coordination
```

## Configuration

### Environment Variables

```env
# LLM Provider
GOOGLE_API_KEY=your_key
LLM_PROVIDER=google
LLM_MODEL=gemini-2.0-flash

# Vector Database
CHROMADB_PERSIST_DIR=./data/chromadb

# Embeddings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Confidence
CONFIDENCE_SAMPLES=5
CONFIDENCE_THRESHOLD=0.80
```

## Performance Metrics

Based on research and validation:

| Metric | Target | Description |
|--------|--------|-------------|
| Accuracy | >93% | Overall decision accuracy |
| Sensitivity | >90% | True positive rate |
| Specificity | >95% | True negative rate |
| Confidence Calibration | ECE <0.1 | Calibration error |

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) file.

## Authors

- **Meléa** - Domain expertise & Clinical validation
- **David (CodeNoLimits)** - Architecture & Implementation
- Built with **Claude Code** (Claude Opus 4.5)

## Acknowledgments

- Original project by Meléa: [clinical_trial-eligibility](https://github.com/Melea1/clinical_trial-eligibility)
- MIMIC-IV dataset for patient data
- LangChain/LangGraph for agent orchestration
- ChromaDB for vector storage

## References

- [RAG in Healthcare - MDPI 2025](https://www.mdpi.com/2673-2688/6/9/226)
- [LangGraph Multi-Agent Workflows](https://langchain-ai.github.io/langgraph/)
- [FDA AI Guidance 2025](https://www.greenlight.guru/blog/fda-guidance-ai-enabled-devices)
- [Clinical Trial Eligibility Standards - CDISC](https://www.cdisc.org/standards)

---

**Built for academic excellence and clinical impact.**
