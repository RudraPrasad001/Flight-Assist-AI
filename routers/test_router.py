from fastapi import APIRouter, Depends
from utils.embedd_airport import example_function

router = APIRouter()

@router.get("/example")
def get_example():
    result = example_function()
    return {"data": result}
