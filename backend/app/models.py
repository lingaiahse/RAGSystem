# backend/app/models.py
from typing import List, Optional, Dict
from pydantic import BaseModel, AnyUrl, Field # ◄ Added BaseModel here
from pydantic_settings import BaseSettings, SettingsConfigDict

class ChunkMetadata(BaseModel):
    source: str
    page: Optional[int]
    section: Optional[str]
    department: Optional[str]
    location: Optional[str]
    role_level: Optional[str]

class VectorChunk(BaseModel):
    id: str
    text: str
    embedding: List[float]
    metadata: ChunkMetadata

class IngestResult(BaseModel):
    inserted: int
    failed: int = 0

class RagQuery(BaseModel):
    query: str
    top_k: int = Field(5, ge=1, le=50)

class UserContext(BaseModel):
    sub: str
    department: str
    employment_status: str
    location: str
    role_level: str