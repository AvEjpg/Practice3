from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "service_center"}

    user_id = Column(Integer, primary_key=True, index=True)
    fio = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    login = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    user_type = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

    requests = relationship("Request", back_populates="client", foreign_keys="Request.client_id")
    comments = relationship("Comment", back_populates="master")

class Request(Base):
    __tablename__ = "requests"
    __table_args__ = {"schema": "service_center"}

    request_id = Column(Integer, primary_key=True, index=True, autoincrement=True) 
    start_date = Column(Date, nullable=False)
    tech_type = Column(String(100), nullable=False)
    tech_model = Column(String(255), nullable=False)
    problem_description = Column(Text, nullable=False)
    request_status = Column(String(50), nullable=False, default="Новая заявка")
    completion_date = Column(Date, nullable=True)
    repair_parts = Column(Text, nullable=True)
    deadline_date = Column(Date, nullable=True)
    priority = Column(String(20), default="Нормальный")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    master_id = Column(Integer, ForeignKey("service_center.users.user_id", ondelete="SET NULL"), nullable=True)
    client_id = Column(Integer, ForeignKey("service_center.users.user_id", ondelete="SET NULL"), nullable=True)

    client = relationship("User", foreign_keys=[client_id], back_populates="requests")
    master = relationship("User", foreign_keys=[master_id])
    comments = relationship("Comment", back_populates="request")

class Comment(Base):
    __tablename__ = "comments"
    __table_args__ = {"schema": "service_center"}

    comment_id = Column(Integer, primary_key=True, index=True)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    master_id = Column(Integer, ForeignKey("service_center.users.user_id", ondelete="CASCADE"))
    request_id = Column(Integer, ForeignKey("service_center.requests.request_id", ondelete="CASCADE"))

    master = relationship("User", back_populates="comments")
    request = relationship("Request", back_populates="comments")