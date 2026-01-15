# Clinical Trial Agentic - Synchronisation Multi-Terminaux

## Vue d'Ensemble du Projet

**Projet**: Clinical Trial Eligibility Screening - Architecture Agentique
**Date de création**: 2026-01-15
**Équipe**: Meléa + David (CodeNoLimits)
**Repo source**: https://github.com/Melea1/clinical_trial-eligibility
**Repo cible**: https://github.com/codenolimits/clinical-trial-agentic

---

## Architecture Cible

```
┌─────────────────────────────────────────────────────────────────────────┐
│           CLINICAL TRIAL ELIGIBILITY - AGENTIC ARCHITECTURE              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌─────────────┐     ┌─────────────────────────────────────────────┐   │
│   │   PATIENT   │     │              VECTOR DATABASE                 │   │
│   │    DATA     │     │         (ChromaDB/Pinecone)                  │   │
│   │   (JSON)    │     │                                              │   │
│   └──────┬──────┘     │  ┌─────────────────────────────────────┐    │   │
│          │            │  │ Collection: clinical_trials          │    │   │
│          │            │  │ - Protocol documents                 │    │   │
│          │            │  │ - Eligibility criteria               │    │   │
│          │            │  └─────────────────────────────────────┘    │   │
│          │            │                                              │   │
│          │            │  ┌─────────────────────────────────────┐    │   │
│          │            │  │ Collection: clinical_notes           │    │   │
│          │            │  │ - Patient records (anonymized)       │    │   │
│          │            │  │ - Medical history                    │    │   │
│          │            │  └─────────────────────────────────────┘    │   │
│          │            └─────────────────────────────────────────────┘   │
│          │                                │                              │
│          │                                ▼                              │
│          │            ┌─────────────────────────────────────────────┐   │
│          │            │           RAG RETRIEVAL ENGINE                │   │
│          │            │  BM25 + Dense (MedEmbed) + RRF Fusion        │   │
│          │            └─────────────────────────────────────────────┘   │
│          │                                │                              │
│          ▼                                ▼                              │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                    SUPERVISOR AGENT (LangGraph)                   │   │
│   │                                                                   │   │
│   │   ÉTAPE 1: Extraction des critères d'éligibilité                 │   │
│   │   ÉTAPE 2: Analyse du profil patient                             │   │
│   │   ÉTAPE 3: Requête RAG pour contexte médical                     │   │
│   │   ÉTAPE 4: Matching critère par critère                          │   │
│   │   ÉTAPE 5: Calcul du score de confiance                          │   │
│   │   ÉTAPE 6: Génération de l'explication AI                        │   │
│   │                                                                   │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                │                                         │
│                                ▼                                         │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                      OUTPUT                                       │   │
│   │                                                                   │   │
│   │   ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │   │
│   │   │  DECISION    │  │  CONFIDENCE  │  │  AI EXPLAINABILITY   │  │   │
│   │   │              │  │    SCORE     │  │       TABLE          │  │   │
│   │   │ - ELIGIBLE   │  │              │  │                      │  │   │
│   │   │ - INELIGIBLE │  │  0% - 100%   │  │ - Criterion details  │  │   │
│   │   │ - UNCERTAIN  │  │              │  │ - Evidence sources   │  │   │
│   │   │              │  │ + Calibration│  │ - Reasoning steps    │  │   │
│   │   └──────────────┘  └──────────────┘  └──────────────────────┘  │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Configuration des 4 Terminaux

### Comment synchroniser les terminaux

Chaque terminal travaille sur une tâche spécifique et met à jour ce fichier avec son statut. Les terminaux lisent ce fichier pour coordonner leurs actions.

| Terminal | Rôle | Dossier de travail |
|----------|------|-------------------|
| **T1** | Backend Core (Agent + RAG) | `src/agents/` |
| **T2** | Vector Database + Embeddings | `src/database/` |
| **T3** | API + Tests | `src/api/` + `tests/` |
| **T4** | UI + Documentation | `src/ui/` + `docs/` |

---

## 🚨 ACTIONS EN ATTENTE DE T1 (Résumé Exécutif)

| # | De | Proposition | Question Clé | Section |
|---|-----|-------------|--------------|---------|
| 1 | T2 | Self-Correcting Agentic RAG | Ajouter `evaluate_retrieval_quality()` ? | §T2→T1 |
| 2 | T4 | Visualisation Workflow RAG | WebSocket ou polling ? | §T4 Visualisation |
| 3 | T4 | Intégration Claude Cowork | Interface avec LangGraph ? | §T4→T1 Cowork |
| 4 | T2 | Batch Processing (Cowork) | Architecture pour N patients ? | §Cowork Briefing |

**⚠️ T1: Voir les sections détaillées plus bas pour les propositions complètes.**

---

## Statut en Temps Réel

### Phase 1: Setup Initial
| Tâche | Terminal | Statut | Notes |
|-------|----------|--------|-------|
| Fork repo Meléa | T1 | 🔄 EN COURS | Clonage vers codenolimits |
| Structure projet | T1 | ⏳ ATTENTE | Après fork |
| Requirements.txt | T1 | ⏳ ATTENTE | - |
| ChromaDB setup | T2 | ✅ TERMINÉ | v1.4.1 - 3 collections créées |
| API FastAPI | T3 | ⏳ ATTENTE | - |
| UI Streamlit | T4 | ✅ TERMINÉ | Lancé sur port 8501 |

### Phase 2: Core Implementation
| Tâche | Terminal | Statut | Notes |
|-------|----------|--------|-------|
| Supervisor Agent | T1 | ⏳ ATTENTE | LangGraph |
| 6 étapes agent | T1 | ⏳ ATTENTE | System prompt |
| Embeddings MedEmbed | T2 | ✅ TERMINÉ | all-MiniLM-L6-v2, dim=384 |
| Ingest protocols | T2 | ✅ TERMINÉ | 3 trials, 23 chunks |
| REST endpoints | T3 | ⏳ ATTENTE | - |
| Tests unitaires | T3 | ⏳ ATTENTE | - |

### Phase 3: Scoring & Explainability
| Tâche | Terminal | Statut | Notes |
|-------|----------|--------|-------|
| Confidence scoring | T1 | ⏳ ATTENTE | Self-consistency |
| AI Explainability | T1 | ⏳ ATTENTE | SHAP + narratives |
| Results storage | T2 | ⏳ ATTENTE | ChromaDB ready |
| API documentation | T3 | ⏳ ATTENTE | OpenAPI |

### Phase 4: UI & Documentation
| Tâche | Terminal | Statut | Notes |
|-------|----------|--------|-------|
| Streamlit advanced | T4 | ✅ TERMINÉ | CSS + App lancée |
| Doc universitaire | T4 | ✅ TERMINÉ | results.md + conclusion.md |
| MkDocs config | T4 | ✅ TERMINÉ | mkdocs.yml + tous les docs |
| Antigravity prep | T4 | ⏳ ATTENTE | Phase 2 UI |

---

## Instructions par Terminal

### Terminal 1 (T1) - Backend Core

```bash
# Démarrer dans ce terminal
cd ~/Desktop/clinical-trial-agentic
# Travailler sur: src/agents/

# Commandes:
# 1. Vérifier le statut sync
cat SYNC_MULTI_TERMINAL.md | grep "T1"

# 2. Mettre à jour le statut (via Claude)
# Demander à Claude de mettre à jour ce fichier

# 3. Tests locaux
python -m pytest tests/test_agents.py -v
```

### Terminal 2 (T2) - Vector Database

```bash
# Démarrer dans ce terminal
cd ~/Desktop/clinical-trial-agentic
# Travailler sur: src/database/

# Commandes:
# 1. Lancer ChromaDB local
python -c "import chromadb; client = chromadb.Client(); print('ChromaDB OK')"

# 2. Ingest des documents
python src/database/ingest_trials.py

# 3. Test retrieval
python src/database/test_retrieval.py
```

### Terminal 3 (T3) - API + Tests

```bash
# Démarrer dans ce terminal
cd ~/Desktop/clinical-trial-agentic
# Travailler sur: src/api/ + tests/

# Commandes:
# 1. Lancer l'API
uvicorn src.api.main:app --reload --port 8000

# 2. Tests API
python -m pytest tests/test_api.py -v

# 3. Docs API
open http://localhost:8000/docs
```

### Terminal 4 (T4) - UI + Docs

```bash
# Démarrer dans ce terminal
cd ~/Desktop/clinical-trial-agentic
# Travailler sur: src/ui/ + docs/

# Commandes:
# 1. Lancer Streamlit
streamlit run src/ui/app.py

# 2. Build docs
cd docs && mkdocs serve

# 3. Préparation Antigravity
# (À venir en Phase 2)
```

---

## Structure du Projet

```
clinical-trial-agentic/
├── SYNC_MULTI_TERMINAL.md    # Ce fichier de synchronisation
├── README.md                  # Documentation principale
├── requirements.txt           # Dépendances Python
├── .env.example              # Variables d'environnement
├── docker-compose.yml        # Orchestration conteneurs
│
├── src/
│   ├── agents/               # T1 - Agents LangGraph
│   │   ├── __init__.py
│   │   ├── supervisor.py     # Agent superviseur principal
│   │   ├── criteria_extractor.py
│   │   ├── patient_profiler.py
│   │   ├── knowledge_agent.py
│   │   ├── eligibility_matcher.py
│   │   └── prompts/
│   │       └── system_prompts.py
│   │
│   ├── database/             # T2 - Vector Database
│   │   ├── __init__.py
│   │   ├── chromadb_client.py
│   │   ├── embeddings.py     # MedEmbed / ModernBERT
│   │   ├── ingest_trials.py  # Ingestion protocoles
│   │   └── retrieval.py      # Hybrid search + RRF
│   │
│   ├── api/                  # T3 - FastAPI
│   │   ├── __init__.py
│   │   ├── main.py           # Application FastAPI
│   │   ├── routes/
│   │   │   ├── screening.py
│   │   │   └── trials.py
│   │   └── schemas/
│   │       ├── patient.py
│   │       └── eligibility.py
│   │
│   ├── scoring/              # T1 - Scoring & Confidence
│   │   ├── __init__.py
│   │   ├── confidence.py     # Self-consistency scoring
│   │   └── calibration.py    # Probability calibration
│   │
│   ├── explainability/       # T1 - AI Explainability
│   │   ├── __init__.py
│   │   ├── shap_explainer.py
│   │   ├── narrative_generator.py
│   │   └── explainability_table.py
│   │
│   └── ui/                   # T4 - Interface utilisateur
│       ├── __init__.py
│       ├── app.py            # Streamlit app
│       ├── components/
│       │   ├── patient_form.py
│       │   ├── results_display.py
│       │   └── explainability_view.py
│       └── styles/
│           └── custom.css
│
├── data/                     # Données
│   ├── trials/               # Protocoles d'essais (Meléa)
│   │   ├── NCT06864546_Glutotrack.md
│   │   ├── DECLARE_TIMI58.md
│   │   └── NCT05928572_CGM_Initiation.md
│   ├── patients/             # Données patients anonymisées
│   └── embeddings/           # Cache embeddings
│
├── tests/                    # T3 - Tests
│   ├── __init__.py
│   ├── test_agents.py
│   ├── test_database.py
│   ├── test_api.py
│   ├── test_scoring.py
│   └── fixtures/
│       ├── sample_patient.json
│       └── sample_trial.md
│
├── docs/                     # T4 - Documentation
│   ├── mkdocs.yml
│   ├── index.md
│   ├── architecture.md
│   ├── user_guide.md
│   ├── api_reference.md
│   └── university_report/    # Rapport universitaire
│       ├── introduction.md
│       ├── methodology.md
│       ├── implementation.md
│       ├── results.md
│       └── conclusion.md
│
└── scripts/                  # Scripts utilitaires
    ├── setup.sh
    ├── migrate_from_melea.sh
    └── run_all_tests.sh
```

---

## Les 6 Étapes de l'Agent

Voici les 6 étapes que le Supervisor Agent exécute pour chaque screening:

### Étape 1: Extraction des Critères d'Éligibilité
- **Input**: Document protocole de l'essai clinique
- **Output**: Liste structurée des critères inclusion/exclusion
- **Agent**: CriteriaExtractor
- **RAG**: Query sur collection `clinical_trials`

### Étape 2: Analyse du Profil Patient
- **Input**: Données patient (JSON)
- **Output**: Profil structuré avec entités médicales extraites
- **Agent**: PatientProfiler
- **Extraction**: Âge, médicaments, comorbidités, labs

### Étape 3: Requête RAG pour Contexte Médical
- **Input**: Entités médicales du patient
- **Output**: Contexte clinique enrichi
- **Agent**: KnowledgeAgent
- **RAG**: Hybrid search (BM25 + Dense + Reranking)

### Étape 4: Matching Critère par Critère
- **Input**: Critères + Profil patient + Contexte
- **Output**: Match status pour chaque critère
- **Agent**: EligibilityMatcher
- **Status**: MATCH | NO_MATCH | UNCERTAIN | MISSING_DATA

### Étape 5: Calcul du Score de Confiance
- **Input**: Résultats du matching
- **Output**: Score de confiance global (0-100%)
- **Méthode**: Self-consistency (5 générations)
- **Calibration**: Temperature scaling

### Étape 6: Génération de l'Explication AI
- **Input**: Tous les résultats précédents
- **Output**: Table AI Explainability + Narrative
- **Format**:
  - Décision finale (ELIGIBLE | INELIGIBLE | UNCERTAIN)
  - Table détaillée par critère
  - Narrative clinique
  - Sources et preuves

---

## Variables d'Environnement

```env
# .env.example
# Copier vers .env et remplir

# LLM API
GOOGLE_API_KEY=your_gemini_api_key
# ou
OPENAI_API_KEY=your_openai_key

# Vector Database
CHROMADB_HOST=localhost
CHROMADB_PORT=8001
# ou Pinecone pour production
PINECONE_API_KEY=your_pinecone_key
PINECONE_ENVIRONMENT=us-east-1

# Embeddings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
# ou pour médical:
# EMBEDDING_MODEL=abhinand/MedEmbed-base-v0.1

# API
API_HOST=0.0.0.0
API_PORT=8000

# UI
STREAMLIT_PORT=8501
```

---

## Commandes de Démarrage

### Installation complète

```bash
# 1. Cloner le projet
git clone https://github.com/codenolimits/clinical-trial-agentic.git
cd clinical-trial-agentic

# 2. Créer environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: .\venv\Scripts\activate  # Windows

# 3. Installer dépendances
pip install -r requirements.txt

# 4. Configurer environnement
cp .env.example .env
# Éditer .env avec vos clés API

# 5. Initialiser ChromaDB
python src/database/init_db.py

# 6. Ingérer les données
python src/database/ingest_trials.py

# 7. Lancer l'API
uvicorn src.api.main:app --reload

# 8. Lancer l'UI (autre terminal)
streamlit run src/ui/app.py
```

### Avec Docker

```bash
docker-compose up -d
```

---

## Historique des Mises à Jour

| Date | Terminal | Action | Résultat |
|------|----------|--------|----------|
| 2026-01-15 | T1 | Création fichier sync | ✅ |
| 2026-01-15 | - | Deep Research complète | ✅ |
| 2026-01-15 | T4 | CSS custom.css créé | ✅ |
| 2026-01-15 | T4 | Doc universitaire (results + conclusion) | ✅ |
| 2026-01-15 | T4 | MkDocs config + docs complets | ✅ |
| 2026-01-15 | T4 | Streamlit lancé port 8501 | ✅ |
| 2026-01-15 | T2 | ChromaDB v1.4.1 initialisé | ✅ |
| 2026-01-15 | T2 | Embeddings (MiniLM-L6-v2, 384d) | ✅ |
| 2026-01-15 | T2 | 3 protocoles ingérés (23 chunks) | ✅ |
| 2026-01-15 | T2 | Retrieval hybride (BM25+Dense+RRF) testé | ✅ |
| 2026-01-15 | T4 | Recherche Claude Cowork pour intégration | 📝 |
| 2026-01-15 | T2 | Deep Research: Self-Correcting Agentic RAG | ✅ |
| 2026-01-15 | T2 | Proposition architecture intégration T2↔T1 | 📝 |
| 2026-01-15 | T2 | Briefing Claude Cowork ajouté au SYNC | ✅ |
| 2026-01-15 | T4 | Proposition visualisation RAG workflow | 📝 |
| 2026-01-15 | T4 | Sommaire exécutif pour T1 ajouté | ✅ |
| | | | |

---

## 💡 Proposition T4 → T1 : Intégration Claude Cowork

**Context**: Claude Cowork est le nouvel agent Anthropic pour workflows fichiers locaux.

**Proposition pour Phase 2**:
1. Utiliser Cowork pour automatiser le batch processing des patients
2. Intégration avec notre UI Streamlit via file watchers
3. Génération automatique de rapports PDF depuis les screenings

**Question pour T1**: Est-ce que l'architecture agent actuelle (LangGraph) pourrait s'interfacer avec Cowork pour déléguer des sous-tâches ?

**Statut**: En attente de réponse T1

---

## 🔗 Proposition T2 → T1 : Intégration RAG + LangGraph (Self-Correcting Agentic RAG)

**Recherche effectuée**: Deep Research sur les meilleures pratiques RAG médical 2025

### Architecture Recommandée (basée sur Frontiers Medical 2025)

```
┌─────────────────────────────────────────────────────────────┐
│                    LANGGRAPH SUPERVISOR                      │
│                                                              │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│   │  STATE   │───→│ RETRIEVE │───→│ EVALUATE │──┐          │
│   │  OBJECT  │    │  (T2)    │    │  QUALITY │  │          │
│   └──────────┘    └──────────┘    └──────────┘  │          │
│        ↑                               │        │          │
│        │         ┌──────────┐         ↓        │          │
│        └─────────│  REFINE  │←── SUFFICIENT? ──┘          │
│                  │  QUERY   │      (NO)                    │
│                  └──────────┘                              │
│                               │                            │
│                              (YES)                         │
│                               ↓                            │
│                  ┌──────────────────┐                      │
│                  │ GENERATE ANSWER  │                      │
│                  │ + EXPLAINABILITY │                      │
│                  └──────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

### Intégration Concrète T2 ↔ T1

**Ce que T2 fournit (PRÊT)**:
- `HybridRetriever.search_hybrid()` - Recherche BM25 + Dense + RRF
- `EmbeddingManager.embed_text()` - Génération embeddings 384d
- `ChromaDBClient.query_trials()` - Accès direct aux collections

**Ce que T1 doit implémenter**:
1. **State Object** avec champs: `query`, `retrieved_docs`, `confidence_score`, `iteration_count`
2. **Evaluate Node** qui vérifie si les résultats RAG sont suffisants (score > 0.7)
3. **Refine Node** qui reformule la query si insuffisant (max 3 itérations)
4. **Self-Consistency** via dual-model validation (comme dans l'article Frontiers)

### Code d'intégration suggéré pour T1

```python
# Dans src/agents/supervisor.py

from src.database.retrieval import HybridRetriever

class RAGIntegrationNode:
    def __init__(self):
        self.retriever = HybridRetriever()
        self.retriever.build_bm25_index()
        self.max_iterations = 3

    async def retrieve_with_refinement(self, state: dict) -> dict:
        query = state["current_query"]
        iteration = state.get("iteration", 0)

        # Retrieve
        results = self.retriever.search_hybrid(query, top_k=5)

        # Evaluate quality
        avg_score = sum(r.score for r in results) / len(results) if results else 0

        if avg_score < 0.7 and iteration < self.max_iterations:
            # Refine query and retry
            state["iteration"] = iteration + 1
            state["needs_refinement"] = True
        else:
            state["retrieved_context"] = [r.document for r in results]
            state["retrieval_scores"] = [r.score for r in results]
            state["needs_refinement"] = False

        return state
```

### Sources de la recherche
- [Frontiers: Self-correcting Agentic Graph RAG](https://www.frontiersin.org/journals/medicine/articles/10.3389/fmed.2025.1716327/full)
- [PubMed: GUIDE-RAG Framework](https://pubmed.ncbi.nlm.nih.gov/39812777/)
- [LangChain RAG Docs](https://docs.langchain.com/oss/python/langchain/rag)

**Question pour T1**: Voulez-vous que j'ajoute une méthode `evaluate_retrieval_quality()` dans le module retrieval.py qui retourne un score de qualité ?

**Statut**: ⏳ En attente de réponse T1

---

## 🎨 Proposition T4 : Visualisation du Workflow RAG dans l'UI

**En réponse à T2**: Voici comment l'UI peut visualiser le Self-Correcting RAG.

### Composant UI proposé

```python
# src/ui/components/rag_workflow_view.py

def render_rag_workflow(state: dict):
    """Visualise le workflow RAG en temps réel"""

    st.subheader("🔄 RAG Workflow Progress")

    # Progress bar pour les itérations
    iteration = state.get("iteration", 0)
    st.progress(iteration / 3, text=f"Iteration {iteration}/3")

    # Quality gauge
    if state.get("retrieval_scores"):
        avg_score = sum(state["retrieval_scores"]) / len(state["retrieval_scores"])
        color = "green" if avg_score >= 0.7 else "orange"
        st.metric("Retrieval Quality", f"{avg_score:.0%}", delta_color=color)

    # Documents récupérés (expandable)
    with st.expander("📄 Retrieved Documents"):
        for i, doc in enumerate(state.get("retrieved_context", [])):
            st.markdown(f"**Doc {i+1}** - Score: {state['retrieval_scores'][i]:.2f}")
```

### Mockup Interface

```
┌─────────────────────────────────────────┐
│  🔄 RAG Workflow Progress               │
│  ████████░░░░░░░░░░░░  Iteration 1/3    │
│                                         │
│  Quality: ████████░░ 78% ✅ Sufficient  │
│                                         │
│  📄 Retrieved Documents (3)      [▼]    │
│  ├─ NCT06864546_Glutotrack.md (0.89)   │
│  ├─ eligibility_criteria.txt (0.82)    │
│  └─ patient_guidelines.md (0.71)       │
└─────────────────────────────────────────┘
```

**Question pour T1**: WebSocket pour streaming temps réel, ou polling simple ?

**Statut**: ⏳ En attente validation T1

---

# ═══════════════════════════════════════════════════════════════════════════════
# 🤖 BRIEFING CLAUDE COWORK - Section Isolée
# ═══════════════════════════════════════════════════════════════════════════════

> **Note aux Terminaux**: Cette section est destinée à Claude Cowork uniquement.
> Ne pas modifier sauf pour ajouter des requêtes ou des réponses Cowork.

## 📋 Contexte du Projet

**Projet**: Clinical Trial Eligibility Screening - Architecture Agentique
**But**: Système automatisé pour déterminer l'éligibilité des patients aux essais cliniques
**Stack**: Python 3.11 + LangGraph + ChromaDB + FastAPI + Streamlit

## 🏗️ Architecture Actuelle

```
clinical-trial-agentic/
├── src/
│   ├── agents/          # T1 - LangGraph Supervisor (6 étapes)
│   ├── database/        # T2 - ChromaDB + RAG ✅ TERMINÉ
│   ├── api/             # T3 - FastAPI endpoints
│   ├── scoring/         # T1 - Confidence + Calibration
│   ├── explainability/  # T1 - SHAP + Narratives
│   └── ui/              # T4 - Streamlit ✅ LANCÉ
├── data/
│   ├── trials/          # 3 protocoles ingérés (23 chunks)
│   └── chromadb/        # Vector DB persistante
└── tests/
```

## ✅ Ce qui est TERMINÉ (T2 - Vector Database)

| Composant | Version | Détails |
|-----------|---------|---------|
| ChromaDB | 1.4.1 | 3 collections: trials, notes, knowledge |
| Embeddings | MiniLM-L6-v2 | Dimension 384, sentence-transformers |
| Retrieval | Hybride | BM25 + Dense + RRF Fusion |
| Données | 23 chunks | 3 protocoles (Diabetes, Hypertension, Test) |

### API disponible pour intégration

```python
from src.database.retrieval import HybridRetriever
from src.database.embeddings import EmbeddingManager
from src.database.chromadb_client import ChromaDBClient

# Recherche hybride
retriever = HybridRetriever()
retriever.build_bm25_index()
results = retriever.search_hybrid("diabetes HbA1c criteria", top_k=5)

# Chaque résultat contient:
# - document: str (le texte)
# - score: float (0-1)
# - source: str ("bm25", "dense", "hybrid")
# - metadata: dict (trial_id, section, etc.)
```

## 🔄 Pattern Self-Correcting RAG Proposé

Basé sur la recherche Frontiers Medical 2025:

```
STATE → RETRIEVE → EVALUATE → [REFINE si score < 0.7] → GENERATE
         (T2)      (T1)         (max 3 iter)           (T1)
```

**Seuil de qualité**: Score moyen > 0.7 = suffisant
**Max itérations**: 3 refinements avant fallback

## ❓ Questions Ouvertes pour Cowork

1. **Batch Processing**: Comment automatiser le screening de plusieurs patients en parallèle?
2. **File Watchers**: Intégration avec Streamlit pour détecter nouveaux fichiers patients?
3. **Rapports PDF**: Génération automatique des rapports d'éligibilité?
4. **Cache Intelligent**: Stratégie de cache pour les embeddings fréquents?

## 📝 Requêtes pour Claude Cowork

> Ajouter ici les tâches spécifiques pour Cowork

### Requête 1: [EN ATTENTE]
**De**: T2
**Sujet**: Optimisation du batch processing des patients
**Détails**: Proposer une architecture pour traiter N patients en parallèle avec le RAG existant
**Priorité**: Moyenne

---

# ═══════════════════════════════════════════════════════════════════════════════
# FIN SECTION COWORK
# ═══════════════════════════════════════════════════════════════════════════════

---

## Notes pour Meléa

### Ce qui change par rapport à ton projet original:

1. **Architecture**: Passage de zero-shot prompting simple à architecture agentique avec LangGraph
2. **Stockage**: CSV → Vector Database (ChromaDB/Pinecone) avec RAG
3. **Scoring**: Ajout d'un système de confidence avec self-consistency
4. **Explainability**: Nouvelle table AI Explainability avec SHAP + narratives
5. **UI**: Streamlit amélioré, puis migration vers Antigravity (Phase 2)

### Tes fichiers préservés:
- `trials/` → Migrés vers `data/trials/`
- `patients_for_trial_screening.csv` → Convertis en JSON dans `data/patients/`
- `screening_utils.py` → Intégré dans les nouveaux modules

---

## Contact & Support

- **David (CodeNoLimits)**: Coordination générale + Backend
- **Meléa**: Domain expertise + Validation clinique
- **Claude Code**: Architecture + Implémentation

Pour toute question, mettre à jour ce fichier avec un commentaire dans la section appropriée.
