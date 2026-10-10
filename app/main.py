import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import ALLOWED_ORIGINS
from app.papers import router as papers_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger("main")

app = FastAPI(
    title="Automatic Research Paper Reviewer",
    description="AI-powered research paper analysis system",
    version="1.0.0"
)


# Allow only the configured frontend origin(s) to call this API.
# Set ALLOWED_ORIGINS in your .env file, e.g.:
#   ALLOWED_ORIGINS=https://myclientapp.com,http://localhost:5173
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(papers_router)


# ---------------------------------------------------------------------
# Global safety net: catches anything that slips past route-level
# try/except blocks so the client always gets clean JSON, never a raw
# Python traceback.
# ---------------------------------------------------------------------
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred."},
    )


@app.get("/health")
def health_check():
    return {"status": "healthy"}
