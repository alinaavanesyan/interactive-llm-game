"""
Game Engine - управление игровым состоянием и обработка действий
"""

import json
import os
from typing import Dict, List, Tuple, Optional
from enum import Enum
from datetime import datetime
from app.ml.optimized_rag_pipeline import get_rag_pipeline
import logging

logger = logging.getLogger(__name__)

class ActionType(Enum):
    DIALOGUE = "dialogue"
    MOVE = "move"
    TAKE = "take"
    DROP = "drop"
    INVENTORY = "inventory"
    EXAMINE = "examine"
    USE = "use"
    STATUS = "status"
    HELP = "help"

class GameEngine:
    """
    Игровой движок для управления состоянием игры и обработки действий игрока
    """

    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.world_path = os.path.join(self.base_dir, "world.json")

        # Загрузить мир игры
        self.world = self._load_world()
        self.locations = self.world.get("locations", {})
        self.npcs = self.world.get("npcs", {})
        self.items = self.world.get("items", {})

        # RAG pipeline для диалогов
        self.rag = get_rag_pipeline()

        logger.info("GameEngine initialized")

    def _load_world(self) -> Dict:
        """Загрузить описание мира из JSON"""
        if os.path.exists(self.world_path):
            with open(self.world_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            logger.warning(f"World file not found at {self.world_path}, using minimal world")
            return self._get_minimal_world()

    def _get_minimal_world(self) -> Dict:
        """Минимальный мир для тестирования"""
        return {
            "locations": {
                "living_room": {
                    "name": "Гостиная Боджека",
                    "description": "Уютная гостиная квартиры Боджека. На столе пустая бутылка виски.",
                    "npcs": ["bojack", "todd"],
                    "items": ["book", "remote"],
                    "connections": ["office", "kitchen"]
                },
                "office": {
                    "name": "Офис Кэролин",
                    "description": "Современный офис продюсера с видом на Голливуд.",
                    "npcs": ["caroline"],
                    "items": ["contract"],
                    "connections": ["living_room"]
                },
                "kitchen": {
                    "name": "Кухня",
                    "description": "Скромная кухня с холодильником и кучей посуды.",
                    "npcs": ["todd"],
                    "items": ["apple", "whiskey"],
                    "connections": ["living_room"]
                }
            },
            "npcs": {
                "bojack": {"name": "BOJACK", "full_name": "BoJack Horseman"},
                "caroline": {"name": "CAROLINE", "full_name": "Princess Carolyn"},
                "todd": {"name": "TODD", "full_name": "Todd Chavez"},
                "diane": {"name": "DIANE", "full_name": "Diane Nguyen"},
                "dog": {"name": "DOG", "full_name": "Mr. Peanutbutter"}
            },
            "items": {
                "book": {"name": "книга", "description": "Старая потёртая книга"},
                "remote": {"name": "пульт", "description": "Пульт от телевизора"},
                "apple": {"name": "яблоко", "description": "Свежее яблоко"},
                "contract": {"name": "контракт", "description": "Важный контракт"}
            }
        }

    def parse_action(self, action_text: str) -> Tuple[ActionType, Dict]:
        """
        Распарсить действие игрока в тип и параметры

        Примеры:
        - "talk to bojack about his life" -> (DIALOGUE, {"npc": "bojack", "topic": "his life"})
        - "go to office" -> (MOVE, {"location": "office"})
        - "take book" -> (TAKE, {"item": "book"})
        - "inventory" -> (INVENTORY, {})
        """
        action_lower = action_text.lower().strip()

        # === РУССКИЕ КОМАНДЫ ===
        # Движение: "перейти в X", "иди в X", "пойти в X"
        if any(action_lower.startswith(p) for p in ("перейти в ", "перейди в ", "иди в ", "пойти в ", "пойди в ", "в ")):
            for prefix in ("перейти в ", "перейди в ", "иди в ", "пойти в ", "пойди в ", "в "):
                if action_lower.startswith(prefix):
                    location = action_lower[len(prefix):]
                    return ActionType.MOVE, {"location": location.strip()}

        # Диалог: "поговори с X о Y", "поговорить с X"
        elif any(action_lower.startswith(p) for p in ("поговори с ", "поговорить с ", "спроси ", "поговорить")):
            for prefix in ("поговори с ", "поговорить с ", "спроси "):
                if action_lower.startswith(prefix):
                    rest = action_lower[len(prefix):]
                    for sep in (" о ", " об ", " про "):
                        if sep in rest:
                            npc, topic = rest.split(sep, 1)
                            return ActionType.DIALOGUE, {"npc": npc.strip(), "topic": topic.strip()}
                    return ActionType.DIALOGUE, {"npc": rest.strip(), "topic": ""}

        # Инвентарь
        elif action_lower in ("инвентарь", "предметы", "сумка", "inventory", "inv", "items", "bag"):
            return ActionType.INVENTORY, {}

        # Статус
        elif action_lower in ("статус", "здоровье", "состояние", "status", "health", "stats"):
            return ActionType.STATUS, {}

        # Помощь
        elif action_lower in ("помощь", "помоги", "справка", "команды", "help", "?", "commands"):
            return ActionType.HELP, {}

        # Осмотреться
        elif action_lower in ("осмотреться", "осмотрись", "оглядеться", "осмотр"):
            return ActionType.EXAMINE, {"target": "room"}

        # Взять
        elif any(action_lower.startswith(p) for p in ("взять ", "возьми ", "подобрать ", "take ", "get ", "pick up ")):
            for prefix in ("взять ", "возьми ", "подобрать ", "take ", "get ", "pick up "):
                if action_lower.startswith(prefix):
                    return ActionType.TAKE, {"item": action_lower[len(prefix):].strip()}

        # === АНГЛИЙСКИЕ КОМАНДЫ ===
        # Диалог
        elif any(action_lower.startswith(p) for p in ("talk to ", "talk with ", "ask ")):
            parts = action_lower
            for prefix in ("talk to ", "talk with ", "ask "):
                parts = parts.replace(prefix, "", 1)
            if " about " in parts:
                npc, topic = parts.split(" about ", 1)
                return ActionType.DIALOGUE, {"npc": npc.strip(), "topic": topic.strip()}
            return ActionType.DIALOGUE, {"npc": parts.strip(), "topic": ""}

        # Движение
        elif any(action_lower.startswith(p) for p in ("go to ", "move to ", "enter ")):
            for prefix in ("go to ", "move to ", "enter "):
                if action_lower.startswith(prefix):
                    return ActionType.MOVE, {"location": action_lower[len(prefix):].strip()}

        # Взять
        elif any(action_lower.startswith(p) for p in ("take ", "get ")):
            for prefix in ("take ", "get "):
                if action_lower.startswith(prefix):
                    return ActionType.TAKE, {"item": action_lower[len(prefix):].strip()}

        # Бросить
        elif any(action_lower.startswith(p) for p in ("drop ", "leave ", "бросить ", "брось ")):
            for prefix in ("drop ", "leave ", "бросить ", "брось "):
                if action_lower.startswith(prefix):
                    return ActionType.DROP, {"item": action_lower[len(prefix):].strip()}

        # Использовать
        elif action_lower.startswith("use "):
            return ActionType.USE, {"item": action_lower[4:].strip()}

        else:
            # По умолчанию — диалог с текущим NPC
            return ActionType.DIALOGUE, {"npc": "", "topic": action_text}

    def process_action(self, action_text: str, game_session,
                       explicit_npc: str = "", explicit_location: str = "",
                       case_context: str = "", chat_history: list = None) -> Dict:
        """
        Обработать действие игрока

        Возвращает:
        {
            "success": bool,
            "message": str,
            "game_state": updated_game_state,
            "metrics": dict (для RAG запросов)
        }
        """
        action_type, params = self.parse_action(action_text)

        # Если фронтенд передал явные npc/location — используем их
        if explicit_npc:
            params["npc"] = explicit_npc
        if explicit_location:
            game_session.current_location = explicit_location

        logger.info(f"Processing action: {action_type.value} with params {params}")

        try:
            if action_type == ActionType.DIALOGUE:
                return self.handle_dialogue(params, game_session, case_context=case_context, chat_history=chat_history or [])
            elif action_type == ActionType.MOVE:
                return self.handle_move(params, game_session)
            elif action_type == ActionType.TAKE:
                return self.handle_take(params, game_session)
            elif action_type == ActionType.DROP:
                return self.handle_drop(params, game_session)
            elif action_type == ActionType.INVENTORY:
                return self.handle_inventory(game_session)
            elif action_type == ActionType.STATUS:
                return self.handle_status(game_session)
            elif action_type == ActionType.HELP:
                return self.handle_help()
            elif action_type == ActionType.EXAMINE:
                return self.handle_examine(params, game_session)
            else:
                return {
                    "success": False,
                    "message": "Unknown action. Type 'help' for commands.",
                    "game_state": self._serialize_game_state(game_session)
                }
        except Exception as e:
            logger.error(f"Error processing action: {e}")
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "game_state": self._serialize_game_state(game_session)
            }

    def handle_dialogue(self, params: Dict, game_session, case_context: str = "", chat_history: list = None) -> Dict:
        """Обработать диалог с персонажем"""
        npc = params.get("npc", "").lower().strip()
        topic = params.get("topic", "").strip()

        current_location = game_session.current_location
        npcs_here = self.locations.get(current_location, {}).get("npcs", [])

        # Если NPC не указан — берём первого в локации
        if not npc and npcs_here:
            npc = npcs_here[0].lower()

        # Русские имена → ключи
        ru_npc = {"боджек": "bojack", "кэролин": "caroline", "принцесса кэролин": "caroline",
                  "тодд": "todd", "диана": "diane", "мистер подхвост": "dog", "пёс": "dog"}
        npc = ru_npc.get(npc, npc)

        if npc not in [n.lower() for n in npcs_here]:
            npcs_ru = ", ".join(npcs_here) or "никого"
            return {
                "success": False,
                "message": f"Здесь нет этого персонажа. Здесь: {npcs_ru}",
                "game_state": self._serialize_game_state(game_session)
            }

        question = topic if topic else "Как дела? Расскажи о себе."

        # === ИСПОЛЬЗУЕМ ОПТИМИЗИРОВАННЫЙ RAG PIPELINE ===
        game_context = {
            "location": current_location,
            "health": game_session.health,
            "inventory": game_session.inventory.get("items", []),
            "character_mood": game_session.npc_relationships.get(npc, {}).get("mood", "neutral")
        }

        try:
            response, chunks, metrics = self.rag.query(question, npc, game_context=game_context, case_context=case_context, chat_history=chat_history or [])
        except Exception as e:
            logger.warning(f"RAG pipeline failed, using direct LLM fallback: {e}")
            response = self._fallback_response(npc, topic or question, game_context, case_context=case_context)
            chunks, metrics = [], {"fallback": True}

        # Обновить отношения с персонажем
        if npc not in game_session.npc_relationships:
            game_session.npc_relationships[npc] = {"trust": 50, "mood": "neutral"}
        game_session.npc_relationships[npc]["trust"] = min(100,
            game_session.npc_relationships[npc]["trust"] + 5)

        return {
            "success": True,
            "message": response,
            "game_state": {**self._serialize_game_state(game_session), "character": npc},
            "metrics": metrics,
            "retrieved_chunks": chunks
        }

    def _fallback_response(self, npc: str, topic: str, game_context: Dict, case_context: str = "") -> str:
        """Прямой LLM-ответ без RAG когда Chroma DB недоступна"""
        import os
        from groq import Groq
        from dotenv import load_dotenv
        load_dotenv()

        npc_descriptions = {
            "bojack": "Ты — Боджек Horseman, бывшая звезда телешоу. Саркастичен, циничен, страдаешь от депрессии. Отвечай коротко, в образе.",
            "diane": "Ты — Диана Нгуен, писатель и активист. Умная, честная, ищешь смысл. Отвечай коротко, в образе.",
            "caroline": "Ты — Принцесса Кэролин, продюсер. Прагматична, деловита. Отвечай коротко, в образе.",
            "todd": "Ты — Тодд Чавез, наивный друг Боджека. Оптимистичен, часто говоришь невпопад. Отвечай коротко, в образе.",
            "dog": "Ты — Мистер Подхвост, добродушный и верный друг. Позитивен. Отвечай коротко, в образе.",
        }
        persona = npc_descriptions.get(npc, f"Ты — персонаж по имени {npc}.")
        system = f"{case_context}\n\n{persona}" if case_context else persona
        try:
            client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            result = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": topic}
                ],
                temperature=0.7,
                max_tokens=250
            )
            return result.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Fallback LLM also failed: {e}")
            return f"({npc} молчит и смотрит в сторону.)"

    def handle_move(self, params: Dict, game_session) -> Dict:
        """Обработать движение между локациями"""
        target_location = params.get("location", "").lower().strip()

        # Найти локацию (нечёткий поиск)
        # Русские названия → ключи
        ru_to_key = {
            "гостиная": "living_room", "гостиную": "living_room",
            "офис": "office", "офиса": "office",
            "кухня": "kitchen", "кухню": "kitchen", "кухне": "kitchen",
            "холл": "lobby", "холла": "lobby",
        }
        target_location = ru_to_key.get(target_location, target_location)

        matching_locations = [loc for loc in self.locations.keys()
                              if target_location in loc or loc in target_location]

        if not matching_locations:
            available = "гостиная, офис, кухня, холл"
            return {
                "success": False,
                "message": f"Локация «{target_location}» не найдена. Доступные: {available}",
                "game_state": self._serialize_game_state(game_session)
            }

        location = matching_locations[0]
        current = game_session.current_location

        if location not in self.locations[current].get("connections", []):
            return {
                "success": False,
                "message": f"Отсюда нельзя попасть туда напрямую.",
                "game_state": self._serialize_game_state(game_session)
            }

        game_session.current_location = location
        if location not in game_session.visited_locations:
            game_session.visited_locations.append(location)
            game_session.experience += 10

        loc_data = self.locations[location]
        npcs_str = ", ".join(loc_data.get("npcs", [])) or "никого"
        items_str = ", ".join(loc_data.get("items", [])) or "ничего"

        message = f"{loc_data.get('description', '')}\n\nЗдесь: {npcs_str}\nПредметы: {items_str}"

        return {
            "success": True,
            "message": message,
            "game_state": self._serialize_game_state(game_session)
        }

    def handle_take(self, params: Dict, game_session) -> Dict:
        """Взять предмет"""
        item = params.get("item", "").lower().strip()
        current_location = game_session.current_location
        location_items = self.locations[current_location]["items"]

        # Найти предмет
        matching_items = [it for it in location_items if item in it or it in item]

        if not matching_items:
            return {
                "success": False,
                "message": f"Item '{item}' not found here",
                "game_state": self._serialize_game_state(game_session)
            }

        found_item = matching_items[0]

        # Добавить в инвентарь
        game_session.inventory["items"].append(found_item)
        game_session.experience += 5

        # Удалить из локации
        self.locations[current_location]["items"].remove(found_item)

        return {
            "success": True,
            "message": f"You took the {found_item}",
            "game_state": self._serialize_game_state(game_session)
        }

    def handle_drop(self, params: Dict, game_session) -> Dict:
        """Бросить предмет"""
        item = params.get("item", "").lower().strip()
        inventory = game_session.inventory["items"]

        matching_items = [it for it in inventory if item in it or it in item]

        if not matching_items:
            return {
                "success": False,
                "message": f"You don't have '{item}'",
                "game_state": self._serialize_game_state(game_session)
            }

        found_item = matching_items[0]
        inventory.remove(found_item)
        self.locations[game_session.current_location]["items"].append(found_item)

        return {
            "success": True,
            "message": f"You dropped the {found_item}",
            "game_state": self._serialize_game_state(game_session)
        }

    def handle_inventory(self, game_session) -> Dict:
        """Показать инвентарь"""
        items = game_session.inventory["items"]
        items_str = ", ".join(items) if items else "empty"

        message = f"Inventory: {items_str}\nHealth: {game_session.health}/100\nExperience: {game_session.experience}"

        return {
            "success": True,
            "message": message,
            "game_state": self._serialize_game_state(game_session)
        }

    def handle_status(self, game_session) -> Dict:
        """Показать статус"""
        message = f"""
=== STATUS ===
Location: {game_session.current_location}
Health: {game_session.health}/100
Experience: {game_session.experience}
Inventory: {', '.join(game_session.inventory['items']) or 'empty'}
        """.strip()

        return {
            "success": True,
            "message": message,
            "game_state": self._serialize_game_state(game_session)
        }

    def handle_examine(self, params: Dict, game_session) -> Dict:
        """Экзаменировать предмет или NPC"""
        target = params.get("target", "").lower().strip()

        # Посмотреть в инвентаре
        inventory = game_session.inventory["items"]
        matching_items = [it for it in inventory if target in it or it in target]

        if matching_items:
            item = matching_items[0]
            item_data = self.items.get(item, {})
            description = item_data.get("description", f"It's a {item}")
            return {
                "success": True,
                "message": description,
                "game_state": self._serialize_game_state(game_session)
            }

        return {
            "success": False,
            "message": f"Cannot examine '{target}'",
            "game_state": self._serialize_game_state(game_session)
        }

    def handle_help(self) -> Dict:
        """Показать справку"""
        help_text = """
=== COMMANDS ===
Dialogue:
  - talk to <npc> about <topic>
  - ask <npc> <question>

Movement:
  - go to <location>
  - move to <location>

Items:
  - take <item>
  - drop <item>
  - inventory / inv

Status:
  - status / health / stats
  - examine <item>

Help:
  - help / commands
        """.strip()

        return {
            "success": True,
            "message": help_text
        }

    def _serialize_game_state(self, game_session) -> Dict:
        """Сериализовать состояние игры"""
        return {
            "location": game_session.current_location,
            "health": game_session.health,
            "experience": game_session.experience,
            "inventory": game_session.inventory,
            "visited_locations": game_session.visited_locations,
            "npc_relationships": game_session.npc_relationships
        }