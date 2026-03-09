from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth.dependencies import RequirePermission,get_current_user
from pydantic import BaseModel
from typing import List,Optional
from datetime import date,datetime
from crud.announcements_ops import (create_announcement,get_all_announcements,get_announcement,update_announcement,delete_announcement)


router=APIRouter()

class AnnouncementCreate(BaseModel):
    title:str
    content:str
    deadline:Optional[date]=None
    status:str="Active"

class AnnouncementResponse(BaseModel):
    id:str
    title:str
    content:str
    deadline:Optional[date]=None
    status:str
    posted_by:Optional[str]=None
    created_at:datetime
    class Config:
        from_attributes=True

@router.post("/",response_model=AnnouncementResponse)
def create_ann(data:AnnouncementCreate,db:Session=Depends(get_db),
               user=Depends(RequirePermission("post_announcements"))):
    payload=data.model_dump()
    payload["posted_by"]=user.username
    return create_announcement(db,payload)

@router.get("/",response_model=List[AnnouncementResponse])
def list_ann(db:Session=Depends(get_db),user=Depends(get_current_user)):
    return get_all_announcements(db)

@router.get("/{ann_id}",response_model=AnnouncementResponse)
def get_ann(ann_id:str,db:Session=Depends(get_db),user=Depends(get_current_user)):
    a=get_announcement(db,ann_id)
    if not a:
        raise HTTPException(status_code=404,detail="Announcement not found")
    return a

@router.put("/{ann_id}",response_model=AnnouncementResponse)
def update_ann(ann_id:str,data:AnnouncementCreate,db:Session=Depends(get_db),
               user=Depends(RequirePermission("put_announcements"))):
    return update_announcement(db,ann_id,data.model_dump())

@router.delete("/{ann_id}")
def delete_ann(ann_id:str,db:Session=Depends(get_db),
               user=Depends(RequirePermission("delete_announcements"))):
    if not delete_announcement(db,ann_id):
        raise HTTPException(status_code=404,detail="Announcement not found")
    return{"detail":"Deleted"}