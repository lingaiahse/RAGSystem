import logging
import textwrap
from typing import List, Dict
from ..config import settings
from ..models import UserContext
from .vector_store import VectorStoreFactory
import google.generativeai as genai

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.vector_store = VectorStoreFactory.create(settings.VECTOR_PROVIDER)

    async def retrieve(self, query: str, user_ctx: UserContext, top_k: int = 5):
        # In a real system we'd compute embeddings using Gemini embeddings model
        # For determinism here we'll skip embedding similarity and use vector_store.query
        metadata_filter = {
            'department': user_ctx.department,
            'location': user_ctx.location,
            'role_level': user_ctx.role_level,
        }
        # placeholder embedding
        embedding = [0.0]
        hits = await self.vector_store.query(embedding, top_k=top_k, metadata_filter=metadata_filter)
        return hits

    async def generate_answer(self, query: str, user_ctx: UserContext, retrieved_chunks: List[Dict]):
        # Build deterministic system prompt with citation formatting requirement
        system_prompt = textwrap.dedent(f"""
        You are an enterprise HR assistant. Only answer questions based on the provided policy chunks.
        Always include deterministic citations after facts in the format: [source:{'{source}'}|page:{'{page}'}|section:{'{section}'}].
        Do not hallucinate sources. If the answer is not contained in the chunks, respond with a safe refusal.
        User context: department={user_ctx.department}, location={user_ctx.location}, role_level={user_ctx.role_level}
        """)

        # assemble retrieved text
        context_text = "\n\n".join([f"[[{c['id']}]] {c['text']} (source={c['metadata'].get('source')},page={c['metadata'].get('page')})" for c in retrieved_chunks])

        prompt = f"{system_prompt}\n\nCONTEXT:\n{context_text}\n\nQUESTION:{query}\n\nAnswer concisely and include citation tokens."

        # Call Gemini chat model (synchronously) and return text.
        resp = genai.chat.create(model='gemini-2.5-flash', messages=[{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': prompt}])
        # Response content may be in resp.candidates[0].content
        text = ''
        try:
            text = resp.last or resp.output or getattr(resp, 'candidates', [{}])[0].get('content', '')
        except Exception:
            text = str(resp)

        # If Gemini didn't return content, produce a safe fallback
        if not text:
            text = "I'm sorry — I couldn't find an answer to that within the allowed HR policy documents."

        # For streaming we will chunk the response by sentences
        chunks = [ch.strip() + ' ' for ch in text.split('. ') if ch]
        # Build citation metadata list
        citations = [c['metadata'] for c in retrieved_chunks]
        return chunks, citations
