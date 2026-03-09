from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

class IMSException(HTTPException):
    pass

class NotFoundError(IMSException):
    def __init__(self, resource: str, id: str):
        super().__init__(status_code=404, detail=f"{resource} with id '{id}' not found")

class DuplicateError(IMSException):
    def __init__(self, resource: str, field: str):
        super().__init__(status_code=409, detail=f"{resource} with this {field} already exists")

class PermissionDeniedError(IMSException):
    def __init__(self):
        super().__init__(status_code=403, detail="Operation not permitted")

class AttendanceAlreadyMarkedError(IMSException):
    def __init__(self, entity_id: str, date: str):
        super().__init__(status_code=409,detail=f"Attendance for '{entity_id}' on {date} already marked")