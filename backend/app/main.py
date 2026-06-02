import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routers import stream as stream_router
from .logging_config import configure_logging
from .config import settings

configure_logging()

app = FastAPI(title='Enterprise HR Policy RAG')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stream_router.router)


if __name__ == '__main__':
    uvicorn.run('app.main:app', host=settings.APP_HOST, port=settings.APP_PORT, reload=True)
