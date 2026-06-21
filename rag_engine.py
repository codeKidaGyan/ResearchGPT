import hashlib
from pathlib import Path

import chromadb
from chromadb.config import Settings

from groq_client import GroqClient


class ResearchAssistant:
    def __init__(self):
        self.groq = GroqClient()
        chroma_dir = Path(__file__).resolve().parent / "chroma_store"
        chroma_dir.mkdir(exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(chroma_dir), settings=Settings(anonymized_telemetry=False))
        self.collection = self.client.get_or_create_collection(name="research_documents")

    def _chunk_text(self, text: str, chunk_size: int = 1800, overlap: int = 250):
        cleaned = " ".join(text.split())
        chunks = []
        start = 0
        while start < len(cleaned):
            end = min(len(cleaned), start + chunk_size)
            chunks.append(cleaned[start:end])
            if end == len(cleaned):
                break
            start = max(0, end - overlap)
        return chunks

    def index_document(self, document_id: str, text: str, metadata: dict | None = None):
        metadata = metadata or {}
        chunks = self._chunk_text(text)
        ids = []
        metadatas = []
        documents = []
        for idx, chunk in enumerate(chunks):
            chunk_id = hashlib.md5(f"{document_id}-{idx}".encode()).hexdigest()
            ids.append(chunk_id)
            md = {k: str(v) for k, v in metadata.items()}
            md.update({"document_id": str(document_id), "chunk_index": str(idx)})
            metadatas.append(md)
            documents.append(chunk)
        existing = self.collection.get(where={"document_id": str(document_id)})
        existing_ids = existing.get("ids", []) if existing else []
        if existing_ids:
            self.collection.delete(ids=existing_ids)
        self.collection.add(ids=ids, documents=documents, metadatas=metadatas)

    def _retrieve_context(self, document_id: str, document_text: str, question: str, top_k: int = 4) -> str:
        existing = self.collection.get(where={"document_id": str(document_id)})
        if not existing or not existing.get("ids"):
            self.index_document(document_id, document_text)
        results = self.collection.query(query_texts=[question], n_results=top_k, where={"document_id": str(document_id)})
        docs = results.get("documents", [[]])[0]
        if not docs:
            docs = self._chunk_text(document_text)[:top_k]
        return "\n\n".join(docs)

    def summarize_document(self, text: str, style: str = "Concise") -> str:
        style_prompt = {
            "Concise": "Give a concise academic summary with objective, methods, findings, and conclusion.",
            "Detailed": "Give a detailed academic summary with background, objective, methods, results, limitations, and conclusion.",
            "Bullet Points": "Summarize in clear bullet points covering problem, methods, results, limitations, and future work.",
            "Methodology Focus": "Focus the summary on methodology, datasets, experiments, evaluation, and technical contribution.",
        }.get(style, "Summarize the research paper clearly.")
        prompt = f"{style_prompt}\n\nPaper content:\n{text[:18000]}"
        return self.groq.chat_completion(
            system_prompt="You are an expert scientific research assistant. Produce accurate, structured, readable academic output.",
            user_prompt=prompt,
            temperature=0.2,
            max_tokens=1400,
        )

    def answer_question(self, document_id: str, document_text: str, question: str) -> str:
        context = self._retrieve_context(document_id, document_text, question)
        prompt = f"Use the paper context below to answer the question accurately. If the answer is not in the paper, clearly say that.\n\nContext:\n{context}\n\nQuestion: {question}"
        return self.groq.chat_completion(
            system_prompt="You answer questions about research papers using only the supplied context when possible.",
            user_prompt=prompt,
            temperature=0.2,
            max_tokens=1000,
        )

    def detect_research_gaps(self, text: str) -> str:
        prompt = (
            "Analyze this research paper and identify research gaps. "
            "Return sections for: limitations, underexplored areas, methodological gaps, dataset/data gaps, practical deployment gaps, and future research opportunities.\n\n"
            f"Paper content:\n{text[:18000]}"
        )
        return self.groq.chat_completion(
            system_prompt="You are a senior research analyst specializing in literature review and gap detection.",
            user_prompt=prompt,
            temperature=0.3,
            max_tokens=1400,
        )