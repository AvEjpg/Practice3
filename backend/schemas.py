from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime

# ---------- Requests ----------
class RequestBase(BaseModel):
    start_date: date
    tech_type: str
    tech_model: str
    problem_description: str
    request_status: str
    completion_date: Optional[date] = None
    repair_parts: Optional[str] = None
    deadline_date: Optional[date] = None
    priority: Optional[str] = "Нормальный"
    master_id: Optional[int] = None
    client_id: Optional[int] = None  

class RequestCreate(RequestBase):
    pass

class RequestUpdate(BaseModel):
    request_status: Optional[str] = None
    completion_date: Optional[date] = None
    repair_parts: Optional[str] = None
    deadline_date: Optional[date] = None
    priority: Optional[str] = None
    master_id: Optional[int] = None
    client_id: Optional[int] = None

class RequestOut(RequestBase):
    request_id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ---------- Users ----------
class UserBase(BaseModel):
    fio: str
    phone: str
    login: str
    password: str
    user_type: str

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    fio: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    user_type: Optional[str] = None

class UserOut(BaseModel):
    user_id: int
    fio: str
    phone: str
    login: str
    user_type: str
    created_at: Optional[datetime] = None
    is_active: Optional[bool] = True

    class Config:
        from_attributes = True

# ---------- Comments ----------
class CommentBase(BaseModel):
    message: str
    master_id: int
    request_id: int

class CommentCreate(CommentBase):
    pass

class CommentOut(CommentBase):
    comment_id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ---------- Auth ----------
class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: Optional[int] = None

    class Config:
        from_attributes = True

class LoginIn(BaseModel):
    login: str
    password: str

# ---------- Client Requests ----------
class ClientRequestCreate(BaseModel):
    start_date: date
    tech_type: str
    tech_model: str
    problem_description: str
    priority: Optional[str] = "Нормальный"  

class ClientRequestOut(BaseModel):
    request_id: int
    start_date: date
    tech_type: str
    tech_model: str
    problem_description: str
    request_status: str
    completion_date: Optional[date] = None
    repair_parts: Optional[str] = None
    deadline_date: Optional[date] = None
    priority: Optional[str] = None
    master_id: Optional[int] = None
    client_id: Optional[int] = None  
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ---------- Extra ----------
class AssignMasterIn(BaseModel):
    master_id: int

class ExtendDeadlineIn(BaseModel):
    new_deadline_date: date
    reason: Optional[str] = None