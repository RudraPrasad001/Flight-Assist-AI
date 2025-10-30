from fastapi import APIRouter, Query
from utils.chat_search import intelligent_search
import json

router = APIRouter()

@router.get("/chat")
async def chat_search(query: str = Query(..., description="Natural language search query")):
    try:
        result = await intelligent_search(query)
        return {
            "query": query,
            "classification": result.get("classification", []),
            "results": result.get("results", {}),
            "summary": result.get("summary", ""),
            "map_data": result.get("map_data",{}),
            "has_map": result.get("has_map",""),
            "total_results": result.get("total_results", 0)

        }
    except Exception as e:
        return {
            "query": query,
            "error": str(e),
            "results": {},
            "total_results": 0
        }