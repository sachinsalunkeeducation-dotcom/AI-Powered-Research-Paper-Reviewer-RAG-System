import chromadb

client = chromadb.PersistentClient(
    path="C:\\Users\\acer\\Documents\\research-paper-reviewer\\chroma_db"
)

try:
    client.delete_collection(
        name="research_paper"
    )
    print("Old collection deleted successfully.")

except Exception as e:
    print("Collection does not exist:", e)