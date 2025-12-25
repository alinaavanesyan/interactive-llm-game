import os
from dotenv import load_dotenv
import chromadb
from sentence_transformers import SentenceTransformer
from groq import Groq

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
CHROMA_PATH = os.path.join(BASE_DIR, "chroma_augmented_store")

COLLECTION_NAME = "bojack_script"

embedder = SentenceTransformer("all-MiniLM-L6-v2")

client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_or_create_collection(name=COLLECTION_NAME)

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
model = Groq(api_key=GROQ_API_KEY)


def retrieve_chunks(query: str, n_results=3):
    res = collection.query(query_texts=[query], n_results=n_results)
    docs = res["documents"][0]
    metas = res["metadatas"][0]
    if not docs:
        raise ValueError("empty retrieval")
    return docs, metas


def build_context(chunks, metas):
    context = ""
    for doc, meta in zip(chunks, metas):
        role = meta.get("role", "UNKNOWN")
        context += f"{role}: {doc}\n"
    return context


def generate_answer(query: str, context: str, character: str):
    prompt = f"""
    Answer the question below based on the context.
    Do not hallucinate.
    Answer strictly in the style of {character}.

    Context:
    {context}

    Question:
    {query}

    Answer:
    """

    output = model.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=600,
        temperature=0.7
    )
    return output.choices[0].message.content.strip()


def rag_forward(question: str, character: str):
    chunks, metas = retrieve_chunks(question)
    context = build_context(chunks, metas)
    answer = generate_answer(question, context, character)
    return answer, chunks