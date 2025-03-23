from fastapi import APIRouter, HTTPException
from app.database import supabase
from app.schemas import UserRegister, UserResponse
from passlib.context import CryptContext
from uuid import uuid4
from app.utils.auth_utils import hash_password, verify_password

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

@router.post("/register", response_model=UserResponse)
def register_user(user: UserRegister):

    try:
        print("🔹 Incoming user payload:", user.dict())

        # Cek apakah email sudah ada
        response = supabase.table("users").select("email").eq("email", user.email).execute()
        print("🔹 Email check response:", response)
        if response.data:
            raise HTTPException(status_code=400, detail="Email sudah terdaftar")

        # Hash password
        hashed_password = hash_password(user.password)
        print("🔹 Password hashed")

        new_user = {
            "name": user.name,
            "email": user.email,
            "password": hashed_password,
            "phone_number": user.phone_number,
            "address": user.address,
            "city": user.city,
            "province": user.province,
            "role": user.role,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "nik": user.nik,
            "birth_date": str(user.birth_date) if user.birth_date else None,
            "jenis_kelamin": user.jenis_kelamin or None,
            "golongan_darah": user.golongan_darah or None,
            "rhesus": user.rhesus or None,
            "riwayat_result": user.riwayat_result if isinstance(user.riwayat_result, bool) else None,
            "total_points": 0
        }

        print("🔹 New user payload to Supabase:", new_user)

        response = supabase.table("users").insert(new_user).execute()
        print("🔹 Insert response:", response)

        if hasattr(response, 'error') and response.error:
            raise HTTPException(status_code=500, detail="Gagal menyimpan user")

        return UserResponse(
            name=new_user["name"],
            email=new_user["email"],
            phone_number=new_user["phone_number"],
            address=new_user["address"],
            city=new_user["city"],
            province=new_user["province"],
            role=new_user["role"]
        )
    except Exception as e:
        print("❌ INTERNAL SERVER ERROR:", str(e))
        raise HTTPException(status_code=500, detail=f"Terjadi kesalahan server: {str(e)}")


from fastapi import Request

@router.get("/me")
def get_current_user(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    session = supabase.table("sessions").select("user_id").eq("session_id", session_id).execute()
    if not session.data:
        raise HTTPException(status_code=401, detail="Invalid session")

    user_id = session.data[0]["user_id"]
    user = supabase.table("users").select("name, role").eq("iduser", user_id).execute()

    if not user.data:
        raise HTTPException(status_code=404, detail="User not found")

    return user.data[0]

@router.get("/test-hash")
def test_hash():
    from passlib.hash import bcrypt
    pw = "cobacoba123"
    hashed = bcrypt.hash(pw)
    return {
        "password": pw,
        "hashed": hashed,
        "valid": bcrypt.verify(pw, hashed)
    }
