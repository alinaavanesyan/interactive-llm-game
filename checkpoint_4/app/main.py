from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import httpx

from app.api import forward, history, stats, auth

app = FastAPI(title="BoJack RAG Service")

app.include_router(auth.router)
app.include_router(forward.router)
app.include_router(history.router)
app.include_router(stats.router)

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

CHARACTERS = ["BOJACK", "CAROLYN", "TODD", "DIANE"]

chat_history = {char: [] for char in CHARACTERS}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "chat.html",
        {"request": request, "characters": CHARACTERS, "chat": [], "selected_character": ""}
    )

@app.get("/select_character/{character}", response_class=HTMLResponse)
async def select_character(request: Request, character: str):
    if character not in CHARACTERS:
        raise HTTPException(status_code=400, detail="Invalid character")
    return templates.TemplateResponse(
        "chat.html",
        {"request": request, "characters": CHARACTERS, "chat": chat_history[character], "selected_character": character}
    )

@app.post("/chat", response_class=HTMLResponse)
async def chat(request: Request, character: str = Form(...), message: str = Form(...)):
    if character not in CHARACTERS:
        raise HTTPException(status_code=400, detail="Invalid character")

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
        "chat.html",
        {"request": request, "characters": CHARACTERS, "chat": chat_history[character], "selected_character": character}
    )
