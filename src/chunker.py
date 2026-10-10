from src.section_detector import (
    is_section_heading,
    normalize_heading
)


def create_chunks(
    pages,
    chunk_size=800,
    overlap=100
):

    chunks = []

    current_section = "unknown"

    for page in pages:

        page_number = page["page"]

        lines = page["text"].splitlines()

        current_words = []

        for line in lines:

            clean_line = line.strip()

            if not clean_line:
                continue

            # -----------------------------------------
            # Detect section heading
            # -----------------------------------------

            if is_section_heading(
                clean_line
            ):

                # Save existing text before
                # changing section
                if current_words:

                    chunks.extend(
                        make_chunks(
                            current_words,
                            page_number,
                            current_section,
                            chunk_size,
                            overlap
                        )
                    )

                    current_words = []

                current_section = normalize_heading(
                    clean_line
                )

                continue

            # -----------------------------------------
            # Add normal text
            # -----------------------------------------

            current_words.extend(
                clean_line.split()
            )

        # ---------------------------------------------
        # Remaining text on page
        # ---------------------------------------------

        if current_words:

            chunks.extend(
                make_chunks(
                    current_words,
                    page_number,
                    current_section,
                    chunk_size,
                    overlap
                )
            )

    return chunks


def make_chunks(
    words,
    page_number,
    section,
    chunk_size,
    overlap
):

    chunks = []

    start = 0

    while start < len(words):

        end = start + chunk_size

        chunk_words = words[
            start:end
        ]

        chunk_text = " ".join(
            chunk_words
        )

        chunks.append({

            "text": chunk_text,

            "page": page_number,

            "section": section

        })

        start += (
            chunk_size - overlap
        )

    return chunks