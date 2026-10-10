import json
import re

from app.retrieval_service import retrieve_chunks
from src.llm import LLMService


llm = LLMService()


# =========================================================
# HELPER: robustly parse LLM JSON output
# =========================================================

def _parse_llm_json(raw_text: str) -> dict:
    """
    LLMs often wrap JSON in ```json fences or add a sentence before/after
    it, even when explicitly told not to. This tries a few strategies
    before giving up, so a single stray character doesn't blow up the
    whole review.
    """

    text = raw_text.strip()

    # Strategy 1: parse as-is
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strategy 2: strip ```json ... ``` or ``` ... ``` fences
    fenced = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    try:
        return json.loads(fenced)
    except json.JSONDecodeError:
        pass

    # Strategy 3: grab the first { ... } block found anywhere in the text
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    # All strategies failed
    raise ValueError("Could not parse LLM response as JSON")


# =========================================================
# ASK A QUESTION ABOUT PAPER
# =========================================================

def answer_question(
    paper_id,
    question
):

    # -----------------------------------------
    # 1. Retrieve relevant chunks
    # -----------------------------------------

    results = retrieve_chunks(
        question,
        paper_id,
        top_k=5
    )

    if not results:
        return {
            "answer": (
                "I couldn't find any relevant content in this paper "
                "to answer that question."
            ),
            "sources": []
        }

    # -----------------------------------------
    # 2. Build context
    # -----------------------------------------

    context_parts = []

    for result in results:

        metadata = result["metadata"]

        context_parts.append(
            f"""
Page: {metadata.get("page")}
Section: {metadata.get("section")}

{result["text"]}
"""
        )

    context = "\n\n---\n\n".join(context_parts)

    # -----------------------------------------
    # 3. System prompt
    # -----------------------------------------

    system_prompt = """
You are an AI research paper assistant.

Answer the user's question using only
the provided research paper context.

Do not invent information.

If the answer cannot be found in the
provided context, say that the information
is not available in the retrieved paper
content.

Give a clear and concise answer.
"""

    # -----------------------------------------
    # 4. User prompt
    # -----------------------------------------

    user_prompt = f"""
Research paper context:

{context}


Question:

{question}


Answer the question using the context above.
"""

    # -----------------------------------------
    # 5. Generate answer
    # -----------------------------------------

    try:
        answer = llm.generate(system_prompt, user_prompt)
    except Exception as e:
        answer = (
            "Sorry, I couldn't reach the language model to generate an "
            "answer right now. Please try again shortly."
        )

    return {
        "answer": answer,
        "sources": [result["metadata"] for result in results]
    }


# =========================================================
# AUTOMATIC RESEARCH PAPER REVIEW
# =========================================================

def generate_review(
    paper_id
):

    # =========================================
    # 1. Questions for different review areas
    # =========================================

    questions = {

        "summary":
            "What is this research paper mainly about?",

        "methodology":
            "What methodology, methods, datasets, "
            "experiments, or approaches does the paper use?",

        "results":
            "What are the main results or findings "
            "of the research?",

        "limitations":
            "What limitations, weaknesses, "
            "or research gaps are mentioned "
            "or evident in the paper?",

        "conclusion":
            "What are the main conclusions "
            "and future research directions?"
    }

    all_results = []

    # =========================================
    # 2. Retrieve chunks
    # =========================================

    for category, question in questions.items():

        results = retrieve_chunks(
            question,
            paper_id,
            top_k=3
        )

        for result in results:

            all_results.append({
                "category": category,
                "text": result["text"],
                "metadata": result["metadata"]
            })

    if not all_results:
        return {
            "review": {
                "error": "No content was retrieved for this paper."
            },
            "sources": []
        }

    # =========================================
    # 3. Remove duplicate chunks
    # =========================================

    unique_chunks = {}

    for result in all_results:

        chunk_id = result["metadata"].get("chunk_id")

        if chunk_id is not None:
            unique_chunks[chunk_id] = result

    # =========================================
    # 4. Build context
    # =========================================

    context_parts = []

    for result in unique_chunks.values():

        metadata = result["metadata"]

        context_parts.append(
            f"""
Category: {result["category"]}

Page: {metadata.get("page")}

Section: {metadata.get("section")}

Text:
{result["text"]}
"""
        )

    context = "\n\n--------------------\n\n".join(context_parts)

    # =========================================
    # 5. Limit context
    # =========================================

    MAX_CONTEXT_CHARS = 30000

    context = context[:MAX_CONTEXT_CHARS]

    # =========================================
    # 6. System prompt
    # =========================================

    system_prompt = """
You are an expert research paper reviewer.

Analyze the research paper using ONLY the
provided paper context.

Do not invent facts.

If information is not available in the
provided context, say:

"Not enough information available in
the retrieved paper content."

Evaluate the paper objectively.

Return ONLY valid JSON, with no preamble,
no explanation, and no markdown code fences.
Your entire response must be a single JSON
object and nothing else.

Use exactly this structure:

{
    "summary": "...",

    "methodology": "...",

    "results": "...",

    "strengths": [
        "...",
        "..."
    ],

    "weaknesses": [
        "...",
        "..."
    ],

    "originality": "...",

    "writing_quality": "...",

    "references": "...",

    "structure": "...",

    "overall_assessment": "..."
}
"""

    # =========================================
    # 7. User prompt
    # =========================================

    user_prompt = f"""
Review the research paper using the context
below.

PAPER CONTEXT:

{context}

Provide the complete research paper review
in the required JSON format.
"""

    # =========================================
    # 8. Call the LLM
    # =========================================

    try:
        review_text = llm.generate(system_prompt, user_prompt)
    except Exception:
        return {
            "review": {
                "error": "Failed to reach the language model."
            },
            "sources": [
                result["metadata"] for result in unique_chunks.values()
            ]
        }

    # =========================================
    # 9. Convert LLM output to a Python dict
    # =========================================

    try:
        review = _parse_llm_json(review_text)
    except ValueError:
        review = {
            "error": "LLM did not return valid JSON",
            "raw_response": review_text
        }

    # =========================================
    # 10. Return review
    # =========================================

    return {
        "review": review,
        "sources": [
            result["metadata"] for result in unique_chunks.values()
        ]
    }
