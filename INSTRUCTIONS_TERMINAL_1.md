# TERMINAL 1 - Backend Core (Agent + RAG)

## Rôle
Ce terminal gère le code backend principal: les agents LangGraph et le système RAG.

## Instructions d'Exécution

### 1. Setup Initial

```bash
# Naviguer vers le projet
cd ~/Desktop/clinical-trial-agentic

# Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copier le fichier d'environnement
cp .env.example .env

# Éditer .env et ajouter ta clé API Google
# GOOGLE_API_KEY=ta_cle_ici
```

### 3. Test du Supervisor Agent

```bash
# Tester l'agent superviseur
python -c "
from src.agents.supervisor import SupervisorAgent
import asyncio

async def test():
    agent = SupervisorAgent()
    print('SupervisorAgent initialisé avec succès!')
    print('Workflow créé:', agent.workflow)

asyncio.run(test())
"
```

### 4. Tâches à Compléter

- [ ] Vérifier que tous les agents sont importables
- [ ] Tester le workflow complet avec des données de test
- [ ] Créer des tests unitaires pour les agents

### 5. Fichiers Concernés

```
src/agents/
├── supervisor.py          # Agent principal
├── criteria_extractor.py  # À créer si nécessaire
├── patient_profiler.py    # À créer si nécessaire
├── knowledge_agent.py     # À créer si nécessaire
├── eligibility_matcher.py # À créer si nécessaire
└── prompts/
    └── system_prompts.py  # Prompts système
```

## Synchronisation

Mettre à jour SYNC_MULTI_TERMINAL.md avec ton statut:
- Remplacer ⏳ par 🔄 quand tu commences une tâche
- Remplacer 🔄 par ✅ quand tu termines

---
**Terminal 1 - Backend Core**
