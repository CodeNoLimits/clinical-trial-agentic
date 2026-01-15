# Méthodologie

## 1. Architecture Système

### 1.1 Vue d'Ensemble

L'architecture proposée suit un paradigme multi-agent basé sur LangGraph, avec séparation claire des responsabilités:

```
┌─────────────────────────────────────────────────────────────────┐
│                    COUCHE PRÉSENTATION                           │
│   Streamlit UI ←→ FastAPI REST ←→ Clients externes              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    COUCHE ORCHESTRATION                          │
│   Supervisor Agent (LangGraph StateGraph)                       │
│   - Gestion d'état                                               │
│   - Routage conditionnel                                         │
│   - Checkpointing                                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    COUCHE AGENTS SPÉCIALISÉS                     │
│   ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐      │
│   │ Criteria  │ │ Patient   │ │ Knowledge │ │ Matcher   │      │
│   │ Extractor │ │ Profiler  │ │ Agent     │ │ Agent     │      │
│   └───────────┘ └───────────┘ └───────────┘ └───────────┘      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    COUCHE DONNÉES                                │
│   ChromaDB (Vector Store) ←→ Embeddings (MedEmbed)              │
│   - clinical_trials                                              │
│   - medical_knowledge                                            │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Choix Technologiques

| Composant | Technologie | Justification |
|-----------|-------------|---------------|
| Orchestration | LangGraph | State management, checkpointing, debugging |
| LLM | Gemini 2.0 Flash | Balance performance/coût, contexte 1M tokens |
| Vector DB | ChromaDB | Open-source, HNSW performant, simple déploiement |
| Embeddings | MiniLM-L6-v2 | Baseline rapide (production: MedEmbed) |
| Retrieval | BM25 + Dense | Hybride pour terminologie médicale exacte |
| API | FastAPI | Async natif, documentation auto, validation Pydantic |
| UI | Streamlit | Prototypage rapide, composants interactifs |

## 2. Le Workflow en 6 Étapes

### Étape 1: Extraction des Critères

**Objectif**: Parser le protocole d'essai pour extraire les critères structurés.

**Méthode**:
- Prompt Chain-of-Thought pour extraction séquentielle
- Catégorisation: DEMOGRAPHIC, CLINICAL, LABORATORY, MEDICATION, MEDICAL_HISTORY, LIFESTYLE
- Normalisation des valeurs numériques et unités

**Output**:
```json
{
  "criterion_id": "INC_001",
  "type": "inclusion",
  "category": "LABORATORY",
  "text": "HbA1c between 7.0% and 10.0%",
  "comparison_operator": "range",
  "values": {"min": 7.0, "max": 10.0, "unit": "%"}
}
```

### Étape 2: Profilage Patient

**Objectif**: Structurer les données patient pour le matching.

**Méthode**:
- Extraction d'entités médicales (NER)
- Normalisation vers standards (ICD-10, ATC, LOINC)
- Identification des données manquantes

### Étape 3: Requête RAG

**Objectif**: Enrichir le contexte avec des connaissances médicales.

**Méthode**:
1. **BM25 (Lexical)**: Pour terminologie médicale exacte
   - Codes médicaments, diagnostics
   - Acronymes (HbA1c, eGFR)

2. **Dense Retrieval (Sémantique)**: Pour similarité conceptuelle
   - Synonymes médicaux
   - Descriptions de symptômes

3. **RRF Fusion**: Reciprocal Rank Fusion pour merger les résultats
   ```
   RRF_score(d) = Σ 1/(k + rank(d))
   ```
   avec k=60 (constante standard)

### Étape 4: Matching d'Éligibilité

**Objectif**: Évaluer chaque critère avec le profil patient.

**Statuts possibles**:
- `MATCH`: Critère satisfait
- `NO_MATCH`: Critère non satisfait
- `UNCERTAIN`: Données ambiguës
- `MISSING_DATA`: Données absentes

**Raisonnement explicite**:
```
1. Critère: "Age 18-75 years"
2. Donnée patient: age = 58
3. Comparaison: 18 ≤ 58 ≤ 75
4. Résultat: MATCH
5. Confiance: 1.0
```

### Étape 5: Scoring de Confiance

**Objectif**: Quantifier la fiabilité de la décision.

**Composantes**:
1. **Confiance individuelle**: Moyenne pondérée des critères
2. **Self-consistency**: N générations indépendantes, taux d'accord
3. **Pénalités**:
   - Missing data: -5% par critère critique
   - Uncertain: -10% par critère critique

**Formule**:
```
Confidence = base_conf × consistency - penalties
```

**Niveaux**:
| Niveau | Score | Action |
|--------|-------|--------|
| HIGH | ≥90% | Procéder |
| MODERATE | 80-89% | Procéder avec monitoring |
| LOW | 70-79% | Revue humaine recommandée |
| VERY_LOW | <70% | Revue humaine obligatoire |

### Étape 6: Génération d'Explication

**Objectif**: Produire documentation conforme FDA/EMA.

**Outputs**:
1. **Décision finale**: ELIGIBLE / INELIGIBLE / UNCERTAIN
2. **Table d'explainability**: Critère par critère
3. **Narrative clinique**: Paragraphe pour documentation
4. **Audit trail**: Timestamp, versions, sources

## 3. Vector Database et RAG

### 3.1 Architecture ChromaDB

**Collections**:
```
clinical_trials/
├── Protocol chunks (semantic)
├── Eligibility criteria (structured)
└── Metadata (NCT, phase, condition)

medical_knowledge/
├── Clinical guidelines
├── Drug interactions
└── Disease staging criteria
```

### 3.2 Chunking Strategy

**Pour protocoles**:
- Section-aware chunking
- Préservation des critères comme unités
- Overlap de 50 tokens pour contexte

**Pour connaissances médicales**:
- Semantic chunking par similarité
- CLEAR entity-aware pour notes cliniques

### 3.3 Hybrid Search Pipeline

```
Query
  │
  ├──► BM25 (Elasticsearch-style)
  │     └── Top 20 lexical matches
  │
  └──► Dense (MiniLM/MedEmbed)
        └── Top 20 semantic matches

        ▼
   RRF Fusion
        │
        ▼
   Top 10 results
```

## 4. Conformité FDA/EMA

### 4.1 Exigences Documentées

- **Transparence**: Explication de chaque décision
- **Traçabilité**: Audit trail complet
- **Reproductibilité**: Mêmes inputs → mêmes outputs
- **Human-in-the-loop**: Revue obligatoire si confiance < 80%

### 4.2 AI Explainability Table

| Champ | Description |
|-------|-------------|
| criterion_id | Identifiant unique |
| criterion_text | Texte original |
| patient_value | Valeur du patient |
| match_status | MATCH/NO_MATCH/UNCERTAIN/MISSING |
| confidence | Score 0-1 |
| evidence_sources | Citations des données |
| reasoning | Étapes de raisonnement |
| concerns | Alertes ou drapeaux |

## 5. Évaluation

### 5.1 Métriques

- **Accuracy**: (TP + TN) / Total
- **Sensitivity**: TP / (TP + FN) - Ne pas exclure patients éligibles
- **Specificity**: TN / (TN + FP) - Ne pas inclure patients non éligibles
- **ECE** (Expected Calibration Error): Qualité de calibration

### 5.2 Dataset de Validation

- Source: MIMIC-IV (dé-identifié)
- Protocoles: NCT ClinicalTrials.gov
- Gold standard: Décisions d'experts cliniques
