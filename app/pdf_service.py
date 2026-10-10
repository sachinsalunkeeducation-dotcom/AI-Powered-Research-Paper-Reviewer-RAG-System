import pymupdf


class PDFExtractionError(Exception):
    """Raised when a PDF can't be opened or read."""
    pass


def extract_pages(pdf_path):
    """
    Opens a PDF and returns a list of {"page": n, "text": "..."} dicts,
    one per page. Raises PDFExtractionError with a human-readable message
    if the file is corrupted, encrypted, or not actually a PDF.
    """

    try:
        doc = pymupdf.open(pdf_path)
    except Exception as e:
        raise PDFExtractionError(
            f"Could not open PDF file. It may be corrupted or not a "
            f"valid PDF. Details: {e}"
        )

    if doc.is_encrypted:
        doc.close()
        raise PDFExtractionError(
            "This PDF is password-protected. Please upload an "
            "unprotected file."
        )

    if doc.page_count == 0:
        doc.close()
        raise PDFExtractionError("The PDF has no pages.")

    pages = []

    try:
        for page_number, page in enumerate(doc, start=1):
            text = page.get_text()
            pages.append({
                "page": page_number,
                "text": text
            })
    finally:
        doc.close()

    # A PDF that's just scanned images (no OCR text layer) will open fine
    # but produce empty text on every page. Catch that early with a clear
    # message rather than letting the pipeline silently produce nothing.
    total_text_length = sum(len(p["text"].strip()) for p in pages)
    if total_text_length == 0:
        raise PDFExtractionError(
            "No extractable text was found in this PDF. It may be a "
            "scanned document without OCR text. Try a text-based PDF, "
            "or run OCR on it first."
        )

    return pages
