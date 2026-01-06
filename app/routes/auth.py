from fastapi import APIRouter, HTTPException, Depends
from app.models import UserSignup, UserLogin
from app.database import get_supabase
from supabase import Client

router = APIRouter()

@router.post("/signup")
async def signup(user: UserSignup, supabase: Client = Depends(get_supabase)):
    try:
        response = supabase.auth.sign_up({
            "email": user.email,
            "password": user.password
        })
        return {
            "message": "User created successfully",
            "user_id": response.user.id if response.user else None
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
async def login(user: UserLogin, supabase: Client = Depends(get_supabase)):
    try:
        response = supabase.auth.sign_in_with_password({
            "email": user.email,
            "password": user.password
        })
        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "user": {
                "id": response.user.id,
                "email": response.user.email
            }
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@router.post("/logout")
async def logout(supabase: Client = Depends(get_supabase)):
    try:
        supabase.auth.sign_out()
        return {"message": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
