from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from typing import AsyncGenerator
import json
import asyncio
from ...auth import verify_jwt_token
from ...models import RagQuery, UserContext
from ...services.rag_service import RAGService

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
