import shutil
import uuid
import logging

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.config import UPLOAD_DIR, MAX_UPLOAD_SIZE_BYTES, MAX_UPLOAD_SIZE_MB
from app.pdf_service import extract_pages, PDFExtractionError
from app.text_cleaner import clean_pages
from app.models import (
    UploadResponse,
    QuestionRequest,
    SearchResponse,
    AskResponse,
    ReviewResponse,
)

from src.chunker import create_chunks
from src.embedding import create_embeddings
from src.vector_store import store_chunks

from app.retrieval_service import retrieve_chunks, paper_exists
from app.review_service import answer_question, generate_review

from app.retrieval_service import retrieve_chunks, paper_exists, list_papers, get_paper_chunks
from app.models import (
    UploadResponse,
    QuestionRequest,
    SearchResponse,
    AskResponse,
    ReviewResponse,
    PapersListResponse,
    PaperChunksResponse,
)

logger = logging.getLogger("papers")

router = APIRouter(
    prefix="/papers",
    tags=["Papers"]
)

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# =========================================================
# UPLOAD PAPER
# =========================================================

@router.post("/upload", response_model=UploadResponse)
def upload_paper(
    file: UploadFile = File(...)
):
    """
    Accepts a PDF, extracts + cleans + chunks + embeds its text, and
    stores the result in ChromaDB under a new paper_id.
    """

    # -----------------------------------------------------
    # 1. Validate content type
    # -----------------------------------------------------
    # UploadFile.content_type comes from the browser/client and can be
    # spoofed, but it's a cheap first filter. We double-check the file
    # extension too, and pymupdf will reject anything that isn't a real
    # PDF when we try to open it in step 4.

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported."
        )

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="File must have a .pdf extension."
        )

    # -----------------------------------------------------
    # 2. Generate unique paper ID
    # -----------------------------------------------------
    # We use this (not the user-supplied filename) as the stored file
    # name. This closes a path-traversal hole: a filename like
    # "../../etc/passwd.pdf" can never escape the upload directory or
    # overwrite another paper's file, because we never use it as a path.

    paper_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{paper_id}.pdf"

    # -----------------------------------------------------
    # 3. Save uploaded PDF, enforcing a size limit while streaming
    # -----------------------------------------------------
    # We read in chunks and check the running size, instead of loading
    # the whole file into memory, so a huge upload can't exhaust RAM
    # before we've even checked the limit.

    total_bytes = 0
    chunk_size = 1024 * 1024  # 1 MB per read

    try:
        with open(file_path, "wb") as destination:
            while True:
                data = file.file.read(chunk_size)
                if not data:
                    break

                total_bytes += len(data)

                if total_bytes > MAX_UPLOAD_SIZE_BYTES:
                    destination.close()
                    file_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            f"File too large. Maximum allowed size is "
                            f"{MAX_UPLOAD_SIZE_MB} MB."
                        )
                    )

                destination.write(data)
    except HTTPException:
        raise
    except Exception as e:
        file_path.unlink(missing_ok=True)
        logger.exception("Failed to save uploaded file")
        raise HTTPException(
            status_code=500,
            detail="Failed to save the uploaded file."
        )
    finally:
        file.file.close()

    # -----------------------------------------------------
    # 4. Extract pages
    # -----------------------------------------------------

    try:
        pages = extract_pages(str(file_path))
    except PDFExtractionError as e:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(e))

    # -----------------------------------------------------
    # 5. Clean PDF text
    # -----------------------------------------------------

    pages = clean_pages(pages)

    # -----------------------------------------------------
    # 6. Create chunks (this also detects/assigns sections)
    # -----------------------------------------------------

    chunks = create_chunks(pages)

    if not chunks:
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=400,
            detail="No usable text could be extracted from this PDF."
        )

    # -----------------------------------------------------
    # 7. Extract text from chunks
    # -----------------------------------------------------

    texts = [chunk["text"] for chunk in chunks]

    # -----------------------------------------------------
    # 8. Create embeddings
    # -----------------------------------------------------

    try:
        embeddings = create_embeddings(texts)
    except Exception:
        logger.exception("Embedding generation failed")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate embeddings for the paper."
        )

    # -----------------------------------------------------
    # 9. Store chunks in ChromaDB
    # -----------------------------------------------------

    try:
        stored_count = store_chunks(chunks, embeddings, paper_id, file.filename)
    except Exception:
        logger.exception("Failed to store chunks in ChromaDB")
        raise HTTPException(
            status_code=500,
            detail="Failed to store the processed paper."
        )

    # -----------------------------------------------------
    # 10. Return response
    # -----------------------------------------------------

    return UploadResponse(
        paper_id=paper_id,
        filename=file.filename,
        status="processed",
        pages=len(pages),
        chunks=len(chunks),
        embedding_shape=list(embeddings.shape),
        stored_in_chromadb=stored_count,
    )


# =========================================================
# SEARCH PAPER
# =========================================================

@router.post("/{paper_id}/search", response_model=SearchResponse)
def search_paper(
    paper_id: str,
    request: QuestionRequest
):
    """Raw semantic search — returns matching chunks, no LLM call."""

    if not paper_exists(paper_id):
        raise HTTPException(
            status_code=404,
            detail=f"No paper found with id '{paper_id}'."
        )

    try:
        results = retrieve_chunks(request.question, paper_id)
    except Exception:
        logger.exception("Search failed")
        raise HTTPException(status_code=500, detail="Search failed.")

    return SearchResponse(
        paper_id=paper_id,
        question=request.question,
        results=results,
    )


# =========================================================
# ASK A QUESTION
# =========================================================

@router.post("/{paper_id}/ask", response_model=AskResponse)
def ask_paper(
    paper_id: str,
    request: QuestionRequest
):
    """Semantic search + LLM answer, grounded in the paper's content."""

    if not paper_exists(paper_id):
        raise HTTPException(
            status_code=404,
            detail=f"No paper found with id '{paper_id}'."
        )

    try:
        result = answer_question(paper_id, request.question)
    except Exception:
        logger.exception("Question answering failed")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate an answer."
        )

    return AskResponse(
        paper_id=paper_id,
        question=request.question,
        answer=result["answer"],
        sources=result["sources"],
    )


# =========================================================
# AUTOMATIC REVIEW
# =========================================================

@router.post("/{paper_id}/review", response_model=ReviewResponse)
def review_paper(
    paper_id: str
):
    if not paper_exists(paper_id):
        raise HTTPException(
            status_code=404,
            detail=f"No paper found with id '{paper_id}'."
        )

    try:
        result = generate_review(paper_id)
    except Exception:
        logger.exception("Review generation failed")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate the review."
        )

    return ReviewResponse(
        paper_id=paper_id,
        review=result["review"],
        sources=result["sources"],
    )

# =========================================================
# सगळे uploaded papers ची यादी
# =========================================================

@router.get("", response_model=PapersListResponse)
def get_all_papers():
    """किती papers upload झालेत आणि त्यांची नावं दाखवतं."""

    papers = list_papers()

    return PapersListResponse(
        papers=papers,
        total=len(papers)
    )


# =========================================================
# एका paper चे सगळे chunks
# =========================================================

@router.get("/{paper_id}/chunks", response_model=PaperChunksResponse)
def get_chunks(paper_id: str):
    """
    दिलेल्या paper चे सगळे chunks दाखवतं — यूजर हे बघून
    verify करू शकतो की माहिती बरोबर आहे का.
    """

    if not paper_exists(paper_id):
        raise HTTPException(
            status_code=404,
            detail=f"No paper found with id '{paper_id}'."
        )

    chunks = get_paper_chunks(paper_id)

    filename = chunks[0]["metadata"].get("filename", "unknown.pdf") if chunks else "unknown.pdf"

    return PaperChunksResponse(
        paper_id=paper_id,
        filename=filename,
        total_chunks=len(chunks),
        chunks=chunks
    )