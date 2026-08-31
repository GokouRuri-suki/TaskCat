from fastapi import FastAPI

from src.routes import task_router

version = "ver1.0"

app = FastAPI(version=version, title="TaskCat")
app.include_router(task_router, prefix=f"/TaskCat/api/{version}", tags=["Task"])


