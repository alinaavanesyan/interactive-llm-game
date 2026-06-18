"""
Оптимизированный RAG Pipeline с лучшими практиками из чекпоинтов 3, 5, 6
- BGE-base embeddings (вместо all-MiniLM-L6-v2)
- Hybrid RRF retrieval (BM25 + Dense, α=0.5, K=7)
- Cross-Encoder reranking (ms-marco-MiniLM-L12)
- Llama 3.3-70B для генерации (вместо 3.1-8B)
- Аугментированный корпус
"""

import os
from dotenv import load_dotenv
import chromadb
from sentence_transformers import SentenceTransformer, CrossEncoder
from rank_bm25 import BM25Okapi
from groq import Groq
import numpy as np
from typing import List, Tuple, Dict
import logging

logger = logging.getLogger(__name__)

load_dotenv()

class OptimizedRAGPipeline:
    def __init__(self):
        # Конфигурация
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.chroma_path = os.path.join(self.base_dir, "chroma_store_aug")

        # === BEST PRACTICES ===
        # all-MiniLM-L6-v2 (384-dim) — соответствует размерности коллекции в Chroma
        logger.info("Loading sentence embeddings...")
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        self.embedding_dim = self.embedder.get_sentence_embedding_dimension()

        # 2. Chroma DB with dense vectors
        self.client = chromadb.PersistentClient(path=self.chroma_path)
        self.collection = self.client.get_or_create_collection(
            name="bojack_script",
            metadata={"hnsw:space": "cosine"}
        )

        # 3. BM25 для гибридного поиска (checkpoint 5)
        logger.info("Building BM25 index...")
        self.documents_cache = self._load_documents_cache()
        self.bm25 = self._build_bm25_index()

        # 4. Cross-Encoder reranker (checkpoint 6 - дал +104% по Top-1)
        logger.info("Loading Cross-Encoder reranker...")
        try:
            self.cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L12-v2", device="cpu")
        except Exception as e:
            logger.warning(f"Cross-Encoder failed to load: {e}. Reranking will be skipped.")
            self.cross_encoder = None

        # 5. Llama 3.3-70B (checkpoint 6 - лучше на 14% vs 3.1-8B)
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
        self.llm_client = Groq(api_key=self.groq_api_key)

        # Параметры retrieval (лучшие из checkpoint 5)
        self.hybrid_alpha = 0.5  # Баланс между BM25 и Dense
        self.retrieval_k = 7     # Гибридный поиск
        self.ce_candidates = 50  # Кандидатов для Cross-Encoder

        logger.info("OptimizedRAGPipeline initialized successfully")

    def _load_documents_cache(self) -> List[str]:
        """Загрузить все документы из Chroma для BM25"""
        try:
            result = self.collection.get()
            return result.get("documents", [])
        except Exception as e:
            logger.warning(f"Could not load documents cache: {e}")
            return []

    def _build_bm25_index(self) -> BM25Okapi:
        """Построить BM25 индекс"""
        if not self.documents_cache:
            raise ValueError("No documents loaded for BM25 index")

        tokenized_docs = [doc.lower().split() for doc in self.documents_cache]
        return BM25Okapi(tokenized_docs)

    def retrieve_hybrid(self, query: str, character: str, k: int = None) -> Tuple[List[str], List[Dict]]:
        """
        Гибридный поиск через RRF (Reciprocal Rank Fusion)
        Combination: BM25 (sparse) + Dense (semantic)

        Alpha балансирует вклад: score = α*rank_bm25 + (1-α)*rank_dense

        Возвращает: (список чанков, метаданные)
        """
        if k is None:
            k = self.retrieval_k

        # 1. BM25 retrieval (sparse - по ключевым словам)
        query_tokens = query.lower().split()
        bm25_scores = self.bm25.get_scores(query_tokens)
        bm25_top_indices = np.argsort(bm25_scores)[::-1][:self.ce_candidates]

        # 2. Dense retrieval (semantic - через embeddings)
        query_embedding = self.embedder.encode(query, convert_to_numpy=True)
        dense_results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=self.ce_candidates
        )

        dense_indices = [self.documents_cache.index(doc)
                        for doc in dense_results["documents"][0]
                        if doc in self.documents_cache]

        # 3. RRF Fusion: комбинируем два метода
        fused_scores = {}

        # BM25 ранги
        for rank, idx in enumerate(bm25_top_indices):
            if idx not in fused_scores:
                fused_scores[idx] = 0
            fused_scores[idx] += self.hybrid_alpha * (1.0 / (rank + 1))

        # Dense ранги
        for rank, idx in enumerate(dense_indices):
            if idx not in fused_scores:
                fused_scores[idx] = 0
            fused_scores[idx] += (1 - self.hybrid_alpha) * (1.0 / (rank + 1))

        # Топ K документов после RRF
        top_fused = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)[:k]
        top_indices = [idx for idx, score in top_fused]

        # Получить документы и метаданные
        documents = [self.documents_cache[idx] for idx in top_indices]
        metadatas = self._get_metadatas(top_indices)

        return documents, metadatas

    def _get_metadatas(self, indices: List[int]) -> List[Dict]:
        """Получить метаданные для документов"""
        all_results = self.collection.get()
        metadatas = all_results.get("metadatas", [])
        return [metadatas[idx] if idx < len(metadatas) else {} for idx in indices]

    def rerank_cross_encoder(self, query: str, documents: List[str], top_k: int = 5) -> Tuple[List[str], List[float]]:
        """
        Cross-Encoder reranking (checkpoint 6)
        Более точное ранжирование: прогоняет каждую пару (query, document) через трансформер

        Дал +104% по Top-1 vs базовый semantic поиск!
        """
        if not documents:
            return [], []

        # Если cross-encoder не загрузился — вернуть без reranking
        if self.cross_encoder is None:
            return documents[:top_k], [0.0] * min(top_k, len(documents))

        pairs = [[query, doc] for doc in documents]
        scores = self.cross_encoder.predict(pairs)
        ranked_indices = np.argsort(scores)[::-1][:top_k]
        return [documents[i] for i in ranked_indices], [float(scores[i]) for i in ranked_indices]

    def generate_response(
        self,
        query: str,
        character: str,
        context_docs: List[str],
        game_context: Dict = None,
        case_context: str = "",
        chat_history: list = None
    ) -> str:
        """
        Генерировать ответ через Llama 3.3-70B с контекстом игры

        game_context = {
            "location": "living_room",
            "health": 100,
            "inventory": ["key", "apple"],
            "character_mood": "happy",
            "previous_dialogue": "..."
        }
        """

        character_descriptions = {
            "bojack": """BOJACK — бывшая звезда телевизионного шоу. Он саркастичен, циничен, страдает от депрессии и алкоголизма.
В общении наполнен чёрным юмором, часто защищается иронией. Глубоко несчастный, но скрывает это под маской равнодушия.""",

            "diane": """DIANE — интеллектуальная и глубокомысленная женщина. Писатель и активист.
Стремится быть честной и справедливой. Чувствует себя потерянной в поиске смысла. Сочувствует другим.""",

            "caroline": """PRINCESS CAROLYN — прагматичная и деловая женщина. Продюсер.
Находит решения в самых сложных ситуациях. Холодная и расчётливая, но иногда проявляет заботу к близким.""",

            "todd": """TODD — наивный и энергичный человек. Часто попадает в нелепые ситуации.
Не очень серьёзен, но добр и искренен. Оптимистичен и верит в лучшее.""",

            "dog": """MR. PEANUTBUTTER — верный и добродушный персонаж. Немного наивный.
Всегда готов помочь своим друзьям, даже если это приводит к забавным последствиям. Позитивный.""",
        }

        # Построить контекст
        context_str = "\n".join(context_docs)

        # Дополнить контекстом игры
        game_context_str = ""
        if game_context:
            game_context_str = f"""
ИГРОВОЙ КОНТЕКСТ:
- Локация: {game_context.get('location', 'unknown')}
- Здоровье игрока: {game_context.get('health', 100)}
- Инвентарь: {', '.join(game_context.get('inventory', []))}
- Настроение персонажа: {game_context.get('character_mood', 'neutral')}
"""

        system_msg = case_context if case_context else (
            f"Ты играешь роль {character.upper()} из сериала «Конь БоДжек». Отвечай по-русски, оставаясь в образе."
        )
        system_msg += f"\n\nОПИСАНИЕ ПЕРСОНАЖА:\n{character_descriptions.get(character, '')}"
        if game_context_str:
            system_msg += game_context_str

        user_msg = f"""КОНТЕКСТ ИЗ СЕРИАЛА:
{context_str}

ВОПРОС: {query}"""

        # Собрать messages: system + история + текущий вопрос
        messages = [{"role": "system", "content": system_msg}]
        if chat_history:
            messages.extend(chat_history[-10:])  # последние 5 пар
        messages.append({"role": "user", "content": user_msg})

        # Генерировать через Llama 3.3-70B
        message = self.llm_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=300,
            top_p=0.9
        )

        return message.choices[0].message.content.strip()

    def query(
        self,
        question: str,
        character: str,
        game_context: Dict = None,
        case_context: str = "",
        chat_history: list = None
    ) -> Tuple[str, List[str], Dict]:
        """
        Главный метод RAG pipeline

        Возвращает: (ответ, найденные чанки, метрики)
        """
        try:
            # === Stage 1: Hybrid Retrieval (checkpoint 5) ===
            logger.info(f"[Stage 1] Hybrid RRF retrieval for '{question}'")
            documents, metadatas = self.retrieve_hybrid(question, character)

            if not documents:
                return "I have no information to respond to that.", [], {"error": "No documents retrieved"}

            # === Stage 2: Cross-Encoder Reranking (checkpoint 6) ===
            logger.info(f"[Stage 2] Cross-Encoder reranking top {self.retrieval_k} -> top 5")
            reranked_docs, ce_scores = self.rerank_cross_encoder(question, documents[:self.retrieval_k], top_k=5)

            # === Stage 3: LLM Generation (checkpoint 6) ===
            logger.info(f"[Stage 3] Generating response with Llama 3.3-70B")
            response = self.generate_response(
                query=question,
                character=character,
                context_docs=reranked_docs,
                game_context=game_context,
                case_context=case_context,
                chat_history=chat_history
            )

            # Метрики
            metrics = {
                "retrieval_method": "hybrid_rrf_alpha=0.5_k=7",
                "reranker": "cross-encoder/ms-marco-MiniLM-L12-v2",
                "llm": "llama-3.3-70b-versatile",
                "cross_encoder_scores": ce_scores,
                "num_documents_retrieved": len(documents),
                "num_documents_reranked": len(reranked_docs)
            }

            logger.info(f"[Success] Generated response. CE scores: {ce_scores}")
            return response, reranked_docs, metrics

        except Exception as e:
            logger.error(f"Error in RAG pipeline: {e}")
            raise

# Глобальный экземпляр
_rag_pipeline = None

def get_rag_pipeline():
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = OptimizedRAGPipeline()
    return _rag_pipeline

# Для обратной совместимости с существующим кодом
def rag_forward(question: str, character: str):
    """Legacy function for compatibility"""
    pipeline = get_rag_pipeline()
    response, chunks, metrics = pipeline.query(question, character)
    return response, chunks