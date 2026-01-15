# TERMINAL 2 - Vector Database + Embeddings

## Rôle
Ce terminal gère ChromaDB, les embeddings et l'ingestion des données.

## Instructions d'Exécution

### 1. Setup Initial

```bash
# Naviguer vers le projet
cd ~/Desktop/clinical-trial-agentic

# Activer l'environnement (déjà créé par Terminal 1)
source venv/bin/activate
```

### 2. Initialiser ChromaDB

```bash
# Tester ChromaDB
python -c "
import chromadb
client = chromadb.Client()
print('ChromaDB OK!')
print('Version:', chromadb.__version__)
"

# Initialiser les collections
python -c "
from src.database.chromadb_client import init_database
db = init_database()
print('Collections créées:', db.get_collection_stats())
"
```

### 3. Tester les Embeddings

```bash
python -c "
from src.database.embeddings import EmbeddingManager

manager = EmbeddingManager()
print('Embedding dimension:', manager.embedding_dim)

# Test embedding
test = 'Type 2 Diabetes with HbA1c 8.5%'
emb = manager.embed_text(test)
print('Test embedding OK, len:', len(emb))
"
```

### 4. Copier les Protocoles de Meléa

```bash
# Créer le dossier data/trials si pas existant
mkdir -p data/trials

# Copier les fichiers de Meléa (si disponibles)
# Ou créer un fichier de test:
cat > data/trials/NCT_TEST_001.md << 'EOF'
# Test Clinical Trial NCT_TEST_001

## INCLUSION CRITERIA
1. Age 18-75 years
2. Diagnosis of Type 2 Diabetes Mellitus
3. HbA1c between 7.0% and 10.0%
4. Currently on stable metformin therapy (≥1000mg/day) for at least 3 months

## EXCLUSION CRITERIA
1. Type 1 Diabetes
2. Pregnant or nursing women
3. Severe renal impairment (eGFR < 30 mL/min/1.73m²)
4. Current use of insulin therapy
5. History of diabetic ketoacidosis
EOF
```

### 5. Ingérer les Protocoles

```bash
# Ingérer un fichier
python src/database/ingest_trials.py --file data/trials/NCT_TEST_001.md

# Ou ingérer tout le dossier
python src/database/ingest_trials.py --directory data/trials/

# Vérifier l'ingestion
python -c "
from src.database.chromadb_client import ChromaDBClient
db = ChromaDBClient()
print('Stats après ingestion:', db.get_collection_stats())
"
```

### 6. Tester le Retrieval Hybride

```bash
python -c "
from src.database.retrieval import HybridRetriever

retriever = HybridRetriever()
retriever.build_bm25_index()

# Test query
results = retriever.search_hybrid('diabetes HbA1c criteria', top_k=3)
print('Résultats:', len(results))
for r in results:
    print(f'  Score: {r.score:.4f} - {r.document[:50]}...')
"
```

### 7. Fichiers Concernés

```
src/database/
├── chromadb_client.py  # Client ChromaDB
├── embeddings.py       # Génération embeddings
├── retrieval.py        # Recherche hybride RAG
└── ingest_trials.py    # Ingestion protocoles

data/
├── trials/             # Protocoles d'essais
├── patients/           # Données patients (test)
└── chromadb/           # Persistence ChromaDB
```

## Synchronisation

Mettre à jour SYNC_MULTI_TERMINAL.md avec ton statut.

---
**Terminal 2 - Vector Database**
