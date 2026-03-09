from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from auth.dependencies import RequirePermission
from pydantic import BaseModel, Field
from crud.permissions_ops import update_permissions

router = APIRouter()

class PermUpdate(BaseModel):
    permissions:dict[str,bool]=Field(default_factory=dict)

@router.put("/{username}")
def update_perm(username: str, data: PermUpdate, db: Session = Depends(get_db),
                user=Depends(RequirePermission("post_principal"))):
    """
    ID FORMAT REFERENCE: D1001, C1001, F1001, S10001
    """
    return update_permissions(db, username, data.model_dump())

