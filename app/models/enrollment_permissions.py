from pydantic import BaseModel, Field


class EnrollmentPermissionInput(BaseModel):
    username: str
    password: str
    permissions: dict[str, bool] = Field(default_factory=dict)

