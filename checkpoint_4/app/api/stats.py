from app.api.auth import get_current_admin
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import numpy as np

from app.db.models import RequestHistory
from app.db.session import get_db

router = APIRouter()

@router.get("/stats")
def stats(
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    records = db.query(RequestHistory).all()

    if not records:
        return {"message": "no data"}

    latencies = np.array([r.latency_ms for r in records])
    questions = [r.question for r in records]
    question_lengths = np.array([len(q) for q in questions])
    question_tokens = np.array([len(q.split()) for q in questions])

    return {
        "latency_ms": {
            "mean": float(latencies.mean()),
            "p50": float(np.percentile(latencies, 50)),
            "p95": float(np.percentile(latencies, 95)),
            "p99": float(np.percentile(latencies, 99)),
            "min": float(latencies.min()),
            "max": float(latencies.max()),
        },
        "input_stats": {
            "avg_question_length": float(question_lengths.mean()),
            "avg_question_tokens": float(question_tokens.mean()),
            "min_length": int(question_lengths.min()),
            "max_length": int(question_lengths.max()),
            "min_tokens": int(question_tokens.min()),
            "max_tokens": int(question_tokens.max())
        }
    }
