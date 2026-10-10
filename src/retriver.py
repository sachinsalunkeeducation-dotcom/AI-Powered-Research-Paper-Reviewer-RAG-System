import chromadb
from sentence_transformers import SentenceTransformer
from llm import LLMService


client = chromadb.PersistentClient(
    path='C:\\Users\\acer\\Documents\\research-paper-reviewer\\chroma_db'
)

collection = client.get_collection(
    name="research_paper"
)


model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


question = "What is this research paper mainly about?"

question_embedding = model.encode(question).tolist()

results = collection.query(
    query_embeddings=[question_embedding],
    n_results=3
)

context = "\n\n".join(
    results["documents"][0]
)

system_prompt = """
You are an expert research paper reviewer.

Answer using only the provided context.
Do not hallucinate.
"""

user_prompt = f"""
Context:

{context}

Question:
{question}
"""

llm = LLMService()

answer = llm.generate(
    system_prompt,
    user_prompt
)
print("---------------ANSWER-----------")
print(answer)
# results = collection.query(
#     query_embeddings=[question_embedding],
#     n_results=3
# )


# context = "\n\n".join(
#     results["documents"][0]
# )
# print(context)