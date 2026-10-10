AI-Based Research Paper Reviewer
An AI-powered application that helps users understand and review
research papers. Users can upload a PDF, ask questions about its
content, search relevant paper chunks, and generate a structured review
using Retrieval-Augmented Generation (RAG).
> **Note:** AI-generated-text detection is a planned feature. It is not
> implemented in the current version unless you have separately added
> the detector module and endpoint.
Features
Currently implemented
Upload a research paper in PDF format.
Extract and clean text from the uploaded PDF.
Split extracted text into smaller chunks.
Detect paper sections where possible.
Generate embeddings for the chunks.
Store chunk text, embeddings, and metadata in ChromaDB.
Search for relevant chunks using a user's question.
Ask questions about an uploaded paper using RAG.
Generate a structured research-paper review.
Return source metadata such as page number and section when
available.
Planned improvements
AI-generated-text likelihood analysis at paper and section level.
More reliable section detection and retrieval.
Improved source citations in answers and reviews.
Reranking and hybrid retrieval.
Better paper management, including listing and deleting uploaded
papers.
Automated evaluation for retrieval quality and answer faithfulness.
Technology Stack
Component              Technology
---
Programming language   Python
Backend API            FastAPI
ASGI server            Uvicorn
PDF processing         Project PDF extraction service
Text cleaning          Custom Python processing
Chunking               Custom chunking module
Embeddings             Sentence Transformers / Hugging Face embedding model
Vector database        ChromaDB
Large language model   Groq API --- `openai/gpt-oss-20b`
Frontend               HTML, CSS, JavaScript
API format             REST / JSON
How It Works
``` text
                 Research Paper PDF
                         |
                         v
                   PDF Extraction
                         |
                         v
                    Text Cleaning
                         |
                         v
                   Section Detection
                         |
                         v
                       Chunking
                         |
                         v
                    Text Embeddings
                         |
                         v
                     ChromaDB
                         |
             User asks a question
                         |
                         v
                 Retrieve relevant chunks
                         |
                         v
               Build context for the LLM
                         |
                         v
                  Groq LLM generation
                         |
                         v
                 Answer / Paper Review
```
The application uses Retrieval-Augmented Generation (RAG). Instead of
sending the entire PDF directly to the language model for every
question, the system retrieves relevant chunks from the vector database
and uses them as context for the response.
Project Structure
The exact structure may differ slightly based on your local files. A
typical layout for this project is:
``` text
research-paper-reviewer/
├── app/
│   ├── main.py
│   ├── pdf_service.py
│   ├── text_cleaner.py
│   ├── retrieval_service.py
│   └── review_service.py
├── src/
│   ├── chunker.py
│   ├── embedding.py
│   ├── vector_store.py
│   └── llm.py
├── frontend/
│   └── index.html
├── data/
│   └── uploads/
├── chroma_db/
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```
`chroma_db/`, uploaded PDFs, virtual environments, and secret files
should generally not be committed to GitHub.
API Endpoints
The following endpoints are part of the current workflow. Exact request
parameters may depend on your implementation.
---
Method                  Endpoint                                   Purpose
---
`POST`                  `/papers/upload`                           Upload and process a
PDF
`POST`                  `/papers/{paper_id}/search?question=...`   Retrieve relevant
chunks
`POST`                  `/papers/{paper_id}/ask?question=...`      Ask a question about
the paper
`POST`                  `/papers/{paper_id}/review`                Generate a structured
paper review
1. Upload a paper
`POST /papers/upload`
Upload a PDF using multipart form data with the field name `file`. The
API processes the paper, creates chunks and embeddings, stores them in
ChromaDB, and returns a `paper_id`.
Example response:
``` json
{
  "paper_id": "your-paper-id",
  "filename": "research-paper.pdf",
  "status": "processed",
  "pages": 10,
  "chunks": 40,
  "embedding_shape": [40, 384],
  "stored_in_chromadb": 40
}
```
The values above are illustrative; actual values depend on the uploaded
PDF and embedding model.
2. Search paper content
`POST /papers/{paper_id}/search?question=What is the methodology?`
Retrieves relevant chunks and their metadata from the vector database.
3. Ask a question
`POST /papers/{paper_id}/ask?question=What are the main findings?`
The backend retrieves relevant chunks, adds them to the prompt as
context, and asks the language model to answer based on that context.
4. Generate a review
`POST /papers/{paper_id}/review`
Generates a structured review. Depending on the paper content retrieved,
the review may cover: - Summary - Methodology - Results and findings -
Strengths - Weaknesses and limitations - Originality - Writing quality -
References - Structure - Overall assessment
The review is an AI-generated aid, not a substitute for expert peer
review. Its claims should be checked against the original paper.
Setup and Installation
Requirements
Python 3.10 or a compatible Python version supported by the
dependencies.
Git.
A Groq API key.
Internet access for calling the Groq API and downloading any model
assets required by the embedding library.
1. Clone the repository
``` bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd research-paper-reviewer
```
Replace `<YOUR_GITHUB_REPOSITORY_URL>` with your repository URL.
2. Create a virtual environment
Windows PowerShell:
``` powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
If PowerShell blocks activation, you can run the virtual environment's
Python directly or follow the activation policy appropriate for your
machine.
3. Install dependencies
``` bash
pip install -r requirements.txt
```
If `requirements.txt` is missing dependencies, install the packages
actually used by your code. Common packages for this stack may include:
``` bash
pip install fastapi uvicorn python-multipart chromadb groq sentence-transformers pymupdf python-dotenv
```
Do not install packages blindly if your project uses different libraries
or versions.
4. Configure the API key
Create a `.env` file in the project root:
``` env
GROQ_API_KEY=your_groq_api_key_here
```
Read the key from the environment in your LLM service. For example:
``` python
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY is not set")

client = Groq(api_key=api_key)
```
Keep `.env` out of Git. Never commit an API key to GitHub. If a real
key has already been pushed to a public repository, revoke or rotate it
in the provider dashboard and remove it from the code and repository
history as appropriate. Deleting the key from the latest file alone does
not invalidate a key that was exposed.
5. Run the backend
Use the module path that matches your actual FastAPI application. For
example, if the FastAPI instance is `app` inside `app/main.py`:
``` bash
uvicorn app.main:app --reload
```
The API will usually be available at:
``` text
http://127.0.0.1:8000
```
Open the interactive API documentation at:
``` text
http://127.0.0.1:8000/docs
```
If your `main.py` is at the project root instead, the command may be
`uvicorn main:app --reload`. The module path must match the file
containing the FastAPI instance.
6. Open the frontend
Open `frontend/index.html` in a browser, or serve the frontend with a
local static-file server. Confirm that the frontend's API base URL
matches the backend, for example:
``` javascript
const API_BASE = "http://localhost:8000/papers";
```
For local development, the frontend and backend must be configured to
communicate correctly, including CORS settings if they run on different
origins.
Configuration and Data
Paper ID: Each uploaded paper receives an ID used by the search,
ask, and review endpoints.
Chunk metadata: Chunks can include the paper ID, chunk ID, page
number, detected section, and source.
Vector persistence: ChromaDB stores vectors on disk using the
configured persistence path.
Model configuration: The LLM model name and generation settings
are configured in the LLM service.
API secrets: Store credentials in environment variables or a
local `.env` file that is excluded from version control.
Do not assume that a paper ID is an authentication mechanism. If the
application is deployed for multiple users, add authentication and
authorization so users can only access papers they are allowed to view.
Planned Feature: AI-Generated Text Detection
The planned detector will estimate whether selected paper passages have
characteristics associated with AI-generated text. It should be treated
as an experimental signal, not proof of authorship.
Potential design:
``` text
Extracted paper text
        |
        v
Split into suitable passages
        |
        v
Analyze each passage
        |
        v
Calibrated detection model / features
        |
        v
Passage-level scores and explanations
        |
        v
Cautious document-level summary
```
Possible implementation options include evaluating a purpose-built
detector on representative academic writing, or training a classifier
using suitable human-written and AI-generated text datasets. Perplexity,
sentence variation, and vocabulary statistics can be explored as
features, but they are not reliable proof by themselves.
A future API could look like:
`POST /papers/{paper_id}/ai-detection`
A future response might include passage-level scores, the detector
version, and a warning about uncertainty. Example only:
``` json
{
  "paper_id": "your-paper-id",
  "status": "experimental",
  "passages_analyzed": 12,
  "message": "Scores indicate text patterns, not verified authorship."
}
```
Avoid presenting a percentage as a calibrated probability unless the
model has been properly evaluated and calibrated. Do not label a paper
as definitely AI-written based only on this result. False positives can
occur, including for non-native English writing, formulaic academic
language, edited text, and short passages. Human-written text may also
be incorrectly flagged, and AI-generated text may evade detection.
Limitations
Retrieval quality depends on PDF extraction, chunk boundaries,
embeddings, and search configuration.
Section detection may be imperfect for papers with unusual layouts
or formatting.
The LLM may produce inaccurate statements even when context is
supplied; verify important claims against the paper.
The quality of a generated review depends on whether the retrieved
chunks cover the relevant sections.
AI-generated-text detection is not currently part of the implemented
workflow unless added separately, and no detector can reliably prove
authorship from text alone.
The current local setup is intended for development, not necessarily
production deployment.
Future Improvements
Improve section detection and chunking.
Add citations linked to the exact retrieved passages and page
numbers.
Add reranking or hybrid retrieval (semantic search plus BM25).
Evaluate answer faithfulness and retrieval quality with a test set.
Improve review generation so all important sections are represented.
Add paper listing, deletion, and per-user access controls.
Build and validate an experimental AI-generated-text detector.
Add tests, logging, error handling, and deployment configuration.
Security
Do not commit `.env`, API keys, uploaded confidential papers,
virtual environments, or local vector database files.
Add size/type validation and safe filenames to PDF upload handling.
Configure CORS narrowly for production.
Add authentication, authorization, rate limits, and request
validation before exposing the API publicly.
Consider privacy and retention requirements before storing research
papers.
Rotate any API credential that was accidentally exposed.
Disclaimer
This project is intended to support research-paper reading and analysis.
AI-generated summaries and reviews may contain errors and should be
verified against the original document. Any future AI-text detector
should be used as an uncertain indicator for further review, not as a
definitive judgement about authorship or academic misconduct.
Author
Your Name
Add your GitHub profile, LinkedIn profile, screenshots, demo link, and
contact details here if you want them included in the public repository.
