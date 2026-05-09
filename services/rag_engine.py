import os
import json
import numpy as np
# pyrefly: ignore [missing-import]
from sentence_transformers import SentenceTransformer
# pyrefly: ignore [missing-import]
import faiss

class RAGEngine:
    """
    Hybrid Retrieval-Augmented Generation (RAG) Engine using FAISS.
    Embeds authoritative text chunks (ICAR, FAO, APEDA) and retrieves them using Semantic Search.
    """
    def __init__(self):
        print("[RAGEngine] Initializing SentenceTransformer (all-MiniLM-L6-v2)...")
        # Lightweight dense retrieval model
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.index = None
        self.documents = []
        self._initialize_knowledge_base()

    def _initialize_knowledge_base(self):
        """Seed the vector database with verified Data Vectors."""
        # Hardcoded knowledge base as provided for the weekend demo
        raw_data = [
            {
                "crop": "Maize",
                "intercrop": "Cowpea / Beans",
                "reason": "Fixes Nitrogen; reduces fertilizer cost by 30%.",
                "export": "High demand in Vietnam/Japan.",
                "source": "FAO Regenerative Manuals / APEDA"
            },
            {
                "crop": "Rice",
                "intercrop": "Azolla (Water Fern)",
                "reason": "Natural bio-fertilizer; improves soil structure.",
                "export": "Basmati varieties peak in Middle East.",
                "source": "ICAR Kharif Advisory 2025 / APEDA"
            },
            {
                "crop": "Turmeric",
                "intercrop": "Chilli",
                "reason": "Maximizes land usage; Chilli acts as a pest trap.",
                "export": "EU demand for organic curcumin.",
                "source": "ICAR Rabi Advisory 2025 / APEDA"
            },
            {
                "crop": "Millets",
                "intercrop": "Pigeon Pea",
                "reason": "Drought resistant; improves soil organic carbon.",
                "export": "Declared 'Global Superfood' for 2025-26.",
                "source": "FAO Regenerative Manuals / NITI Aayog"
            }
        ]

        # Step 1: Chunking
        for item in raw_data:
            chunk = (f"Crop: {item['crop']}. "
                     f"Regenerative Intercropping Pair: {item['intercrop']}. "
                     f"Agronomic Reason: {item['reason']} "
                     f"Export Intelligence: {item['export']} "
                     f"Source Data: {item['source']}")
            self.documents.append({
                "crop": item["crop"].lower(),
                "chunk": chunk,
                "source": item["source"],
                "intercrop": item["intercrop"],
                "reason": item["reason"],
                "export": item["export"]
            })

        # Step 1 (cont): Embedding
        texts = [doc["chunk"] for doc in self.documents]
        print(f"[RAGEngine] Embedding {len(texts)} data vectors...")
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        
        # Build FAISS index (Dense Semantic Search)
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings)
        print("[RAGEngine] FAISS Vector Database initialized successfully.")

    def retrieve(self, predicted_crop: str, weather_context: str = "") -> dict:
        """
        Step 2: Context Injection and Retrieval.
        Queries the FAISS index for the specific crop context.
        """
        # Construct the semantic query
        query = f"Best regenerative intercropping and export strategy for {predicted_crop} given weather {weather_context}."
        
        # Embed the query
        query_embedding = self.model.encode([query], convert_to_numpy=True)
        
        # Search the FAISS index for the top 1 most relevant chunk
        distances, indices = self.index.search(query_embedding, k=1)
        best_idx = indices[0][0]
        
        # Check if we have an exact exact keyword match (simulating BM25 filter)
        for doc in self.documents:
            if doc["crop"] == predicted_crop.lower():
                return doc
                
        # If no exact match, rely on semantic distance
        if best_idx != -1 and distances[0][0] < 1.5:
            return self.documents[best_idx]

        # Fallback for crops not in the weekend demo dataset
        return {
            "chunk": f"Regenerative practices for {predicted_crop} involve crop rotation and organic mulching. Ensure standard ICAR sowing windows are followed.",
            "source": "ICAR General Advisory / Local Mandi",
            "intercrop": "Legume Rotation",
            "reason": "Enhances soil biodiversity and disrupts pest cycles naturally.",
            "export": "Stable domestic demand; monitor local Agmarknet pricing for export parity."
        }

# Singleton instance
rag_engine = RAGEngine()
