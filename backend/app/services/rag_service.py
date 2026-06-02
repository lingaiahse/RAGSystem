# backend/app/services/rag_service.py
import logging
import textwrap
from typing import List, Dict, Tuple
from google import genai
from google.genai import types

from ..config import settings
from ..models import UserContext
from .vector_store import VectorStoreFactory

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(self):
        # Natively instantiate the Google GenAI client object
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.vector_store = VectorStoreFactory.create(settings.VECTOR_PROVIDER)

    async def retrieve(self, query: str, user_ctx: UserContext, top_k: int = 5) -> List[Dict]:
        """
        Retrieves matching HR document chunks using strict RBAC metadata filters.
        """
        metadata_filter = {
            'department': user_ctx.department,
            'location': user_ctx.location,
            'role_level': user_ctx.role_level,
        }
        
        # Placeholder embedding logic matched to your provider payload layout
        # (In production, replace with: self.client.models.embed_content)
        embedding = [0.0]
        hits = await self.vector_store.query(embedding, top_k=top_k, metadata_filter=metadata_filter)
        return hits

    async def generate_answer(self, query: str, user_ctx: UserContext, retrieved_chunks: List[Dict]) -> Tuple[List[str], List[Dict]]:
        """
        Assembles context and streams production-safe responses with strict structural citations.
        """
        # Build strict system rules for safe HR reasoning
        system_prompt = textwrap.dedent(f"""
        You are an enterprise HR assistant. Only answer questions based on the provided policy chunks.
        Always include deterministic citations after facts in the format: .
        Do not hallucinate sources. If the answer is not contained in the chunks, respond with a safe refusal.
        User context: department={user_ctx.department}, location={user_ctx.location}, role_level={user_ctx.role_level}
        """)

        # Assemble retrieved content data blocks securely
        context_text = "\n\n".join([
            f"[[{c['id']}]] {c['text']} (source={c['metadata'].get('source')}, page={c['metadata'].get('page')}, section={c['metadata'].get('section')})" 
            for c in retrieved_chunks
        ])

        user_prompt = f"CONTEXT:\n{context_text}\n\nQUESTION: {query}\n\nAnswer concisely and include citation tokens."

        # Modern unified model call using the canonical generation syntax
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.2, # Low temperature ensures focused, analytical responses
                )
            )
            text = response.text
        except Exception as e:
            logger.error(f"Gemini API failure: {str(e)}")
            text = "I'm sorry — an internal error occurred while processing your query. Please contact HR support."

        # Safe fallback logic if generation engine returns an empty text block
        if not text or text.strip() == "":
            text = "I'm sorry — I couldn't find an answer to that within the allowed HR policy documents."

        # Package the full response text into discrete stream segments (split by sentences)
        chunks = [ch.strip() + '. ' for ch in text.split('. ') if ch]
        
        # Extract metadata structures safely to return to the UI for citation chips
        citations = [c['metadata'] for c in retrieved_chunks]
        
        return chunks, citations