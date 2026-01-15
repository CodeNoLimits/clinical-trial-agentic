# PROMPT ANTIGRAVITY - Clinical Trial Eligibility Screening UI

## Contexte du Projet

Tu vas créer une interface utilisateur sophistiquée pour un système de screening d'éligibilité aux essais cliniques. Ce système utilise une architecture agentique avec RAG (Retrieval-Augmented Generation).

### Backend Existant

Le backend est déjà implémenté avec :
- **FastAPI** sur `http://localhost:8000`
- **Endpoints disponibles** :
  - `POST /screen` - Screening d'un patient
  - `GET /trials` - Liste des essais
  - `GET /health` - Health check

### Architecture du Système

```
┌─────────────────────────────────────────────────────────────────────────┐
│           CLINICAL TRIAL ELIGIBILITY SCREENING SYSTEM                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ANTIGRAVITY UI ←──────────────────────────────────────────────┐       │
│   (Ce que tu vas créer)                                          │       │
│         │                                                        │       │
│         ▼                                                        │       │
│   ┌─────────────────┐                                           │       │
│   │   FastAPI       │ ← Déjà implémenté                         │       │
│   │   REST API      │                                           │       │
│   └────────┬────────┘                                           │       │
│            │                                                     │       │
│            ▼                                                     │       │
│   ┌─────────────────────────────────────────────────────────┐   │       │
│   │   SUPERVISOR AGENT (LangGraph)                           │   │       │
│   │   6 étapes de screening automatisées                     │   │       │
│   └─────────────────────────────────────────────────────────┘   │       │
│                                                                  │       │
│   ┌─────────────────────────────────────────────────────────┐   │       │
│   │   OUTPUT:                                                │   │       │
│   │   - Decision: ELIGIBLE / INELIGIBLE / UNCERTAIN         │ ──┘       │
│   │   - Confidence Score: 0-100%                            │           │
│   │   - AI Explainability Table                             │           │
│   │   - Clinical Narrative                                  │           │
│   └─────────────────────────────────────────────────────────┘           │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Spécifications UI

### 1. Page d'Accueil / Dashboard

**Layout** : Design médical professionnel, clean, confiance

**Sections** :
```
┌─────────────────────────────────────────────────────────────────────────┐
│  HEADER                                                                  │
│  Logo + "Clinical Trial Eligibility Screening" + Menu Navigation        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │  SCREENINGS     │  │  TRIALS         │  │  PATIENTS       │         │
│  │  Today: 12      │  │  Active: 5      │  │  Processed: 156 │         │
│  │  Pending: 3     │  │  Total: 23      │  │  Eligible: 67   │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  QUICK ACTIONS                                                    │  │
│  │  [+ New Screening]  [Upload Batch]  [View Reports]               │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  RECENT SCREENINGS                                                │  │
│  │  ┌────────┬─────────┬──────────┬────────────┬─────────────────┐  │  │
│  │  │ ID     │ Patient │ Trial    │ Decision   │ Confidence      │  │  │
│  │  ├────────┼─────────┼──────────┼────────────┼─────────────────┤  │  │
│  │  │ SCR001 │ PT_058  │ NCT123   │ ✅ ELIGIBLE │ 94%            │  │  │
│  │  │ SCR002 │ PT_059  │ NCT456   │ ❌ INELIG.  │ 97%            │  │  │
│  │  │ SCR003 │ PT_060  │ NCT123   │ ⚠️ UNCERT. │ 72%            │  │  │
│  │  └────────┴─────────┴──────────┴────────────┴─────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2. Page de Screening (Principale)

**Layout en 2 colonnes** :

```
┌─────────────────────────────────────────────────────────────────────────┐
│  NEW SCREENING                                                           │
├────────────────────────────────┬────────────────────────────────────────┤
│                                │                                         │
│  PATIENT DATA                  │  TRIAL SELECTION                        │
│  ─────────────                 │  ────────────────                       │
│                                │                                         │
│  [Form View] [JSON View]       │  Trial ID: [________] 🔍               │
│                                │                                         │
│  Demographics                  │  ┌─────────────────────────────────┐   │
│  ┌──────────────────────────┐ │  │ NCT12345678                      │   │
│  │ Patient ID: [________]   │ │  │ Type 2 Diabetes Study            │   │
│  │ Age:        [____] years │ │  │ Phase 3 | Active                 │   │
│  │ Sex:        [▼ Male    ] │ │  │ 12 criteria | Last updated 2024 │   │
│  └──────────────────────────┘ │  └─────────────────────────────────┘   │
│                                │                                         │
│  Diagnoses                     │  OR                                     │
│  ┌──────────────────────────┐ │                                         │
│  │ + Add Diagnosis          │ │  [📤 Upload Protocol]                   │
│  │ ┌────────────────────┐   │ │                                         │
│  │ │ Type 2 Diabetes    │❌ │ │  [📋 Paste Protocol Text]               │
│  │ │ ICD-10: E11.9      │   │ │                                         │
│  │ └────────────────────┘   │ │                                         │
│  └──────────────────────────┘ │                                         │
│                                │                                         │
│  Medications                   │                                         │
│  ┌──────────────────────────┐ │                                         │
│  │ + Add Medication         │ │                                         │
│  │ ┌────────────────────┐   │ │                                         │
│  │ │ Metformin 1000mg   │❌ │ │                                         │
│  │ │ Twice daily        │   │ │                                         │
│  │ └────────────────────┘   │ │                                         │
│  └──────────────────────────┘ │                                         │
│                                │                                         │
│  Lab Values                    │                                         │
│  ┌──────────────────────────┐ │                                         │
│  │ + Add Lab Value          │ │                                         │
│  │ ┌────────────────────┐   │ │                                         │
│  │ │ HbA1c: 8.2%        │❌ │ │                                         │
│  │ │ Date: 2024-01-15   │   │ │                                         │
│  │ └────────────────────┘   │ │                                         │
│  └──────────────────────────┘ │                                         │
│                                │                                         │
├────────────────────────────────┴────────────────────────────────────────┤
│                                                                          │
│  [         🔬 RUN ELIGIBILITY SCREENING         ]                       │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3. Page de Résultats

**Design impact visuel pour la décision** :

```
┌─────────────────────────────────────────────────────────────────────────┐
│  SCREENING RESULTS                                           [📤 Export]│
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                                                                   │  │
│  │           ████████████████████████████████████████               │  │
│  │           █                                      █               │  │
│  │           █         ✅  ELIGIBLE                █               │  │
│  │           █                                      █               │  │
│  │           ████████████████████████████████████████               │  │
│  │                                                                   │  │
│  │           Confidence: 94%  │  Level: HIGH                        │  │
│  │           Human Review: Not Required                              │  │
│  │                                                                   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌────────────────────────────┐  ┌────────────────────────────────┐   │
│  │ CONFIDENCE GAUGE           │  │ CRITERIA SUMMARY               │   │
│  │                            │  │                                │   │
│  │     ╭────────────╮        │  │  Inclusion: 6/6 ✅             │   │
│  │    ╱              ╲       │  │  Exclusion: 0/5 ✅             │   │
│  │   │   ███  94%    │       │  │  Uncertain: 0                  │   │
│  │    ╲              ╱       │  │  Missing: 1                    │   │
│  │     ╰────────────╯        │  │                                │   │
│  │  ░░░░░░████████████       │  │  [View Details →]              │   │
│  │  70%        90%    100%   │  │                                │   │
│  └────────────────────────────┘  └────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  AI EXPLAINABILITY TABLE                                         │  │
│  │  ────────────────────────                                        │  │
│  │                                                                   │  │
│  │  ┌────────┬─────────────────────┬─────────┬────────┬──────────┐ │  │
│  │  │ ID     │ Criterion           │ Patient │ Status │ Confid.  │ │  │
│  │  ├────────┼─────────────────────┼─────────┼────────┼──────────┤ │  │
│  │  │ INC_01 │ Age 18-75 years     │ 58      │ ✅     │ 100%     │ │  │
│  │  │ INC_02 │ Type 2 Diabetes     │ E11.9   │ ✅     │ 100%     │ │  │
│  │  │ INC_03 │ HbA1c 7.0-10.0%     │ 8.2%    │ ✅     │ 100%     │ │  │
│  │  │ INC_04 │ Metformin ≥1000mg   │ 1000mg  │ ✅     │ 95%      │ │  │
│  │  │ EXC_01 │ Type 1 Diabetes     │ No      │ ✅     │ 100%     │ │  │
│  │  │ EXC_02 │ Pregnancy           │ N/A     │ ✅     │ 100%     │ │  │
│  │  │ EXC_03 │ eGFR < 30           │ 85      │ ✅     │ 100%     │ │  │
│  │  └────────┴─────────────────────┴─────────┴────────┴──────────┘ │  │
│  │                                                                   │  │
│  │  [Expand Row for Full Reasoning]                                 │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  CLINICAL NARRATIVE                                              │  │
│  │  ───────────────────                                             │  │
│  │                                                                   │  │
│  │  "The patient has been assessed as ELIGIBLE for clinical trial   │  │
│  │   NCT12345678 with 94% confidence. The patient, a 58-year-old   │  │
│  │   male with Type 2 Diabetes Mellitus (ICD-10: E11.9), meets all │  │
│  │   inclusion criteria: age within range (18-75), HbA1c of 8.2%   │  │
│  │   within target (7.0-10.0%), and stable metformin therapy at    │  │
│  │   1000mg twice daily. No exclusion criteria were met. The       │  │
│  │   patient's eGFR of 85 mL/min/1.73m² confirms adequate renal    │  │
│  │   function. Recommend proceeding with standard enrollment."      │  │
│  │                                                                   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        │
│  │ [📄 PDF Report] │  │ [📊 CSV Export] │  │ [🔄 New Screen] │        │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘        │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4. Codes Couleur et États

```css
/* Décisions */
ELIGIBLE:    #28a745 (vert)     - background gradient vers #20c997
INELIGIBLE:  #dc3545 (rouge)    - background gradient vers #c82333
UNCERTAIN:   #ffc107 (jaune)    - background gradient vers #e0a800

/* Confidence Levels */
HIGH:        #28a745 (vert)     ≥90%
MODERATE:    #17a2b8 (bleu)     80-89%
LOW:         #ffc107 (jaune)    70-79%
VERY_LOW:    #dc3545 (rouge)    <70%

/* Status Icons */
MATCH:        ✅ (vert)
NO_MATCH:     ❌ (rouge)
UNCERTAIN:    ⚠️ (jaune)
MISSING_DATA: ❓ (gris)
```

### 5. Composants Réutilisables

#### PatientCard
```
┌────────────────────────────┐
│ 👤 Patient PT_058          │
│ ───────────────            │
│ Age: 58 | Sex: Male        │
│ Dx: Type 2 Diabetes        │
│ Meds: Metformin 1000mg     │
│ Labs: HbA1c 8.2%           │
└────────────────────────────┘
```

#### TrialCard
```
┌────────────────────────────┐
│ 🔬 NCT12345678             │
│ ───────────────            │
│ Type 2 Diabetes Study      │
│ Phase 3 | Active           │
│ 6 inclusion | 5 exclusion  │
│ [Select Trial]             │
└────────────────────────────┘
```

#### ConfidenceGauge
```
     ╭────────────╮
    ╱    94%      ╲
   │   ████████   │
    ╲   HIGH     ╱
     ╰────────────╯
```

#### CriterionRow (expandable)
```
┌────────────────────────────────────────────────────────────────┐
│ ▶ INC_01 | Age 18-75 years | 58 | ✅ MATCH | 100%             │
├────────────────────────────────────────────────────────────────┤
│ (Expanded)                                                      │
│ Reasoning: Patient age (58) is within required range (18-75).  │
│ Evidence: Patient demographics record, DOB: 1966-03-15         │
│ Confidence: 100% - exact numeric comparison                    │
│ Concerns: None                                                  │
└────────────────────────────────────────────────────────────────┘
```

---

## API Endpoints à Utiliser

### POST /screen
```json
// Request
{
  "patient": {
    "patient_id": "PT001",
    "age": 58,
    "sex": "male",
    "diagnoses": [{"condition": "Type 2 Diabetes", "icd10": "E11.9"}],
    "medications": [{"drug_name": "Metformin", "dose": "1000mg"}],
    "lab_values": [{"test": "HbA1c", "value": 8.2, "unit": "%"}],
    "medical_history": [],
    "lifestyle": {}
  },
  "trial_id": "NCT12345678",
  "trial_protocol": "..." // Optional, fetched from DB if not provided
}

// Response
{
  "screening_id": "SCR-20240115-PT001",
  "trial_id": "NCT12345678",
  "patient_id": "PT001",
  "decision": "ELIGIBLE",
  "confidence": 0.94,
  "confidence_level": "HIGH",
  "requires_human_review": false,
  "explainability_table": [
    {
      "criterion_id": "INC_01",
      "criterion_text": "Age 18-75 years",
      "patient_value": "58",
      "match_status": "MATCH",
      "confidence": 1.0,
      "reasoning": "Patient age (58) is within required range (18-75)."
    }
  ],
  "clinical_narrative": "The patient has been assessed as ELIGIBLE...",
  "processing_time_ms": 3450,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### GET /trials
```json
// Response
[
  {
    "trial_id": "NCT12345678",
    "title": "Type 2 Diabetes Study",
    "condition": "Type 2 Diabetes Mellitus",
    "document_count": 15
  }
]
```

### GET /health
```json
// Response
{
  "status": "healthy",
  "version": "1.0.0",
  "database_status": "OK (3 trials indexed)",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## Fonctionnalités Requises

### Must Have (MVP)
1. ✅ Formulaire de saisie patient
2. ✅ Sélection/upload de trial
3. ✅ Affichage décision avec confidence
4. ✅ Table d'explainability
5. ✅ Export PDF/CSV

### Nice to Have
1. Mode JSON pour power users
2. Batch upload (CSV)
3. Historique des screenings
4. Graphiques de distribution
5. Mode sombre

### Future (Phase 3)
1. Intégration FHIR directe
2. Notifications temps réel
3. Multi-langue
4. Comparaison multi-trials

---

## Stack Technique Recommandée

```
Frontend:
- React 18+ ou Next.js 14+
- Tailwind CSS pour le styling
- Framer Motion pour les animations
- Recharts ou Chart.js pour les graphiques
- React Hook Form pour les formulaires

État:
- Zustand ou Jotai (léger)
- React Query pour le cache API

Autres:
- Axios pour les appels API
- React-PDF pour export
- Date-fns pour les dates
```

---

## Notes de Design

### Principes UX Médicaux
1. **Clarté** : Les décisions doivent être immédiatement compréhensibles
2. **Confiance** : Design professionnel, pas de distractions
3. **Sécurité** : Confirmation avant actions importantes
4. **Accessibilité** : WCAG 2.1 AA minimum
5. **Audit** : Tout doit être traçable

### Responsive
- Desktop first (utilisateurs principaux: coordinateurs cliniques)
- Tablette supportée
- Mobile: lecture seule des résultats

---

## Contact Backend

```
API Base URL: http://localhost:8000
Documentation: http://localhost:8000/docs
Health Check: http://localhost:8000/health
```

---

**Ce prompt est prêt pour Antigravity. L'UI doit se connecter au backend FastAPI existant.**
