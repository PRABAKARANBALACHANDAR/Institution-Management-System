from pydantic import BaseModel
from datetime import date,datetime
from typing import Optional
from uuid import UUID

class RevenueReportItem(BaseModel):
    transaction_type:str
    entity_name:str
    role:str
    amount:float
    month:int
    year:int
    is_paid:bool
    paid_date:Optional[date]=None
    class Config:
        from_attributes=True

class RevenueReportSummary(BaseModel):
    month:int
    year:int
    total_fees_collected:float
    total_salary_paid:float
    net_revenue:float
