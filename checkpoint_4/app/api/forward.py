from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.ml.rag_pipeline import rag_forward
from app.db.session import get_db
from app.db.models import RequestHistory
import time

router = APIRouter()

@router.post("/forward")
def forward(data: dict, db: Session = Depends(get_db)):
    if "question" not in data or "character" not in data:
        raise HTTPException(status_code=400, detail="bad request")

    start = time.time()

    try:
        answer, chunks = rag_forward(
            data["question"],
            data["character"]
        )
    except Exception:
        raise HTTPException(
            status_code=403,
            detail="модель не смогла обработать данные"
        )

    latency_ms = int((time.time() - start) * 1000)

    # Сохраняем запрос и ответ в базу данных
    request_history = RequestHistory(
        question=data["question"],
        character=data["character"],
        answer=answer,
        latency_ms=latency_ms
    )
    db.add(request_history)
    db.commit()

    return {
        "answer": answer,
        "character": data["character"],
        "retrieved_chunks": chunks,
        "latency_ms": latency_ms
    }
