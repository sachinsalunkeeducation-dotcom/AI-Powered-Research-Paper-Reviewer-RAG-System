import chromadb


client = chromadb.PersistentClient(
    path="./chroma_db"
)

collection = client.get_collection(
    name="research_paper"
)

results = collection.get(
    include=["documents", "metadatas"]
)

print("Total chunks:", len(results["ids"]))

for i in range(1, len(results["ids"])):

    print("\n==============================")
    print("ID:", results["ids"][i])
    print("Metadata:", results["metadatas"][i])
    print("Document:")
    print(results["documents"][i][:300])