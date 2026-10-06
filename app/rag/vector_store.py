import numpy as np
import re
from typing import List, Dict, Any, Tuple
from app.rag.documents import KB_DOCUMENTS
from app.models.schemas import RAGSource
from app.config import settings

class HybridVectorStore:
    """Hybrid semantic vector store with FAISS + sentence-transformers and lexical fallback."""

    def __init__(self):
        self.documents = KB_DOCUMENTS
        self.embedding_model = None
        self.faiss_index = None
        self.embeddings = None
        self._initialized = False

    def initialize(self):
        """Build vector embeddings and FAISS index."""
        if self._initialized:
            return

        texts = [f"{doc['title']} {doc['category']} {doc['content']}" for doc in self.documents]

        try:
            from sentence_transformers import SentenceTransformer
            import faiss

            self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
            raw_embeddings = self.embedding_model.encode(texts, convert_to_numpy=True)

            # L2 normalize for cosine similarity via inner product
            faiss.normalize_L2(raw_embeddings)
            self.embeddings = raw_embeddings

            dimension = raw_embeddings.shape[1]
            self.faiss_index = faiss.IndexFlatIP(dimension)
            self.faiss_index.add(raw_embeddings)
            self._initialized = True
        except Exception as e:
            # Fallback to lexical/TF-IDF based vectorization if model loading encounters issue
            print(f"[RAG Store] SentenceTransformers/FAISS init fallback: {e}")
            self._init_lexical_fallback(texts)
            self._initialized = True

    def _init_lexical_fallback(self, texts: List[str]):
        """Simple TF-IDF cosine similarity fallback."""
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.tfidf = TfidfVectorizer(stop_words="english")
        self.tfidf_matrix = self.tfidf.fit_transform(texts)

    def _calculate_lexical_score(self, query: str, doc: Dict[str, Any]) -> float:
        """Calculate word overlap and keyword matching score."""
        q_tokens = set(re.findall(r"\w+", query.lower()))
        if not q_tokens:
            return 0.0

        # Match against keywords
        keyword_hits = 0
        for kw in doc.get("keywords", []):
            kw_tokens = set(re.findall(r"\w+", kw.lower()))
            if kw_tokens.issubset(q_tokens) or any(t in q_tokens for t in kw_tokens):
                keyword_hits += 1

        # Match against document tokens
        doc_tokens = set(re.findall(r"\w+", f"{doc['title']} {doc['content']}".lower()))
        token_overlap = len(q_tokens.intersection(doc_tokens)) / max(len(q_tokens), 1)

        lexical_score = (token_overlap * 0.6) + (min(keyword_hits, 3) * 0.15)
        return min(lexical_score, 1.0)

    def search(self, query: str, top_k: int = 3, threshold: float = 0.45) -> List[RAGSource]:
        """Perform hybrid semantic + lexical search."""
        if not self._initialized:
            self.initialize()

        scored_results: List[Tuple[float, Dict[str, Any]]] = []

        if self.faiss_index is not None and self.embedding_model is not None:
            import faiss
            q_emb = self.embedding_model.encode([query], convert_to_numpy=True)
            faiss.normalize_L2(q_emb)
            scores, indices = self.faiss_index.search(q_emb, k=min(top_k * 2, len(self.documents)))

            for score, idx in zip(scores[0], indices[0]):
                if idx < 0 or idx >= len(self.documents):
                    continue
                doc = self.documents[idx]
                lexical = self._calculate_lexical_score(query, doc)
                # Hybrid fusion: 70% semantic, 30% lexical
                hybrid_score = (float(score) * 0.70) + (lexical * 0.30)
                scored_results.append((hybrid_score, doc))
        elif hasattr(self, "tfidf"):
            from sklearn.metrics.pairwise import cosine_similarity
            q_vec = self.tfidf.transform([query])
            sims = cosine_similarity(q_vec, self.tfidf_matrix)[0]
            for idx, score in enumerate(sims):
                doc = self.documents[idx]
                lexical = self._calculate_lexical_score(query, doc)
                hybrid_score = (float(score) * 0.70) + (lexical * 0.30)
                scored_results.append((hybrid_score, doc))
        else:
            for doc in self.documents:
                score = self._calculate_lexical_score(query, doc)
                scored_results.append((score, doc))

        # Sort descending by score
        scored_results.sort(key=lambda x: x[0], reverse=True)

        results: List[RAGSource] = []
        for score, doc in scored_results[:top_k]:
            if score >= threshold:
                results.append(RAGSource(
                    doc_id=doc["doc_id"],
                    title=doc["title"],
                    category=doc["category"],
                    snippet=doc["content"],
                    score=round(score, 4)
                ))

        return results

vector_store = HybridVectorStore()
