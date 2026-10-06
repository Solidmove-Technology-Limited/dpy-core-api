from fastapi import APIRouter, Depends
from app.models import User
from app.schemas import UserResponse
from app.dep import get_current_user

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information"""
    return UserResponse.from_orm(current_user)
