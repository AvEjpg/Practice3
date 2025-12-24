from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import crud, schemas, database
from ..auth import require_roles, get_current_user, hash_password

router = APIRouter()

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=list[schemas.UserOut])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), 
               current=Depends(require_roles('Менеджер','Менеджер по качеству'))):
    return crud.get_users(db, skip=skip, limit=limit)

@router.get("/{user_id}", response_model=schemas.UserOut)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.post("/", response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db), 
                current=Depends(require_roles('Менеджер'))):
    return crud.create_user(db, user)

@router.put("/{user_id}", response_model=schemas.UserOut)
def update_user(user_id: int, user_update: schemas.UserUpdate, db: Session = Depends(get_db),
                current=Depends(require_roles('Менеджер', 'Менеджер по качеству'))):
    """Обновление пользователя"""
    db_user = crud.get_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Преобразуем данные для обновления
    update_data = user_update.dict(exclude_unset=True)
    
    # Если указан пароль, хешируем его
    if "password" in update_data and update_data["password"]:
        update_data["password"] = hash_password(update_data["password"])
    elif "password" in update_data:
        # Если пароль пустой, не обновляем его
        del update_data["password"]
    
    # Обновляем поля
    for key, value in update_data.items():
        setattr(db_user, key, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), 
                current=Depends(require_roles('Менеджер'))):
    deleted = crud.delete_user(db, user_id)
    if deleted is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return {"detail": "Пользователь удалён"}