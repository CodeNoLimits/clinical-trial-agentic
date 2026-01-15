# Architecture

## System Overview

The Clinical Trial Eligibility Screening system uses a multi-agent architecture orchestrated by LangGraph.

```
+------------------------------------------------------------------+
|                    CLINICAL TRIAL SCREENING                       |
+------------------------------------------------------------------+
|                                                                    |
|  +----------------+     +--------------------------------+         |
|  |   PATIENT      |     |       VECTOR DATABASE          |         |
|  |    DATA        |     |         (ChromaDB)             |         |
|  |   (JSON)       |     |                                |         |
|  +-------+--------+     |  +---------------------------+ |         |
|          |              |  | clinical_trials           | |         |
|          |              |  | clinical_notes            | |         |
|          |              |  | medical_knowledge         | |         |
|          |              |  +---------------------------+ |         |
|          |              +----------------+---------------+         |
|          |                               |                         |
|          v                               v                         |
|  +-------------------------------------------------------+         |
|  |              SUPERVISOR AGENT (LangGraph)              |         |
|  |                                                        |         |
|  |   Step 1: Extract eligibility criteria                 |         |
|  |   Step 2: Analyze patient profile                      |         |
|  |   Step 3: RAG query for medical context                |         |
|  |   Step 4: Match criterion by criterion                 |         |
|  |   Step 5: Calculate confidence score                   |         |
|  |   Step 6: Generate AI explanation                      |         |
|  |                                                        |         |
|  +------------------------+-------------------------------+         |
|                           |                                         |
|                           v                                         |
|  +-------------------------------------------------------+         |
|  |                       OUTPUT                           |         |
|  |                                                        |         |
|  |  +------------+  +-------------+  +-----------------+  |         |
|  |  | DECISION   |  | CONFIDENCE  |  | EXPLAINABILITY  |  |         |
|  |  | ELIGIBLE   |  |   SCORE     |  |     TABLE       |  |         |
|  |  | INELIGIBLE |  |  0-100%     |  |                 |  |         |
|  |  | UNCERTAIN  |  |             |  |                 |  |         |
|  |  +------------+  +-------------+  +-----------------+  |         |
|  +-------------------------------------------------------+         |
|                                                                    |
+--------------------------------------------------------------------+
```

## Components

### 1. Supervisor Agent

The main orchestrator using LangGraph's StateGraph:

```python
class SupervisorAgent:
    def __init__(self):
        self.graph = StateGraph(ScreeningState)

        # Add nodes for each step
        self.graph.add_node("extract_criteria", self.extract_criteria)
        self.graph.add_node("profile_patient", self.profile_patient)
        self.graph.add_node("rag_retrieval", self.rag_retrieval)
        self.graph.add_node("match_criteria", self.match_criteria)
        self.graph.add_node("calculate_confidence", self.calculate_confidence)
        self.graph.add_node("generate_explanation", self.generate_explanation)

        # Define edges
        self.graph.add_edge("extract_criteria", "profile_patient")
        self.graph.add_edge("profile_patient", "rag_retrieval")
        # ... etc
```

### 2. Vector Database (ChromaDB)

Three collections for different data types:

| Collection | Content | Purpose |
|------------|---------|---------|
| `clinical_trials` | Protocol documents | Criteria retrieval |
| `clinical_notes` | Patient records | Context enrichment |
| `medical_knowledge` | Medical literature | Evidence support |

### 3. RAG Retrieval Engine

Hybrid approach combining:

- **BM25**: Sparse retrieval for exact matches
- **Dense**: Semantic embeddings (all-MiniLM-L6-v2)
- **RRF**: Reciprocal Rank Fusion for combining results

```python
class HybridRetriever:
    def retrieve(self, query: str, top_k: int = 10):
        bm25_results = self.bm25_search(query, top_k)
        dense_results = self.dense_search(query, top_k)
        return self.rrf_fusion(bm25_results, dense_results)
```

### 4. Confidence Scoring

Self-consistency based scoring with calibration:

```python
confidence = base_score * consistency_factor * missing_data_penalty

# Where:
# - base_score: Average from 5 independent generations
# - consistency_factor: Agreement level multiplier
# - missing_data_penalty: Reduction for incomplete data
```

### 5. Explainability Generator

FDA/EMA compliant output including:

- Decision (ELIGIBLE | INELIGIBLE | UNCERTAIN)
- Confidence score with interpretation
- Criterion-level breakdown table
- Clinical narrative
- Evidence citations

## Data Flow

```
1. Input
   |
   +-- Patient JSON data
   +-- Trial protocol ID
   |
2. Criteria Extraction
   |
   +-- Parse inclusion criteria
   +-- Parse exclusion criteria
   |
3. Patient Profiling
   |
   +-- Extract demographics
   +-- Extract diagnoses
   +-- Extract medications
   +-- Extract lab values
   |
4. RAG Retrieval
   |
   +-- Query relevant context
   +-- Enrich patient profile
   |
5. Criterion Matching
   |
   +-- For each criterion:
       +-- Match patient data
       +-- Determine status (MATCH | NO_MATCH | UNCERTAIN)
   |
6. Confidence Calculation
   |
   +-- Generate 5 independent assessments
   +-- Calculate agreement
   +-- Apply calibration
   |
7. Output Generation
   |
   +-- Final decision
   +-- Confidence score
   +-- Explainability table
   +-- Clinical narrative
```

## API Architecture

```
+------------------+
|    Streamlit     |
|       UI         |
+--------+---------+
         |
         v
+--------+---------+
|    FastAPI       |
|   REST API       |
+--------+---------+
         |
    +----+----+
    |         |
    v         v
+---+---+ +---+----+
|Agents | |ChromaDB|
+-------+ +--------+
```

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/screen` | POST | Single patient screening |
| `/api/trials` | GET | List available trials |
| `/api/trials/{id}` | GET | Get trial details |
| `/api/health` | GET | System health check |

## Technology Stack

| Layer | Technology |
|-------|------------|
| Orchestration | LangGraph |
| LLM | Gemini / OpenAI |
| Vector DB | ChromaDB |
| API | FastAPI |
| UI | Streamlit |
| Embeddings | sentence-transformers |

## Security Considerations

- Patient data anonymization
- API authentication (JWT)
- Audit logging
- HIPAA compliance considerations
- Encrypted data at rest
