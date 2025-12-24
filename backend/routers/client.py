from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List
from datetime import date
from .. import models, schemas, database
from ..auth import get_current_user

router = APIRouter()

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/my-requests", response_model=List[schemas.ClientRequestOut])
def get_my_requests(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = Query(None, description="Фильтр по статусу"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Получить заявки текущего пользователя (клиента)"""
    if current_user.user_type != "Заказчик":
        raise HTTPException(status_code=403, detail="Только для заказчиков")
    
    query = db.query(models.Request).filter(models.Request.client_id == current_user.user_id)
    
    if status:
        query = query.filter(models.Request.request_status == status)
    
    return query.offset(skip).limit(limit).all()

@router.post("/my-requests", response_model=schemas.ClientRequestOut)
def create_my_request(
    request: schemas.ClientRequestCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Создать новую заявку для текущего пользователя"""
    if current_user.user_type != "Заказчик":
        raise HTTPException(status_code=403, detail="Только для заказчиков")
    
    request_data = request.dict()
    request_data["client_id"] = current_user.user_id
    request_data["request_status"] = "Новая заявка"
    request_data["priority"] = "Нормальный"  # Добавьте это!
    
    if not request_data.get("start_date"):
        request_data["start_date"] = date.today()
    
    try:
        db_request = models.Request(**request_data)
        db.add(db_request)
        db.commit()
        db.refresh(db_request)
        return db_request
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при создании заявки: {str(e)}")

@router.get("/my-requests/{request_id}", response_model=schemas.ClientRequestOut)
def get_my_request_detail(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Получить детали конкретной заявки пользователя"""
    if current_user.user_type != "Заказчик":
        raise HTTPException(status_code=403, detail="Только для заказчиков")
    
    request = db.query(models.Request).filter(
        models.Request.request_id == request_id,
        models.Request.client_id == current_user.user_id
    ).first()
    
    if not request:
        raise HTTPException(status_code=404, detail="Заявка не найдена или у вас нет доступа")
    
    return request