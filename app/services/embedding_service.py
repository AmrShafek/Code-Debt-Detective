"""
Embedding Service
Manages text embeddings for semantic search and code similarity
"""

import os
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import numpy as np


class EmbeddingService:
    """Manages text embeddings for code search and similarity matching"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        self._initialized = False

    async def initialize(self):
        """Initialize the embedding model"""
        if self._initialized:
            return
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
            self._initialized = True
        except ImportError:
            self._initialized = False

    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        if not self._initialized:
            await self.initialize()
        if self._model:
            return self._model.encode(text).tolist()
        return []

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        if not self._initialized:
            await self.initialize()
        if self._model:
            return self._model.encode(texts).tolist()
        return []

    async def compute_similarity(self, text1: str, text2: str) -> float:
        """Compute cosine similarity between two texts"""
        emb1 = await self.embed_text(text1)
        emb2 = await self.embed_text(text2)
        if emb1 and emb2:
            v1, v2 = np.array(emb1), np.array(emb2)
            return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
        return 0.0

    async def find_similar_code(self, query: str, code_chunks: List[Dict[str, str]], top_k: int = 5) -> List[Dict[str, Any]]:
        """Find code chunks similar to the query"""
        query_emb = await self.embed_text(query)
        if not query_emb:
            return []

        chunk_texts = [c.get("text", "") for c in code_chunks]
        chunk_embs = await self.embed_texts(chunk_texts)

        if not chunk_embs:
            return []

        query_vec = np.array(query_emb)
        scores = []
        for i, emb in enumerate(chunk_embs):
            chunk_vec = np.array(emb)
            sim = float(np.dot(query_vec, chunk_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(chunk_vec)))
            scores.append((i, sim))

        scores.sort(key=lambda x: x[1], reverse=True)
        results = []
        for i, sim in scores[:top_k]:
            results.append({
                **code_chunks[i],
                "similarity": round(sim, 4),
                "rank": len(results) + 1
            })

        return results

    def is_available(self) -> bool:
        return self._initialized
