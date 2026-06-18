import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
CHROMA_PATH = os.path.join(BASE_DIR, "chroma_store_aug")
COLLECTION_NAME = "bojack_script"

# Ленивая инициализация — не открываем ChromaDB при импорте
_embedder = None
_client = None
_collection = None
_model = None


def _get_resources():
    global _embedder, _client, _collection, _model
    if _collection is None:
        import chromadb
        from sentence_transformers import SentenceTransformer
        from groq import Groq
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
        _client = chromadb.PersistentClient(path=CHROMA_PATH)
        _collection = _client.get_or_create_collection(name=COLLECTION_NAME)
        _model = Groq(api_key=os.getenv("GROQ_API_KEY"))
    return _embedder, _collection, _model


def rag_forward(question: str, character: str):
    embedder, collection, model = _get_resources()

    character_map = {
        "bojack": "BOJACK", "diane": "DIANE NGUEYEN",
        "caroline": "PRINCESS CAROLYN", "todd": "TODD", "dog": "MR. PEANUTBUTTER"
    }
    query_with_character = f'Request: "{question}" for the character {character_map.get(character, character.upper())}'
    res = collection.query(query_texts=[query_with_character], n_results=10)
    chunks = res["documents"][0]

    context = "\n".join(chunks)

    character_description = {
        "bojack": "Боджек — бывшая звезда телешоу, саркастичен, циничен, страдает от депрессии.",
        "diane": "Диана — писатель и активист, честная, глубокомысленная.",
        "caroline": "Кэролин — продюсер, прагматична и деловита.",
        "todd": "Тодд — наивный и добродушный друг Боджека.",
        "dog": "Мистер Подхвост — верный и позитивный."
    }

    prompt = f"""Отвечай строго в образе персонажа на русском языке.
{character_description.get(character, '')}

Контекст: {context}
Вопрос: {question}
Ответ:"""

    output = model.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=600, temperature=0.7
    )
    return output.choices[0].message.content.strip(), chunks
