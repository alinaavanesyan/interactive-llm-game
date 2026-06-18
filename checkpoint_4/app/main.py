from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx
from app.api.auth import get_current_user
from app.api.auth import SECRET_KEY, ALGORITHM
from jose import jwt
from pathlib import Path
from app.api import forward, history, stats, auth, game
from app.db.session import get_db
from app.db.models import RequestHistory

def _run_db_migrations():
    """Добавить новые колонки в game_sessions если их нет (SQLite не поддерживает ALTER через create_all)"""
    import sqlite3, os
    db_path = os.path.join(os.path.dirname(__file__), "app.db")
    if not os.path.exists(db_path):
        return
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cols = {row[1] for row in cur.execute("PRAGMA table_info(game_sessions)")}
    if "case_id" not in cols:
        cur.execute("ALTER TABLE game_sessions ADD COLUMN case_id INTEGER")
    if "chat_histories" not in cols:
        cur.execute("ALTER TABLE game_sessions ADD COLUMN chat_histories TEXT DEFAULT '{}'")
    if "solved" not in cols:
        cur.execute("ALTER TABLE game_sessions ADD COLUMN solved INTEGER DEFAULT 0")
    if "solved_at" not in cols:
        cur.execute("ALTER TABLE game_sessions ADD COLUMN solved_at TEXT")
    if "attempts" not in cols:
        cur.execute("ALTER TABLE game_sessions ADD COLUMN attempts INTEGER DEFAULT 0")
    if "hints_used" not in cols:
        cur.execute("ALTER TABLE game_sessions ADD COLUMN hints_used INTEGER DEFAULT 0")
    # request_history — новые колонки
    rh_cols = {row[1] for row in cur.execute("PRAGMA table_info(request_history)")}
    if "retrieved_chunks" not in rh_cols:
        cur.execute("ALTER TABLE request_history ADD COLUMN retrieved_chunks TEXT")
    if "retrieval_method" not in rh_cols:
        cur.execute("ALTER TABLE request_history ADD COLUMN retrieval_method TEXT DEFAULT 'hybrid'")
    if "retrieval_metrics" not in rh_cols:
        cur.execute("ALTER TABLE request_history ADD COLUMN retrieval_metrics TEXT")
    con.commit()
    con.close()

_run_db_migrations()

app = FastAPI(title="BoJack Interactive Game")

@app.on_event("startup")
async def warmup():
    import asyncio, logging
    async def _load():
        try:
            from app.ml.optimized_rag_pipeline import get_rag_pipeline
            get_rag_pipeline()
            logging.getLogger(__name__).info("RAG pipeline warmed up")
        except Exception as e:
            logging.getLogger(__name__).warning(f"Warmup failed: {e}")
    asyncio.create_task(_load())

app.include_router(auth.router)
app.include_router(forward.router)
app.include_router(history.router)
app.include_router(stats.router)
app.include_router(game.router)  # NEW: Game API endpoints

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

CHARACTERS = ["БОДЖЕК", "КЭРОЛИН", "ТОДД", "ДИАНА", "МИСТЕР ПОДХВОСТ"]

CHARACTER_BACKGROUNDS = {
    "bojack": "locations/background_bojack.jpg",
    "caroline": "locations/background_caroline.png",
    "todd": "locations/background_todd.png",
    "diane": "locations/background_diane.png",
    "dog": "locations/background_dog.png"
}


CHARACTER_MAP = {
    "БОДЖЕК": "bojack",
    "КЭРОЛИН": "caroline",
    "ТОДД": "todd",
    "ДИАНА": "diane",
    "МИСТЕР ПОДХВОСТ": "dog"
}

chat_history = {character: [] for character in CHARACTER_MAP.values()}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, user: dict = Depends(get_current_user)):
    if not user:
        return RedirectResponse(url="/login")

    return templates.TemplateResponse(
        request=request,
        name="game.html",
        context={"user": user}
    )

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html", context={})

@app.post("/login", response_class=RedirectResponse)
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    from app.api.auth import ADMIN_DATA, USERS_DATA, create_access_token

    if email == ADMIN_DATA["email"] and password == ADMIN_DATA["password"]:
        user_data = ADMIN_DATA
    elif email in USERS_DATA and USERS_DATA[email]["password"] == password:
        user_data = USERS_DATA[email]
        user_data["email"] = email
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(
        {
            "user_id": user_data["user_id"],
            "email": email,
            "role": user_data["role"]
        }
    )

    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(key="access_token", value=token, httponly=True)
    return response

@app.get("/select_character/{character}")
async def select_character(request: Request, character: str, user: dict = Depends(get_current_user)):
    if character not in CHARACTER_MAP:
        raise HTTPException(status_code=400, detail="Invalid character")

    character_latin = CHARACTER_MAP[character]

    return templates.TemplateResponse(
        request=request,
        name="chat.html",
        context={
            "characters": CHARACTERS,
            "selected_character": character_latin,
            "backgrounds": CHARACTER_BACKGROUNDS,
            "chat": chat_history[character_latin],
            "user_role": user.get("role")
        })


@app.post("/chat", response_class=HTMLResponse)
async def chat(request: Request, character: str = Form(...), message: str = Form(...), user: dict = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if character not in CHARACTER_MAP.values():
        raise HTTPException(status_code=400, detail="Invalid character")

    import time
    start_time = time.time()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://127.0.0.1:8000/forward",
            json={"question": message, "character": character}
        )
        if response.status_code != 200:
            answer = f"Ошибка API: {response.text}"
        else:
            answer = response.json().get("answer", "Нет ответа")

    chat_history[character].append({"user": message, "bot": answer})

    return templates.TemplateResponse(
        request=request,
        name="chat.html",
        context={
            "characters": CHARACTERS,
            "selected_character": character,
            "backgrounds": CHARACTER_BACKGROUNDS,
            "chat": chat_history[character],
            "user_role": user.get("role")
        })

# Страница выхода
@app.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/")
    response.delete_cookie("access_token")
    return response

@app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request, user: dict = Depends(get_current_user)):
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(request=request, name="profile.html", context={"user": user})

@app.get("/admin/history", response_class=HTMLResponse)
async def admin_history(request: Request, user: dict = Depends(get_current_user)):
    if not user or user.get("role") != "admin":
        return RedirectResponse(url="/login")

    return templates.TemplateResponse(request=request, name="admin_history.html", context={})


@app.get("/admin/stats", response_class=HTMLResponse)
async def admin_stats(request: Request, user: dict = Depends(get_current_user)):
    if not user or user.get("role") != "admin":
        return RedirectResponse(url="/login")

    return templates.TemplateResponse(request=request, name="admin_stats.html", context={})

@app.delete("/api/clear-chat-memory")
async def clear_chat_memory(user: dict = Depends(get_current_user)):
    """Очистить чаты в памяти (вызывается после удаления БД)"""
    global chat_history
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not enough privileges")

    chat_history = {character: [] for character in CHARACTER_MAP.values()}
    return {"status": "chat_memory_cleared"}
