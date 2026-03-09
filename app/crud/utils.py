from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

def generate_custom_id(db:Session,model,prefix:str)->str:
    current_year=datetime.now().year
    base_prefix=f"{current_year}{prefix}"
    last_record=db.query(model.id).filter(model.id.like(f"{base_prefix}%")).order_by(model.id.desc()).first()
    if last_record:
        last_seq=int(last_record[0][-4:])
        new_seq=last_seq+1
    else:
        new_seq=1
    return f"{base_prefix}{new_seq:04d}"