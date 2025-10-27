from fastapi import APIRouter, Depends,Query
from utils.search_airport import semantic_search

router = APIRouter()

@router.get("/search")
async def get_example(query:str = Query (...,description="Search Query")):
    result =await semantic_search(query)
    return {"data": result}
