from fastapi import APIRouter, Depends,Query
from utils.search_airport import semantic_search as s_airport
from utils.search_airline import semantic_search as s_airline
from utils.search_plane import semantic_search as s_plane


router = APIRouter()

@router.get("/search-airport")
async def get_example(query:str = Query (...,description="Search Query")):
    result =await s_airport(query)
    return {"data": result}
@router.get("/search-airline")
async def get_example(query:str = Query (...,description="Search Query")):
    result =await s_airline(query)
    return {"data": result}
@router.get("/search-plane")
async def get_example(query:str = Query (...,description="Search Query")):
    result =await s_plane(query)
    return {"data": result}
