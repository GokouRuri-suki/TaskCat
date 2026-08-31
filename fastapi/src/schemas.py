from pydantic import BaseModel
import uuid

class UserBaseModel(BaseModel):#基本模型
    uid:uuid=uuid.uuid4()
    user:str
    name:str
    modify_int:int


class TaskBaseModel(BaseModel):
    title:str
    task:str
    is_complete:bool
    priority:int

