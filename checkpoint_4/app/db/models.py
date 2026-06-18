from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    game_sessions = relationship("GameSession", back_populates="user")

class GameSession(Base):
    """Сессия игры пользователя"""
    __tablename__ = "game_sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    current_location = Column(String, default="living_room")
    health = Column(Integer, default=100)
    experience = Column(Integer, default=0)
    inventory = Column(JSON, default={"items": [], "keys": []})
    completed_tasks = Column(JSON, default={})
    visited_locations = Column(JSON, default=[])
    npc_relationships = Column(JSON, default={})  # "bojack": {"mood": "neutral", "trust": 50}
    case_id = Column(Integer, nullable=True)
    chat_histories = Column(JSON, default={})  # {"bojack": [{role, content}, ...], ...}
    solved = Column(Boolean, default=False)
    solved_at = Column(DateTime, nullable=True)
    attempts = Column(Integer, default=0)
    hints_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="game_sessions")
    game_events = relationship("GameEvent", back_populates="session")

class GameEvent(Base):
    """Логирование событий в игре"""
    __tablename__ = "game_events"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("game_sessions.id"), nullable=False)
    event_type = Column(String)  # "dialogue", "move", "take_item", "combat", "quest"
    character = Column(String, nullable=True)
    action = Column(String)
    result = Column(String)
    game_state_before = Column(JSON, nullable=True)
    game_state_after = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    session = relationship("GameSession", back_populates="game_events")

class RequestHistory(Base):
    """История RAG-запросов (для логирования и метрик)"""
    __tablename__ = "request_history"

    id = Column(Integer, primary_key=True)
    question = Column(String, nullable=False)
    character = Column(String, nullable=False)
    answer = Column(String, nullable=True)
    retrieved_chunks = Column(JSON, nullable=True)  # Какие чанки нашлись
    latency_ms = Column(Integer, nullable=False)
    retrieval_method = Column(String, default="hybrid")  # "semantic", "hybrid", "hybrid+ce"
    retrieval_metrics = Column(JSON, nullable=True)  # {"top_1": 0.432, "retr_sim": 0.646}
    created_at = Column(DateTime, default=datetime.utcnow)