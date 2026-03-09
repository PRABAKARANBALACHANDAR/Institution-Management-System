from fastapi import APIRouter,Depends,HTTPException,status,Response,Request
from pydantic import BaseModel
from datetime import datetime,timedelta,timezone
from sqlalchemy.orm import Session
import jwt
import os
from database import get_db
from schemas.permissions import MYSQL_Permissions
from crud.permissions_ops import verify_password
from dotenv import load_dotenv

env_path=os.path.join(os.path.dirname(__file__),"..",".env")
load_dotenv(env_path)

router=APIRouter(tags=["Auth"]) 
SECRET_KEY=os.getenv("SECRET_KEY")
ALGORITHM=os.getenv("ALGORITHM")
JWT_EXPIRE_MINUTES=os.getenv("JWT_EXPIRE_MINUTES")

ADMIN_USERNAME=os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD=os.getenv("ADMIN_PASSWORD")

class LoginRequest(BaseModel):
    username:str
    password:str

@router.post("/IMS/login")
def login(login_data:LoginRequest,response:Response,db:Session=Depends(get_db)):
    user_perm=db.query(MYSQL_Permissions).filter(MYSQL_Permissions.username==login_data.username).first()
    if login_data.username==ADMIN_USERNAME and login_data.password==ADMIN_PASSWORD:
        role="admin"
        expire=datetime.now(timezone.utc)+timedelta(minutes=int(JWT_EXPIRE_MINUTES))
        token=jwt.encode({"sub":login_data.username,"exp":int(expire.timestamp()),"role":role},SECRET_KEY,algorithm=ALGORITHM)
        response.set_cookie(key="access_token",value=token,httponly=True,samesite="lax",secure=False)
        return {"message":"Login successful"}
    if not user_perm or not verify_password(login_data.password, user_perm.password):
        raise HTTPException(status_code=401,detail="Invalid credentials")
    expire=datetime.now(timezone.utc)+timedelta(minutes=int(JWT_EXPIRE_MINUTES))
    token=jwt.encode({"sub":login_data.username,"exp":int(expire.timestamp()),"role":user_perm.role},SECRET_KEY,algorithm=ALGORITHM)
    response.set_cookie(key="access_token",value=token,httponly=True,samesite="lax",secure=False)
    return {"message":"Login successful"}
