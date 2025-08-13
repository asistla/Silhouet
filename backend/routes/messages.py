from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from workers.message_queue import pop_message_for_user

router = APIRouter(prefix="/messages", tags=["Messages"])

@router.get("/next")
def get_next_message(
    user_id: str = Query(..., description="UUID of the user requesting the next message"),
    db: Session = Depends(get_db)
):
    """
    Pops the next message from the per-user Redis queue and returns it.
    - user_id: Required, must be a valid UUID string.
    """
    try:
        msg = pop_message_for_user(user_id)
        return {"message": msg}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
