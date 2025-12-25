from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.models import RequestHistory
from app.db.session import get_db
from app.api.auth import get_current_admin

router = APIRouter()

@router.get("/history")
def get_history(db: Session = Depends(get_db)):
    return db.query(RequestHistory).all()

# @router.delete("/history")
# def clear_history(db: Session = Depends(get_db), current_admin=Depends(get_current_admin)):
#     db.query(RequestHistory).delete()
#     db.commit()
#     return {"status": "deleted"}

@router.delete("/history")
def clear_history(
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    db.query(RequestHistory).delete()
    db.commit()
    return {"status": "deleted"}