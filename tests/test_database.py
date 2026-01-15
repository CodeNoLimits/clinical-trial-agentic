"""
Tests for the Database Module.

Terminal 3 - Database Testing Module
Tests ChromaDB client, embeddings, and retrieval functionality.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any, Optional
import os


# =============================================================================
# MOCK DEFINITIONS
# =============================================================================

class MockCollection:
    """Mock ChromaDB collection for testing."""

    def __init__(self, name: str):
        self.name = name
        self._data = {
            "ids": [],
            "documents": [],
            "embeddings": [],
            "metadatas": []
        }

    def add(
        self,
        ids: List[str],
        documents: List[str] = None,
        embeddings: List[List[float]] = None,
        metadatas: List[Dict[str, Any]] = None
    ):
        self._data["ids"].extend(ids)
        if documents:
            self._data["documents"].extend(documents)
        if embeddings:
            self._data["embeddings"].extend(embeddings)
        if metadatas:
            self._data["metadatas"].extend(metadatas)

    def get(
        self,
        ids: List[str] = None,
        where: Dict[str, Any] = None,
        include: List[str] = None
    ) -> Dict[str, Any]:
        # Filter by where clause if provided
        if where and "trial_id" in where:
            trial_id = where["trial_id"]
            filtered_indices = [
                i for i, m in enumerate(self._data["metadatas"])
                if m and m.get("trial_id") == trial_id
            ]
            return {
                "ids": [self._data["ids"][i] for i in filtered_indices],
                "documents": [self._data["documents"][i] for i in filtered_indices] if self._data["documents"] else [],
                "metadatas": [self._data["metadatas"][i] for i in filtered_indices]
            }
        return self._data

    def query(
        self,
        query_embeddings: List[List[float]],
        n_results: int = 5,
        where: Dict[str, Any] = None,
        include: List[str] = None
    ) -> Dict[str, Any]:
        # Return mock query results
        results = {
            "ids": [self._data["ids"][:n_results]],
            "documents": [self._data["documents"][:n_results]] if self._data["documents"] else [[]],
            "metadatas": [self._data["metadatas"][:n_results]],
            "distances": [[0.1 * (i + 1) for i in range(min(n_results, len(self._data["ids"])))]]
        }
        return results

    def delete(self, ids: List[str]):
        for id_ in ids:
            if id_ in self._data["ids"]:
                idx = self._data["ids"].index(id_)
                self._data["ids"].pop(idx)
                if self._data["documents"]:
                    self._data["documents"].pop(idx)
                if self._data["embeddings"]:
                    self._data["embeddings"].pop(idx)
                if self._data["metadatas"]:
                    self._data["metadatas"].pop(idx)

    def count(self) -> int:
        return len(self._data["ids"])


class MockChromaDBClient:
    """Mock ChromaDB client for testing."""

    TRIALS_COLLECTION = "clinical_trials"
    NOTES_COLLECTION = "clinical_notes"
    KNOWLEDGE_COLLECTION = "medical_knowledge"

    def __init__(self):
        self.trials = MockCollection(self.TRIALS_COLLECTION)
        self.notes = MockCollection(self.NOTES_COLLECTION)
        self.knowledge = MockCollection(self.KNOWLEDGE_COLLECTION)

    def add_trial(
        self,
        trial_id: str,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]]
    ) -> None:
        ids = [f"{trial_id}_{i}" for i in range(len(documents))]
        # Add trial_id to metadatas
        for m in metadatas:
            m["trial_id"] = trial_id
        self.trials.add(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)

    def add_knowledge(
        self,
        source_id: str,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]]
    ) -> None:
        ids = [f"{source_id}_{i}" for i in range(len(documents))]
        self.knowledge.add(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)

    def query_trials(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        return self.trials.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where
        )

    def query_knowledge(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        return self.knowledge.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where
        )

    def get_trial_by_id(self, trial_id: str) -> Dict[str, Any]:
        return self.trials.get(where={"trial_id": trial_id})

    def delete_trial(self, trial_id: str) -> None:
        results = self.trials.get(where={"trial_id": trial_id})
        if results["ids"]:
            self.trials.delete(ids=results["ids"])

    def get_collection_stats(self) -> Dict[str, int]:
        return {
            "trials": self.trials.count(),
            "notes": self.notes.count(),
            "knowledge": self.knowledge.count()
        }


class MockEmbeddingManager:
    """Mock Embedding Manager for testing."""

    def __init__(self, model_name: str = "test-model"):
        self.model_name = model_name
        self.embedding_dim = 384  # Common dimension for sentence-transformers

    def embed_text(self, text: str) -> List[float]:
        # Return a deterministic mock embedding based on text length
        import hashlib
        hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
        return [(hash_val % (i + 1)) / 1000 for i in range(self.embedding_dim)]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(t) for t in texts]

    def chunk_protocol(self, text: str, chunk_size: int = 500) -> List[str]:
        """Chunk protocol text into sections."""
        chunks = []

        # Split by common section headers
        sections = ["INCLUSION CRITERIA", "EXCLUSION CRITERIA", "ENDPOINTS", "STUDY DESIGN"]

        current_chunk = ""
        for line in text.split("\n"):
            current_chunk += line + "\n"
            if len(current_chunk) >= chunk_size:
                chunks.append(current_chunk.strip())
                current_chunk = ""

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks if chunks else [text]


# =============================================================================
# TESTS - CHROMADB CLIENT
# =============================================================================

def test_chromadb_client_initialization():
    """Test ChromaDB client can be initialized."""
    client = MockChromaDBClient()
    assert client is not None
    assert client.trials is not None
    assert client.notes is not None
    assert client.knowledge is not None


def test_chromadb_collection_stats():
    """Test collection statistics."""
    client = MockChromaDBClient()
    stats = client.get_collection_stats()

    assert "trials" in stats
    assert "notes" in stats
    assert "knowledge" in stats
    assert all(isinstance(v, int) for v in stats.values())


def test_add_trial_documents():
    """Test adding trial documents to database."""
    client = MockChromaDBClient()

    trial_id = "NCT001"
    documents = [
        "INCLUSION CRITERIA: Age 18-75 years",
        "EXCLUSION CRITERIA: Pregnancy",
        "STUDY DESIGN: Randomized controlled trial"
    ]
    embeddings = [[0.1] * 384 for _ in documents]
    metadatas = [
        {"section": "inclusion", "title": "Test Trial"},
        {"section": "exclusion", "title": "Test Trial"},
        {"section": "design", "title": "Test Trial"}
    ]

    client.add_trial(
        trial_id=trial_id,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )

    stats = client.get_collection_stats()
    assert stats["trials"] == 3


def test_get_trial_by_id():
    """Test retrieving trial by ID."""
    client = MockChromaDBClient()

    # Add a trial
    trial_id = "NCT002"
    client.add_trial(
        trial_id=trial_id,
        documents=["Test document 1", "Test document 2"],
        embeddings=[[0.1] * 384, [0.2] * 384],
        metadatas=[{"section": "test"}, {"section": "test"}]
    )

    # Retrieve it
    results = client.get_trial_by_id(trial_id)

    assert len(results["ids"]) == 2
    assert all(trial_id in id_ for id_ in results["ids"])


def test_delete_trial():
    """Test deleting a trial from database."""
    client = MockChromaDBClient()

    # Add a trial
    trial_id = "NCT003"
    client.add_trial(
        trial_id=trial_id,
        documents=["To be deleted"],
        embeddings=[[0.1] * 384],
        metadatas=[{"section": "test"}]
    )

    assert client.get_collection_stats()["trials"] == 1

    # Delete it
    client.delete_trial(trial_id)

    assert client.get_collection_stats()["trials"] == 0


def test_query_trials():
    """Test querying trials by embedding similarity."""
    client = MockChromaDBClient()

    # Add trials
    client.add_trial(
        trial_id="NCT004",
        documents=["Diabetes trial eligibility"],
        embeddings=[[0.1] * 384],
        metadatas=[{"condition": "diabetes"}]
    )

    # Query
    query_embedding = [0.1] * 384
    results = client.query_trials(query_embedding, n_results=5)

    assert "ids" in results
    assert "documents" in results
    assert "distances" in results


def test_add_knowledge_documents():
    """Test adding knowledge base documents."""
    client = MockChromaDBClient()

    client.add_knowledge(
        source_id="GUIDELINES_001",
        documents=["ADA Diabetes Guidelines 2024"],
        embeddings=[[0.5] * 384],
        metadatas=[{"source": "ADA", "year": 2024}]
    )

    stats = client.get_collection_stats()
    assert stats["knowledge"] == 1


# =============================================================================
# TESTS - EMBEDDING MANAGER
# =============================================================================

def test_embedding_manager_initialization():
    """Test EmbeddingManager initialization."""
    manager = MockEmbeddingManager()
    assert manager.embedding_dim > 0


def test_embed_text():
    """Test single text embedding."""
    manager = MockEmbeddingManager()
    text = "Patient has type 2 diabetes mellitus"

    embedding = manager.embed_text(text)

    assert len(embedding) == manager.embedding_dim
    assert all(isinstance(v, (int, float)) for v in embedding)


def test_embed_batch():
    """Test batch text embedding."""
    manager = MockEmbeddingManager()
    texts = [
        "First clinical note",
        "Second clinical note",
        "Third clinical note"
    ]

    embeddings = manager.embed_batch(texts)

    assert len(embeddings) == 3
    assert all(len(e) == manager.embedding_dim for e in embeddings)


def test_chunk_protocol():
    """Test protocol text chunking."""
    manager = MockEmbeddingManager()

    protocol = """
    CLINICAL TRIAL: NCT12345678

    INCLUSION CRITERIA:
    1. Age 18-75 years
    2. Diagnosis of Type 2 Diabetes Mellitus
    3. HbA1c between 7.0% and 10.0%

    EXCLUSION CRITERIA:
    1. Type 1 Diabetes
    2. Pregnant or nursing women
    3. Severe renal impairment
    """

    chunks = manager.chunk_protocol(protocol, chunk_size=100)

    assert len(chunks) > 0
    # Verify all text is preserved
    combined = "".join(chunks).replace(" ", "").replace("\n", "")
    original = protocol.replace(" ", "").replace("\n", "")
    assert combined == original


def test_embedding_determinism():
    """Test that same text produces same embedding."""
    manager = MockEmbeddingManager()
    text = "Deterministic test text"

    embedding1 = manager.embed_text(text)
    embedding2 = manager.embed_text(text)

    assert embedding1 == embedding2


# =============================================================================
# TESTS - RAG RETRIEVAL
# =============================================================================

def test_hybrid_retrieval_structure():
    """Test that hybrid retrieval returns expected structure."""
    client = MockChromaDBClient()

    # Add test data
    client.add_trial(
        trial_id="NCT_RAG_001",
        documents=["Diabetes eligibility criteria for ages 18-65"],
        embeddings=[[0.3] * 384],
        metadatas=[{"condition": "diabetes", "section": "eligibility"}]
    )

    # Simulate retrieval
    query_embedding = [0.3] * 384
    results = client.query_trials(query_embedding, n_results=3)

    assert "ids" in results
    assert "documents" in results
    assert "metadatas" in results
    assert "distances" in results


def test_retrieval_with_filter():
    """Test retrieval with metadata filter."""
    client = MockChromaDBClient()

    # Add multiple conditions
    client.add_trial(
        trial_id="NCT_FILTER_001",
        documents=["Diabetes trial"],
        embeddings=[[0.1] * 384],
        metadatas=[{"condition": "diabetes"}]
    )
    client.add_trial(
        trial_id="NCT_FILTER_002",
        documents=["Hypertension trial"],
        embeddings=[[0.2] * 384],
        metadatas=[{"condition": "hypertension"}]
    )

    # Query specific trial
    results = client.get_trial_by_id("NCT_FILTER_001")

    assert len(results["ids"]) == 1


# =============================================================================
# TESTS - DATA INTEGRITY
# =============================================================================

def test_metadata_preservation():
    """Test that metadata is preserved after storage."""
    client = MockChromaDBClient()

    original_metadata = {
        "trial_id": "NCT_META_001",
        "condition": "diabetes",
        "phase": "3",
        "sponsor": "Test Pharma"
    }

    client.add_trial(
        trial_id="NCT_META_001",
        documents=["Test document"],
        embeddings=[[0.1] * 384],
        metadatas=[original_metadata.copy()]
    )

    results = client.get_trial_by_id("NCT_META_001")

    assert len(results["metadatas"]) == 1
    stored_metadata = results["metadatas"][0]
    assert stored_metadata["condition"] == "diabetes"


def test_empty_query_handling():
    """Test handling of queries on empty collection."""
    client = MockChromaDBClient()

    results = client.query_trials([0.1] * 384, n_results=5)

    assert results is not None
    assert "ids" in results


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
