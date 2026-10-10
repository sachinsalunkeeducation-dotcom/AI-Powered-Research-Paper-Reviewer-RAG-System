from typing import Any
from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    paper_id: str
    filename: str
    status: str
    pages: int
    chunks: int
    embedding_shape: list[int]
    stored_in_chromadb: int


class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)


class SearchResult(BaseModel):
    text: str
    metadata: dict[str, Any]
    distance: float


class SearchResponse(BaseModel):
    paper_id: str
    question: str
    results: list[SearchResult]


class AskResponse(BaseModel):
    paper_id: str
    question: str
    answer: str
    sources: list[dict[str, Any]]


class ReviewResponse(BaseModel):
    paper_id: str
    review: dict[str, Any]
    sources: list[dict[str, Any]]


class PaperSummary(BaseModel):
    paper_id: str
    filename: str
    chunk_count: int


class PapersListResponse(BaseModel):
    papers: list[PaperSummary]
    total: int


class ChunkItem(BaseModel):
    text: str
    metadata: dict[str, Any]


class PaperChunksResponse(BaseModel):
    paper_id: str
    filename: str
    total_chunks: int
    chunks: list[ChunkItem]