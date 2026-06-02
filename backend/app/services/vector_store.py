from typing import List, Dict, Optional
import uuid
import logging

logger = logging.getLogger(__name__)


class InMemoryVectorStore:
    def __init__(self):
        self._items = []  # each item: {'id', 'embedding', 'text', 'metadata'}

    async def upsert(self, items: List[Dict]):
        for it in items:
            self._items.append(it)
        return {'upserted': len(items)}

    async def query(self, embedding: List[float], top_k: int = 5, metadata_filter: Optional[Dict] = None):
        # naive cosine-ish via dot product; we'll not compute exact similarity for brevity
        results = []
        for it in self._items:
            if metadata_filter:
                skip = False
                for k, v in metadata_filter.items():
                    if v is None:
                        continue
                    if it['metadata'].get(k) != v:
                        skip = True
                        break
                if skip:
                    continue
            # simple length-based score placeholder
            score = len(set(it['text'].split()))
            results.append({'id': it['id'], 'text': it['text'], 'metadata': it['metadata'], 'score': score})
        results = sorted(results, key=lambda r: r['score'], reverse=True)
        return results[:top_k]


class VectorStoreFactory:
    @staticmethod
    def create(provider: str):
        if provider == 'in_memory':
            return InMemoryVectorStore()
        # Extend here for pgvector or Pinecone
        raise ValueError('Unsupported vector provider')
