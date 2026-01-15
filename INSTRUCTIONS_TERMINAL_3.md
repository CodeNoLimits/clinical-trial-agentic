# TERMINAL 3 - API + Tests

## Rôle
Ce terminal gère l'API FastAPI et tous les tests unitaires.

## Instructions d'Exécution

### 1. Setup Initial

```bash
# Naviguer vers le projet
cd ~/Desktop/clinical-trial-agentic

# Activer l'environnement
source venv/bin/activate
```

### 2. Lancer l'API FastAPI

```bash
# Lancer l'API en mode développement
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

L'API sera disponible à:
- http://localhost:8000
- Documentation: http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json

### 3. Tester les Endpoints (dans un autre terminal ou via curl)

```bash
# Health check
curl http://localhost:8000/health

# Lister les trials
curl http://localhost:8000/trials

# Screening (exemple)
curl -X POST http://localhost:8000/screen \
  -H "Content-Type: application/json" \
  -d '{
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
    "trial_id": "NCT_TEST_001"
  }'
```

### 4. Créer et Exécuter les Tests

```bash
# Créer le fichier de test
cat > tests/test_api.py << 'EOF'
"""Tests for the FastAPI endpoints."""
import pytest
from httpx import AsyncClient
from src.api.main import app

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

@pytest.mark.asyncio
async def test_list_trials():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/trials")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
EOF

# Créer __init__.py pour tests
touch tests/__init__.py

# Exécuter les tests
python -m pytest tests/test_api.py -v
```

### 5. Tests des Agents

```bash
cat > tests/test_agents.py << 'EOF'
"""Tests for the agent system."""
import pytest
from src.agents.supervisor import SupervisorAgent

def test_supervisor_creation():
    agent = SupervisorAgent()
    assert agent is not None
    assert agent.workflow is not None

def test_initial_state_creation():
    agent = SupervisorAgent()
    state = agent._create_initial_state(
        patient_data={"patient_id": "PT001"},
        trial_protocol="Test protocol",
        trial_id="NCT001"
    )
    assert state["patient_data"]["patient_id"] == "PT001"
    assert state["trial_id"] == "NCT001"
    assert state["current_step"] == "CRITERIA_EXTRACTION"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
EOF

# Exécuter
python -m pytest tests/test_agents.py -v
```

### 6. Tests de la Base de Données

```bash
cat > tests/test_database.py << 'EOF'
"""Tests for the database module."""
import pytest
from src.database.chromadb_client import ChromaDBClient
from src.database.embeddings import EmbeddingManager

def test_chromadb_client():
    client = ChromaDBClient()
    stats = client.get_collection_stats()
    assert "trials" in stats
    assert "notes" in stats
    assert "knowledge" in stats

def test_embedding_manager():
    manager = EmbeddingManager()
    assert manager.embedding_dim > 0

    embedding = manager.embed_text("test text")
    assert len(embedding) == manager.embedding_dim

def test_chunking():
    manager = EmbeddingManager()
    text = """
    INCLUSION CRITERIA:
    1. Age 18-75 years
    2. Diabetes diagnosis

    EXCLUSION CRITERIA:
    1. Pregnancy
    """
    chunks = manager.chunk_protocol(text)
    assert len(chunks) > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
EOF

python -m pytest tests/test_database.py -v
```

### 7. Exécuter Tous les Tests

```bash
# Tous les tests avec coverage
python -m pytest tests/ -v --cov=src --cov-report=html

# Voir le rapport de couverture
open htmlcov/index.html  # macOS
```

### 8. Fichiers Concernés

```
src/api/
├── main.py              # Application FastAPI
├── routes/              # Endpoints additionnels
└── schemas/             # Schémas Pydantic

tests/
├── __init__.py
├── test_api.py          # Tests API
├── test_agents.py       # Tests agents
├── test_database.py     # Tests database
├── test_scoring.py      # Tests scoring
└── fixtures/            # Données de test
```

## Synchronisation

Mettre à jour SYNC_MULTI_TERMINAL.md avec ton statut.

---
**Terminal 3 - API + Tests**
