import os
from dotenv import load_dotenv
import chromadb
from sentence_transformers import SentenceTransformer
from groq import Groq

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
CHROMA_PATH = os.path.join(BASE_DIR, "chroma_store_aug")

COLLECTION_NAME = "bojack_script"

embedder = SentenceTransformer("all-MiniLM-L6-v2")

client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_or_create_collection(name=COLLECTION_NAME)

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
model = Groq(api_key=GROQ_API_KEY)


def retrieve_chunks(query: str, character: str, n_results=10):
    character_map = {
        "bojack": "BOJACK",
        "diane": "DIANE NGUEYEN",
        "caroline": "PRINCESS CAROLYN",
        "todd": "TODD",
        "dog": "MR. PEANUTBUTTER"
    }

    query_with_character = f'''Reqest: "{query}" for the character {character_map[character]}'''
    
    res = collection.query(query_texts=[query_with_character], n_results=n_results)

    docs = res["documents"][0]
    metas = res["metadatas"][0]
    if not docs:
        raise ValueError("empty retrieval")
    return docs, metas


def build_context(chunks, metas):
    context = ""
    for doc, meta in zip(chunks, metas):
        # role = meta.get("role", "UNKNOWN")
        # context += f"{role}: {doc}\n"
        context += f"{doc}\n"
    return context

def generate_answer(query: str, context: str, character: str):
    character_description = {
        "bojack": "Боджек (BOJACK) — бывшая звезда телевизионного шоу, страдающая от депрессии, алкоголизма и проблем в личной жизни. Он саркастичен и циничен.",
        "diane": "Диана (DIANE) — интеллектуальная и глубокомысленная женщина, работающая как писатель и активист. Она стремится быть честной, но часто чувствует себя потерянной.",
        "caroline": "Кэролин (PRINCESS CAROLYN) — прагматичная, серьезная женщина, работавшая как продюсер. Она находит решения в самых сложных ситуациях, но иногда её холодность мешает её отношениям.",
        "todd": "Тодд (TODD) — наивный и энергичный человек, который часто оказывается в нелепых ситуациях. Он не очень серьезен, но всегда добр и искренен.",
        "dog": "Мистер Подхвост (MR. PEANUTBUTTER) — верный и добродушный, но немного наивный персонаж, который всегда готов помочь своим друзьям, даже если это приводит к забавным последствиям."
    }

    prompt = f"""
    Ответьте на вопрос ниже, основываясь на контексте.
    Не выдумывайте информацию.
    Ответьте строго в стиле следующего персонажа:
    
    {character_description[character]}
    
    При ответе строго используйте русский язык.

    Контекст:
    {context}

    Вопрос:
    {query}

    Ответ:
    """

    output = model.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=600,
        temperature=0.7
    )
    return output.choices[0].message.content.strip()


def rag_forward(question: str, character: str):
    chunks, metas = retrieve_chunks(question, character)
    context = build_context(chunks, metas)
    answer = generate_answer(question, context, character)
    return answer, chunks