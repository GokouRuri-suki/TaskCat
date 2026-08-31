from fastapi import FastAPI
import json
import os
curr_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(curr_dir,"data","data.json")


app = FastAPI()

@app.get("/get")
async def get_data():
  
    with open (data_path,'r',encoding="utf-8")as f:
      data = json.load(f)
      return data

    

