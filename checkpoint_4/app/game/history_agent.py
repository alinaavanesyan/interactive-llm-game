"""
History Agent - отслеживание развития сюжета и управление игровыми событиями
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
from app.ml.optimized_rag_pipeline import get_rag_pipeline

logger = logging.getLogger(__name__)

class HistoryAgent:
    """
    Агент, отслеживающий развитие сюжета в игре.

    Задачи:
    1. Вести историю взаимодействий с персонажами
    2. Отслеживать изменения в отношениях между персонажами
    3. Управлять сюжетными событиями и квестами
    4. Обеспечивать консистентность сюжета
    """

    def __init__(self, game_session):
        self.session = game_session
        self.rag = get_rag_pipeline()
        self.story_context = []  # История всех событий
        self.character_states = {}  # Состояния персонажей

        logger.info(f"HistoryAgent initialized for session {game_session.id}")

    def add_story_event(self, event: Dict):
        """Добавить событие в историю сюжета"""
        event["timestamp"] = datetime.utcnow().isoformat()
        self.story_context.append(event)
        logger.info(f"Story event added: {event.get('type', 'unknown')}")

    def get_story_summary(self, num_recent: int = 5) -> str:
        """Получить краткую историю последних событий"""
        recent_events = self.story_context[-num_recent:]

        summary = "Recent events:\n"
        for event in recent_events:
            if event.get("type") == "dialogue":
                summary += f"- You talked with {event.get('character')} about {event.get('topic')}\n"
            elif event.get("type") == "movement":
                summary += f"- You went to {event.get('location')}\n"
            elif event.get("type") == "item":
                summary += f"- You took {event.get('item')}\n"

        return summary

    def should_trigger_special_event(self, game_session) -> Optional[Dict]:
        """
        Проверить, должно ли произойти какое-то специальное событие

        Примеры триггеров:
        - Посещение всех локаций → финальная сцена
        - Низкое здоровье → сцена спасения
        - Высокое доверие NPC → специальный диалог
        """

        # Триггер 1: Посещение всех локаций
        if len(game_session.visited_locations) >= 3:
            if "final_scene_triggered" not in game_session.completed_tasks:
                return {
                    "type": "final_scene",
                    "title": "A Moment of Clarity",
                    "description": "After visiting all these places, you finally understand something important about BoJack."
                }

        # Триггер 2: Низкое здоровье
        if game_session.health < 20:
            return {
                "type": "danger",
                "title": "You're in danger!",
                "description": "Your health is critically low. You need to rest."
            }

        # Триггер 3: Высокое доверие с персонажем
        for npc, relationship in game_session.npc_relationships.items():
            if relationship.get("trust", 0) > 80:
                if f"special_dialog_{npc}" not in game_session.completed_tasks:
                    return {
                        "type": "special_dialogue",
                        "character": npc,
                        "title": f"{npc} trusts you",
                        "description": f"{npc} seems ready to share something important with you."
                    }

        return None

    def enrich_dialogue_context(
        self,
        character: str,
        question: str,
        game_session
    ) -> Dict:
        """
        Обогатить контекст диалога информацией из истории сюжета

        Это помогает RAG pipeline лучше понять контекст и генерировать более релевантные ответы
        """

        context = {
            "location": game_session.current_location,
            "health": game_session.health,
            "inventory": game_session.inventory.get("items", []),
            "character_mood": game_session.npc_relationships.get(character, {}).get("mood", "neutral"),
            "character_trust": game_session.npc_relationships.get(character, {}).get("trust", 50),
        }

        # Добавить информацию о предыдущих диалогах с этим персонажем
        character_dialogue_history = [
            event for event in self.story_context
            if event.get("type") == "dialogue" and event.get("character") == character
        ]

        if character_dialogue_history:
            context["previous_topics"] = [
                event.get("topic") for event in character_dialogue_history[-3:]  # Последние 3 диалога
            ]

        # Добавить контекст о других персонажах в локации
        from app.game.engine import GameEngine
        engine = GameEngine()
        current_loc = engine.locations.get(game_session.current_location, {})
        other_npcs = [npc for npc in current_loc.get("npcs", []) if npc != character]
        if other_npcs:
            context["other_npcs_present"] = other_npcs

        return context

    def process_dialogue_result(
        self,
        character: str,
        question: str,
        response: str,
        metrics: Dict,
        game_session
    ):
        """
        Обработать результат диалога и обновить состояние

        Здесь можно:
        1. Добавить событие в историю
        2. Обновить отношения с персонажем
        3. Проверить триггеры квестов/событий
        """

        # Добавить событие
        dialogue_event = {
            "type": "dialogue",
            "character": character,
            "topic": question,
            "response": response,
            "retrieval_metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }

        self.add_story_event(dialogue_event)

        # Логирование
        logger.info(f"Dialogue recorded: {character} - Quality metrics: {metrics}")

        # Можно добавить логику изменения настроения персонажа
        # в зависимости от результата диалога

    def get_game_context_for_llm(self, game_session) -> str:
        """
        Построить полный контекст игры для передачи в LLM

        Используется для более контекстных ответов LLM
        """

        context_str = f"""
=== GAME CONTEXT ===
Current Location: {game_session.current_location}
Health: {game_session.health}/100
Experience: {game_session.experience}
Inventory: {', '.join(game_session.inventory.get('items', [])) or 'empty'}
Visited Locations: {', '.join(game_session.visited_locations)}

=== RELATIONSHIPS ===
"""

        for npc, rel in game_session.npc_relationships.items():
            context_str += f"- {npc}: Trust {rel.get('trust', 50)}/100, Mood: {rel.get('mood', 'neutral')}\n"

        # Последние события
        context_str += "\n=== RECENT EVENTS ===\n"
        context_str += self.get_story_summary(3)

        return context_str

    def check_game_over_conditions(self, game_session) -> Optional[str]:
        """
        Проверить условия поражения

        Возвращает причину поражения или None если игра продолжается
        """

        if game_session.health <= 0:
            return "Your health reached zero. Game Over."

        # Можно добавить другие условия поражения
        return None

    def check_win_conditions(self, game_session) -> Optional[str]:
        """
        Проверить условия победы

        Возвращает причину победы или None если игра продолжается
        """

        # Пример: посещение всех локаций + диалоги со всеми персонажами
        if (len(game_session.visited_locations) >= 3 and
            game_session.experience >= 100 and
            "final_dialogue_completed" in game_session.completed_tasks):
            return "You have completed your journey. Congratulations!"

        return None