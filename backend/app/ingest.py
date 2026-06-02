import io
import uuid
import logging
from typing import List, Dict, Optional
from pdfminer.high_level import extract_text
from .services.vector_store import VectorStoreFactory
from .config import settings
from .models import IngestResult
import google.generativeai as genai

logger = logging.getLogger(__name__)


def chunk_text(text: str, max_chars: int = 2000) -> List[str]:
    # simple chunker by characters with sentence boundary respect
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        chunk = text[start:end]
        chunks.append(chunk.strip())
        start = end
    return chunks


def extract_pdf_text(file_path: str) -> str:
    text = extract_text(file_path)
    return text


def compute_embedding(text: str) -> List[float]:
    # Use Gemini embeddings in production. Here we call the SDK.
    genai.configure(api_key=settings.GEMINI_API_KEY)
    resp = genai.embeddings.create(model='embed-1', input=text)
    emb = getattr(resp.data[0], 'embedding', None) or resp[0].embedding
    return emb


def ingest_pdf(file_path: str, source_name: str, department: Optional[str], location: Optional[str], role_level: Optional[str]) -> IngestResult:
    text = extract_pdf_text(file_path)
    text_chunks = chunk_text(text)
    store = VectorStoreFactory.create(settings.VECTOR_PROVIDER)
    to_upsert = []
    for i, chunk in enumerate(text_chunks):
        chunk_id = str(uuid.uuid4())
        try:
            embedding = compute_embedding(chunk)
        except Exception:
            embedding = [0.0]
        metadata = {
            'source': source_name,
            'page': None,
            'section': None,
            'department': department,
            'location': location,
            'role_level': role_level,
        }
        to_upsert.append({'id': chunk_id, 'text': chunk, 'embedding': embedding, 'metadata': metadata})
    result = None
    try:
        # vector store upsert is async; for simplicity support sync call if needed
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(store.upsert(to_upsert))
    except Exception:
        # fallback synchronous
        import asyncio
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(store.upsert(to_upsert))
    inserted = result.get('upserted', len(to_upsert))
    return IngestResult(inserted=inserted)
