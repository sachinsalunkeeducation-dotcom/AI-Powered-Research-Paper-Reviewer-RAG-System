import chromadb

from app.config import CHROMA_DIR
from src.embedding import create_embeddings


client = chromadb.PersistentClient(path=str(CHROMA_DIR))

collection = client.get_or_create_collection(
    name="research_paper"
)


def paper_exists(paper_id: str) -> bool:
    """
    Checks whether any chunks exist for this paper_id, so routes can
    return a proper 404 instead of silently returning empty results.
    """
    results = collection.get(
        where={"paper_id": paper_id},
        limit=1
    )
    return len(results.get("ids", [])) > 0


def retrieve_chunks(
    question,
    paper_id,
    top_k=5
):

    # ---------------------------------------------
    # 1. Convert question into embedding
    # ---------------------------------------------

    query_embedding = create_embeddings([question])

    # ---------------------------------------------
    # 2. Search ChromaDB
    # ---------------------------------------------

    results = collection.query(
        query_embeddings=query_embedding.tolist(),
        n_results=top_k,
        where={"paper_id": paper_id}
    )

    # ---------------------------------------------
    # 3. Convert Chroma response into clean list
    # ---------------------------------------------

    retrieved_chunks = []

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for i in range(len(documents)):
        retrieved_chunks.append({
            "text": documents[i],
            "metadata": metadatas[i],
            "distance": distances[i]
        })

    return retrieved_chunks

def list_papers():
    """
    ChromaDB मध्ये साठवलेल्या सगळ्या unique papers ची यादी देतं,
    प्रत्येकाचं filename आणि chunk count सह.
    """
    results = collection.get(
        include=["metadatas"]
    )

    metadatas = results.get("metadatas", [])

    papers = {}

    for metadata in metadatas:
        paper_id = metadata.get("paper_id")

        if paper_id is None:
            continue

        if paper_id not in papers:
            papers[paper_id] = {
                "paper_id": paper_id,
                "filename": metadata.get("filename", "unknown.pdf"),
                "chunk_count": 0
            }

        papers[paper_id]["chunk_count"] += 1

    return list(papers.values())


def get_paper_chunks(paper_id: str):
    """
    दिलेल्या paper_id चे सगळे chunks (text + metadata) परत देतं,
    जेणेकरून यूजर ते बघून माहिती बरोबर आहे का verify करू शकेल.
    """
    results = collection.get(
        where={"paper_id": paper_id},
        include=["documents", "metadatas"]
    )

    documents = results.get("documents", [])
    metadatas = results.get("metadatas", [])

    chunks = []

    for i in range(len(documents)):
        chunks.append({
            "text": documents[i],
            "metadata": metadatas[i]
        })

    # page आणि chunk_id नुसार क्रमाने लावा, म्हणजे वाचायला सोपं जाईल
    chunks.sort(
        key=lambda c: (
            c["metadata"].get("page", 0),
            c["metadata"].get("chunk_id", 0)
        )
    )

    return chunks
