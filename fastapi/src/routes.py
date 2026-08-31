from fastapi import FastAPI,HTTPException,status
import json
import os

from fastapi.routing import APIRoute
curr_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(curr_dir,"data","data.json")

task = APIRoute()

@task.get("/task")
def get_info():
  try:
    with open(data_path,'r',encoding='utf-8')as f:
      data = json.load(f)
      return data
  except FileNotFoundError:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
  