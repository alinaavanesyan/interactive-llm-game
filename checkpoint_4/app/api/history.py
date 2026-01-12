from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.models import RequestHistory
from app.db.session import get_db
from app.api.auth import get_current_admin


router = APIRouter(prefix="/api/history", tags=["history"])

@router.get("")
def get_history(
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Получить всю историю (только для админа)"""
    records = db.query(RequestHistory).all()
    return [
        {
            "id": r.id,
            "question": r.question,
            "answer": r.answer,
            "character": r.character,
            "latency_ms": r.latency_ms,
            "created_at": r.created_at.isoformat() if r.created_at else None
        }
        for r in records
    ]


@router.delete("")
def clear_history(
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Удалить всю историю (только для админа)"""
    count = db.query(RequestHistory).delete()
    db.commit()
    return {"status": "deleted", "rows_deleted": count}

# @router.delete("/history")
# def clear_history(db: Session = Depends(get_db), current_admin=Depends(get_current_admin)):
#     db.query(RequestHistory).delete()
#     db.commit()
#     return {"status": "deleted"}
