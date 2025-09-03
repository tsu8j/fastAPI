from fastapi import FastAPI
from app.routers.tasks import router as tasks_router  
app = FastAPI(title="Task Manager API", version="1.0.0")

@app.get("/")
def hello():
   return {"message": "Hello FastAPI!"}
# /tasks 配下のCRUDを登録
#  register CRUD under /tasks
app.include_router(tasks_router)