from fastapi import APIRouter, Depends, Request, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse, JSONResponse
from typing import AsyncGenerator
import json
import asyncio
from ...auth import verify_jwt_token
from ...models import RagQuery, UserContext
from ...services.rag_service import RAGService
from ...ingest import chunk_text, extract_pdf_text, compute_embedding
import tempfile
import os

router = APIRouter(prefix='/api/rag')
service = RAGService()


@router.post('/stream')
async def stream_answer(request: Request, payload: RagQuery, user=Depends(verify_jwt_token)):
    # Build UserContext
    user_ctx = UserContext(sub=user['sub'], department=user.get('department') or '', employment_status=user.get('employment_status') or '', location=user.get('location') or '', role_level=user.get('role_level') or '')

    retrieved = await service.retrieve(payload.query, user_ctx, top_k=payload.top_k)

    # If nothing retrieved, return a short refusal as SSE
    if not retrieved:
        async def empty_gen():
            yield f"event: citation\ndata: {json.dumps([])}\n\n"
            yield f"event: message\ndata: {json.dumps({'text':'No accessible policy documents found for your context.'})}\n\n"
        return StreamingResponse(empty_gen(), media_type='text/event-stream')

    chunks, citations = await service.generate_answer(payload.query, user_ctx, retrieved)

    async def event_generator() -> AsyncGenerator[str, None]:
        # first send citation metadata
        yield f"event: citation\ndata: {json.dumps(citations)}\n\n"
        # then stream message chunks
        for chunk in chunks:
            # small delay to allow client rendering progressively
            await asyncio.sleep(0.05)
            yield f"event: message\ndata: {json.dumps({'text': chunk})}\n\n"
        yield f"event: done\ndata: {{}}\n\n"

    return StreamingResponse(event_generator(), media_type='text/event-stream')



@router.post('/ingest')
async def ingest_file(request: Request, file: UploadFile = File(...), source: str = Form(...), department: str = Form(None), location: str = Form(None), role_level: str = Form(None), user=Depends(verify_jwt_token)):
    """Upload a PDF and ingest into the running process vector store (development/testing).

    Important: this endpoint writes embeddings into the RAGService.vector_store used by
    the running FastAPI process, so it will be available for subsequent `/stream` queries.
    """
    # write uploaded file to a temp path
    suffix = os.path.splitext(file.filename)[1] or '.pdf'
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        text = extract_pdf_text(tmp_path)
        text_chunks = chunk_text(text)
        to_upsert = []
        for i, chunk in enumerate(text_chunks):
            try:
                emb = compute_embedding(chunk)
            except Exception:
                emb = [0.0]
            metadata = {
                'source': source,
                'page': None,
                'section': None,
                'department': department,
                'location': location,
                'role_level': role_level,
            }
            to_upsert.append({'id': f'ingest-{i}-{os.path.basename(tmp_path)}', 'text': chunk, 'embedding': emb, 'metadata': metadata})

        # upsert into the running service's vector store
        result = await service.vector_store.upsert(to_upsert)
        return {'inserted': result.get('upserted', len(to_upsert))}
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass
