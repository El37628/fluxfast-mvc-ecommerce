from pydantic import BaseModel, EmailStr


class CustomerItem(BaseModel):
    id: int
    email: EmailStr
    name: str
    tier: str
