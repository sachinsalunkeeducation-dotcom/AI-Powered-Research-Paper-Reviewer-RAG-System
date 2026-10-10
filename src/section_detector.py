import re
import pymupdf

KNOWN_SECTIONS = {
    "abstract", "introduction", "background", "related work",
    "literature review", "methodology", "methods", "materials and methods",
    "research methodology", "experiments", "experimental setup",
    "results", "discussion", "conclusion", "future work",
    "limitations", "references", "acknowledgements"
}

METADATA_PATTERNS = [
    r"^issn\b", r"^isbn\b", r"^doi\b", r"^cc-by", r"^cc license",
    r"^copyright\b", r"^available online", r"^volume\b", r"^journal\b",
    r"^www\.", r"^http",
    r".*\bemail\b.*", r".*\b@gmail\.com\b.*", r".*\b@yahoo\.com\b.*",
    r".*\bhotmail\.com\b.*", r".*\bcorresponding author\b.*",
    r".*\bassistant professor\b.*", r".*\bdepartment\b.*",
    r".*\bcollege\b.*", r".*\buniversity\b.*"
]

def normalize_heading(line):
    line = line.strip()
    # Remove trailing colons, dashes, dots, and trailing whitespace
    line = re.sub(r"[\s:\-\–\—\.]+$", "", line)
    # Remove standard numbering (e.g., 1., 1.1)
    line = re.sub(r"^\d+(\.\d+)*\.?\s*", "", line)
    # Remove Roman numbering (e.g., I., IV.)
    line = re.sub(r"^[IVXLC]+\.?\s+", "", line, flags=re.IGNORECASE)
    return line.strip().lower()

def extract_section_name(line):
    """Extracts clean section name, handling inline text like 'Abstract—In the future...'"""
    normalized = normalize_heading(line)
    
    for known in KNOWN_SECTIONS:
        # Matches exact section name or section name followed by inline separator/space
        if normalized == known or re.match(r"^" + re.escape(known) + r"[\s:\-\–\—\.]", normalized):
            return known
            
    return normalized

def is_metadata(line):
    clean = line.strip().lower()
    for pattern in METADATA_PATTERNS:
        if re.match(pattern, clean):
            return True
    return False

def is_section_heading(line):
    line = line.strip()
    if not line or is_metadata(line):
        return False

    normalized = normalize_heading(line)

    # 1. Known section names (handles exact and inline headings)
    for known in KNOWN_SECTIONS:
        if normalized == known or re.match(r"^" + re.escape(known) + r"[\s:\-\–\—\.]", normalized):
            return True

    # Reject very long lines for generic pattern detection
    if len(line) > 100:
        return False

    # 2. Numbered headings
    if re.match(r"^\d+(\.\d+)*\.?\s+[A-Za-z]", line):
        return True

    # 3. Roman numeral headings
    if re.match(r"^[IVXLC]+\.?\s+[A-Za-z]", line):
        return True

    words = line.split()

    # 4. ALL CAPS headings (allows single-word headers like 'ABSTRACT')
    if line.isupper() and 1 <= len(words) <= 8:
        return True

    # 5. Title-style headings (allows single-word headers)
    if 1 <= len(words) <= 6:
        alphabetic_words = [w for w in words if w[0].isalpha()]
        if alphabetic_words:
            capitalized = sum(w[0].isupper() for w in alphabetic_words)
            if (capitalized / len(alphabetic_words)) >= 0.7:
                return True

    return False

def detect_sections_from_pages(pages):
    results = []
    current_section = "unknown"

    for page in pages:
        page_number = page["page"]
        lines = page["text"].splitlines()

        for line in lines:
            clean_line = line.strip()
            if not clean_line:
                continue

            if is_section_heading(clean_line):
                current_section = extract_section_name(clean_line)

            results.append({
                "page": page_number,
                "section": current_section,
                "text": clean_line
            })

    return results

def detect_sections_from_pdf(pdf_path):
    doc = pymupdf.open(pdf_path)
    pages = []
    
    for page_num, page in enumerate(doc, start=1):
        pages.append({
            "page": page_num,
            "text": page.get_text()
        })
        
    return detect_sections_from_pages(pages)

def assign_sections_to_pages(pages):

    current_section = "unknown"

    updated_pages = []

    for page in pages:

        page_number = page["page"]
        text = page["text"]

        lines = text.splitlines()

        updated_lines = []

        for line in lines:

            clean_line = line.strip()

            if not clean_line:
                continue

            if is_section_heading(
                clean_line
            ):

                current_section = normalize_heading(
                    clean_line
                )

            updated_lines.append(
                clean_line
            )

        updated_pages.append({
            "page": page_number,
            "text": "\n".join(
                updated_lines
            ),
            "section": current_section
        })

    return updated_pages