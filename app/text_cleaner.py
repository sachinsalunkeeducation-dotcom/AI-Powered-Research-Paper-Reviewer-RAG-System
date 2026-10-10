import re
from collections import Counter


def clean_pages(pages):

    # Count how many pages contain each line
    line_counts = Counter()

    for page in pages:

        lines = page["text"].splitlines()

        for line in lines:

            clean_line = line.strip()

            if clean_line:
                line_counts[clean_line] += 1

    # Lines appearing on many pages are likely headers/footers
    repeated_lines = {
        line
        for line, count in line_counts.items()
        if count >= 3
    }

    cleaned_pages = []

    for page in pages:

        lines = page["text"].splitlines()

        cleaned_lines = []

        for line in lines:

            clean_line = line.strip()

            # Skip empty lines
            if not clean_line:
                continue

            # Remove repeated header/footer lines
            if clean_line in repeated_lines:
                continue

            # Remove standalone page numbers
            if re.fullmatch(r"\d+", clean_line):
                continue

            cleaned_lines.append(clean_line)

        cleaned_pages.append({
            "page": page["page"],
            "text": "\n".join(cleaned_lines)
        })

    return cleaned_pages