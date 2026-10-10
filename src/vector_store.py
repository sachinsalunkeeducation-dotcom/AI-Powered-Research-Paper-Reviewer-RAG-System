import chromadb

from app.config import CHROMA_DIR

client = chromadb.PersistentClient(path=str(CHROMA_DIR))

collection = client.get_or_create_collection(
    name="research_paper"
)


def store_chunks(chunks, embeddings, paper_id, filename="unknown.pdf"):

    ids = []
    documents = []
    metadatas = []

    for i, chunk in enumerate(chunks):

        ids.append(
            f"{paper_id}_chunk_{i}"
        )

        documents.append(
            chunk["text"]
        )

        metadatas.append({
            "paper_id": paper_id,
            "chunk_id": i,
            "page": chunk["page"],
            "section": chunk.get(
                "section",
                "unknown"
            ),
            "source": chunk.get(
                "source",
                "uploaded_pdf"
            ),
            "filename": filename
        })

    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings.tolist(),
        metadatas=metadatas
    )

    return len(chunks)