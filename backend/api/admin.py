# backend/api/admin.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database import get_db
from schemas import AdvertiserCreate, AdvertiserCreateResponse
from crud import users as crud_users
from models import User
from auth import RoleChecker

# Dependency to check for 'admin' role
allow_admin_only = RoleChecker(['admin'])

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(allow_admin_only)],
    responses={403: {"description": "Operation not permitted"}},
)

@router.post("/create-advertiser", response_model=AdvertiserCreateResponse, status_code=status.HTTP_201_CREATED)
def create_advertiser_account(
    advertiser_data: AdvertiserCreate,
    db: Session = Depends(get_db)
):
    """
    Creates an advertiser account. This is an admin-only operation.
    The request body should contain all the necessary user info plus
    the company name.
    """
    try:
        advertiser = crud_users.create_advertiser(db=db, advertiser_data=advertiser_data)
        return advertiser
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Public key is already registered to another user."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}"
        )
