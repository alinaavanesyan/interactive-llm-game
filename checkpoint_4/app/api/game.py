"""
Game API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import GameSession, GameEvent, RequestHistory, User
from app.game.engine import GameEngine
from app.game.history_agent import HistoryAgent
from app.api.auth import get_current_user
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/game", tags=["game"])

@router.post("/session/start")
def start_game_session(request_body: dict = None, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """
    Начать или продолжить сессию для конкретного дела.
    Если сессия для этого case_id уже существует — возвращает её с историей чатов.
    """
    try:
        case_id = (request_body or {}).get("case_id")

        # Поискать существующую активную сессию для этого дела
        existing = None
        if case_id:
            existing = db.query(GameSession).filter(
                GameSession.user_id == user["user_id"],
                GameSession.case_id == case_id,
                GameSession.is_active == True
            ).first()

        if existing:
            return {
                "success": True,
                "session_id": existing.id,
                "resumed": True,
                "chat_histories": existing.chat_histories or {},
                "game_state": {
                    "location": existing.current_location,
                    "health": existing.health,
                    "experience": existing.experience,
                    "inventory": existing.inventory,
                    "visited_locations": existing.visited_locations
                }
            }

        # Деактивировать другие сессии этого дела (если есть)
        if case_id:
            db.query(GameSession).filter(
                GameSession.user_id == user["user_id"],
                GameSession.case_id == case_id
            ).update({"is_active": False})

        new_session = GameSession(
            user_id=user["user_id"],
            case_id=case_id,
            current_location="living_room",
            health=100,
            experience=0,
            inventory={"items": [], "keys": []},
            chat_histories={},
            npc_relationships={
                "bojack": {"trust": 50, "mood": "neutral"},
                "caroline": {"trust": 50, "mood": "neutral"},
                "todd": {"trust": 50, "mood": "neutral"},
                "diane": {"trust": 50, "mood": "neutral"},
                "dog": {"trust": 50, "mood": "neutral"}
            }
        )

        db.add(new_session)
        db.commit()
        db.refresh(new_session)

        logger.info(f"New game session started for user {user['email']}, case_id={case_id}")

        return {
            "success": True,
            "session_id": new_session.id,
            "resumed": False,
            "chat_histories": {},
            "game_state": {
                "location": new_session.current_location,
                "health": new_session.health,
                "experience": new_session.experience,
                "inventory": new_session.inventory,
                "visited_locations": new_session.visited_locations
            }
        }
    except Exception as e:
        logger.error(f"Error starting game session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/action")
def process_game_action(
    data: dict,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Обработать действие игрока

    Body:
    {
        "session_id": int,
        "action": "talk to bojack about his depression"
    }

    Возвращает: результат действия + обновленное состояние игры
    """
    try:
        session_id = data.get("session_id")
        action = data.get("action", "").strip()
        explicit_npc = data.get("npc", "")
        explicit_location = data.get("location", "")
        case_context = data.get("case_context", "")

        if not session_id or not action:
            raise HTTPException(status_code=400, detail="Missing session_id or action")

        # Загрузить сессию
        game_session = db.query(GameSession).filter(
            GameSession.id == session_id,
            GameSession.user_id == user["user_id"]
        ).first()

        if not game_session:
            raise HTTPException(status_code=404, detail="Game session not found")

        # Инициализировать движок и агента
        engine = GameEngine()
        history_agent = HistoryAgent(game_session)

        # Достать историю чата для конкретного NPC (последние 10 сообщений = 5 пар)
        npc_chat_history = []
        if explicit_npc:
            all_histories = game_session.chat_histories or {}
            npc_chat_history = all_histories.get(explicit_npc, [])[-10:]

        # === STAGE 1: Обработать действие ===
        start_time = time.time()
        result = engine.process_action(action, game_session,
                                       explicit_npc=explicit_npc,
                                       explicit_location=explicit_location,
                                       case_context=case_context,
                                       chat_history=npc_chat_history)
        latency_ms = int((time.time() - start_time) * 1000)

        # === STAGE 1b: Обновить историю чата для NPC ===
        if explicit_npc and result.get("success") and result.get("message"):
            all_histories = dict(game_session.chat_histories or {})
            npc_history = list(all_histories.get(explicit_npc, []))
            npc_history.append({"role": "user", "content": action})
            npc_history.append({"role": "assistant", "content": result["message"]})
            all_histories[explicit_npc] = npc_history
            game_session.chat_histories = all_histories

        # === STAGE 2: Сохранить событие в историю ===
        game_event = GameEvent(
            session_id=game_session.id,
            event_type=result.get("game_state", {}).get("action_type", "unknown"),
            action=action,
            result=result.get("message", ""),
            game_state_before={
                "location": game_session.current_location,
                "health": game_session.health,
                "experience": game_session.experience,
            },
            game_state_after=result.get("game_state", {})
        )

        db.add(game_event)

        # === STAGE 3: Если это диалог, сохранить в RequestHistory для метрик ===
        if "dialogue" in action.lower() or "talk" in action.lower():
            if "metrics" in result:
                request_history = RequestHistory(
                    question=action,
                    character=result.get("game_state", {}).get("character", "unknown"),
                    answer=result.get("message", ""),
                    retrieved_chunks=result.get("retrieved_chunks", []),
                    latency_ms=latency_ms,
                    retrieval_method="hybrid_rrf_alpha=0.5_k=7",
                    retrieval_metrics={
                        "method": result.get("metrics", {}).get("retrieval_method"),
                        "llm": result.get("metrics", {}).get("llm"),
                        "reranker": result.get("metrics", {}).get("reranker")
                    }
                )
                db.add(request_history)

        # === STAGE 4: Проверить триггеры событий ===
        special_event = history_agent.should_trigger_special_event(game_session)

        # === STAGE 5: Обновить сессию ===
        db.commit()
        db.refresh(game_session)

        response = {
            "success": result.get("success", False),
            "message": result.get("message", ""),
            "game_state": result.get("game_state", {}),
            "latency_ms": latency_ms
        }

        if special_event:
            response["special_event"] = special_event

        if "metrics" in result:
            response["rag_metrics"] = result["metrics"]

        logger.info(f"Action processed: {action[:50]}... (latency: {latency_ms}ms)")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing action: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/state")
def get_game_state(session_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """
    Получить текущее состояние игры

    Query params:
    - session_id: int

    Возвращает: полное состояние игры
    """
    try:
        game_session = db.query(GameSession).filter(
            GameSession.id == session_id,
            GameSession.user_id == user["user_id"]
        ).first()

        if not game_session:
            raise HTTPException(status_code=404, detail="Game session not found")

        return {
            "session_id": game_session.id,
            "location": game_session.current_location,
            "health": game_session.health,
            "experience": game_session.experience,
            "inventory": game_session.inventory,
            "visited_locations": game_session.visited_locations,
            "npc_relationships": game_session.npc_relationships,
            "completed_tasks": game_session.completed_tasks
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting game state: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
def get_game_history(
    session_id: int,
    limit: int = 10,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Получить историю событий игры

    Query params:
    - session_id: int
    - limit: int (по умолчанию 10)

    Возвращает: последние события в игре
    """
    try:
        game_session = db.query(GameSession).filter(
            GameSession.id == session_id,
            GameSession.user_id == user["user_id"]
        ).first()

        if not game_session:
            raise HTTPException(status_code=404, detail="Game session not found")

        events = db.query(GameEvent).filter(
            GameEvent.session_id == session_id
        ).order_by(GameEvent.id.desc()).limit(limit).all()

        return {
            "session_id": session_id,
            "events": [
                {
                    "id": event.id,
                    "type": event.event_type,
                    "action": event.action,
                    "result": event.result,
                    "timestamp": event.timestamp.isoformat() if event.timestamp else None
                }
                for event in reversed(events)
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting game history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


CASE_TITLES = {
    1: "Исчезновение сценария",
    2: "Тайна пропавшей бутылки",
    3: "Анонимное письмо",
    4: "Сорванная съёмка",
}

@router.post("/solve")
def solve_case(data: dict, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    session_id = data.get("session_id")
    game_session = db.query(GameSession).filter(
        GameSession.id == session_id, GameSession.user_id == user["user_id"]
    ).first()
    if not game_session:
        raise HTTPException(status_code=404, detail="Session not found")
    if not game_session.solved:
        game_session.solved = True
        game_session.solved_at = datetime.utcnow()
        db.commit()
    return {"success": True}

@router.post("/attempt")
def log_attempt(data: dict, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    session_id = data.get("session_id")
    game_session = db.query(GameSession).filter(
        GameSession.id == session_id, GameSession.user_id == user["user_id"]
    ).first()
    if not game_session:
        raise HTTPException(status_code=404, detail="Session not found")
    game_session.attempts = (game_session.attempts or 0) + 1
    db.commit()
    return {"success": True, "attempts": game_session.attempts}

@router.post("/hint")
def log_hint(data: dict, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    session_id = data.get("session_id")
    game_session = db.query(GameSession).filter(
        GameSession.id == session_id, GameSession.user_id == user["user_id"]
    ).first()
    if not game_session:
        raise HTTPException(status_code=404, detail="Session not found")
    game_session.hints_used = True
    db.commit()
    return {"success": True}

@router.get("/profile")
def get_profile(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    sessions = db.query(GameSession).filter(
        GameSession.user_id == user["user_id"],
        GameSession.case_id != None,
    ).order_by(GameSession.created_at.desc()).all()

    cases = []
    seen_case_ids = set()
    for s in sessions:
        if s.case_id in seen_case_ids:
            continue
        seen_case_ids.add(s.case_id)
        msg_count = sum(
            len([m for m in msgs if m.get("role") == "user"])
            for msgs in (s.chat_histories or {}).values()
        )
        cases.append({
            "case_id": s.case_id,
            "title": CASE_TITLES.get(s.case_id, f"Дело №{s.case_id}"),
            "solved": s.solved or False,
            "solved_at": s.solved_at.isoformat() if s.solved_at else None,
            "attempts": s.attempts or 0,
            "hints_used": s.hints_used or False,
            "messages_sent": msg_count,
            "started_at": s.created_at.isoformat() if s.created_at else None,
        })

    solved_count = sum(1 for c in cases if c["solved"])
    return {
        "email": user.get("email", ""),
        "total_cases": len(CASE_TITLES),
        "started": len(cases),
        "solved": solved_count,
        "cases": cases,
    }

@router.post("/chat/reset")
def reset_chat_history(data: dict, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """Сбросить историю чатов для сессии (начать дело заново)"""
    try:
        session_id = data.get("session_id")
        if not session_id:
            raise HTTPException(status_code=400, detail="Missing session_id")

        game_session = db.query(GameSession).filter(
            GameSession.id == session_id,
            GameSession.user_id == user["user_id"]
        ).first()

        if not game_session:
            raise HTTPException(status_code=404, detail="Game session not found")

        game_session.chat_histories = {}
        game_session.npc_relationships = {
            "bojack": {"trust": 50, "mood": "neutral"},
            "caroline": {"trust": 50, "mood": "neutral"},
            "todd": {"trust": 50, "mood": "neutral"},
            "diane": {"trust": 50, "mood": "neutral"},
            "dog": {"trust": 50, "mood": "neutral"}
        }
        db.commit()

        logger.info(f"Chat history reset for session {session_id}")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rag-metrics")
def get_rag_metrics(session_id: int, limit: int = 10, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """
    Получить метрики RAG запросов для сессии

    Это покажет качество работы RAG pipeline на протяжении игры
    """
    try:
        # Verify session ownership
        game_session = db.query(GameSession).filter(
            GameSession.id == session_id,
            GameSession.user_id == user["user_id"]
        ).first()

        if not game_session:
            raise HTTPException(status_code=404, detail="Game session not found")

        # Get RAG request history for this session's game events
        rag_requests = db.query(RequestHistory).order_by(
            RequestHistory.created_at.desc()
        ).limit(limit).all()

        return {
            "requests": [
                {
                    "id": req.id,
                    "character": req.character,
                    "question": req.question,
                    "latency_ms": req.latency_ms,
                    "retrieval_method": req.retrieval_method,
                    "retrieval_metrics": req.retrieval_metrics,
                    "timestamp": req.created_at.isoformat() if req.created_at else None
                }
                for req in rag_requests
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting RAG metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/help")
def get_game_help():
    """
    Получить справку по командам игры
    """
    help_text = """
=== BOJACK GAME - COMMAND REFERENCE ===

DIALOGUE:
  "talk to bojack about his depression"
  "ask diane about writing"

MOVEMENT:
  "go to office"
  "move to kitchen"

ITEMS:
  "take apple"
  "drop book"
  "inventory"

STATUS:
  "health"
  "status"

HELP:
  "help"
  "commands"

AVAILABLE LOCATIONS:
  - living_room (Bojack's apartment)
  - office (Carolyn's office)
  - kitchen (The kitchen)

CHARACTERS:
  - bojack
  - caroline (Princess Carolyn)
  - todd
  - diane
  - dog (Mr. Peanutbutter)

MECHANICS:
- Talk to characters to increase trust
- Visit locations to gain experience
- Health decreases if you neglect yourself
- Some NPCs have special dialogues when trust is high
    """

    return {"help": help_text}