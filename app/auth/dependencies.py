from fastapi import Request,HTTPException,Depends
from sqlalchemy.orm import Session
import jwt
import os
from database import get_db
from schemas.permissions import MYSQL_Permissions
from dotenv import load_dotenv

env_path=os.path.join(os.path.dirname(__file__),"..",".env")
load_dotenv(env_path)

SECRET_KEY=os.getenv("SECRET_KEY")
ALGORITHM=os.getenv("ALGORITHM")

def get_current_user(request:Request,db:Session=Depends(get_db)):
    token=request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    if not token:
        raise HTTPException(status_code=401,detail="Not authenticated")
    try:
        payload=jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        username=payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401,detail="Invalid token")
        user_perm=db.query(MYSQL_Permissions).filter(MYSQL_Permissions.username==username).first()
        if not user_perm:
            raise HTTPException(status_code=401,detail="User not found")
        return user_perm
    except jwt.PyJWTError:
        raise HTTPException(status_code=401,detail="Token expired/invalid")
    
class RequirePermission:
    def __init__(self,permission_name:str):
        self.permission_name=permission_name
    def __call__(self,user:MYSQL_Permissions=Depends(get_current_user)):
        has_perm=getattr(user,self.permission_name,0)
        if has_perm!=1:
            raise HTTPException(status_code=403,detail="Operation not permitted")
        return user
