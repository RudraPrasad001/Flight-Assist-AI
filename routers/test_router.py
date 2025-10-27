from fastapi import APIRouter, Depends
from utils.example_util import example_function

router = APIRouter()

@router.get("/example")
def get_example():
    result = example_function()
    return {"data": result}
