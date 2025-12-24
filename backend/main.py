from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import users, requests, comments, auth as auth_router, client, qr
from backend.database import Base, engine
import backend.models

app = FastAPI(title="Service Center API", version="1.0.0")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(requests.router, prefix="/requests", tags=["Requests"])
app.include_router(comments.router, prefix="/comments", tags=["Comments"])
app.include_router(auth_router.router, prefix="/auth", tags=["Auth"])
app.include_router(client.router, prefix="/client", tags=["Client"])
app.include_router(qr.router, prefix="/qr", tags=["QR"])

@app.get("/")
def root():
    return {"message": "Service Center API", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)