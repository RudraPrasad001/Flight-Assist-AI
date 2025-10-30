import re
from typing import Dict, Any

from utils.search_airport import semantic_search as search_airports
from utils.search_airline import semantic_search as search_airlines
from utils.search_plane import semantic_search as search_planes
from utils.search_route import semantic_search as search_routes

# Import the map data builder
from utils.route_map import get_route_map_data


def classify_query(query: str) -> list:
    query_lower = query.lower()
    categories = []
    
    # Using Keywords TO Classify
    airport_keywords = [
        'airport', 'terminal', 'runway', 'gate', 'departure', 'arrival',
        'international airport', 'domestic airport', 'hub', 'layover',
        'city airport', 'regional airport'
    ]
    
    airline_keywords = [
        'airline', 'airways', 'carrier', 'flight company', 'aviation company',
        'airline company', 'air', 'flights by', 'operated by'
    ]
    
    plane_keywords = [
        'aircraft', 'plane', 'jet', 'boeing', 'airbus', 'bombardier',
        'embraer', 'wide body', 'narrow body', 'commercial aircraft',
        'airplane', 'aircraft type', 'fleet'
    ]
    
    route_keywords = [
        'route', 'flight', 'from', 'to', 'connection', 'direct flight',
        'connecting flight', 'flight path', 'journey', 'travel from',
        'fly from', 'flights between'
    ]
    
    # Check for each category
    if any(keyword in query_lower for keyword in airport_keywords):
        categories.append('airports')
    
    if any(keyword in query_lower for keyword in airline_keywords):
        categories.append('airlines')
        
    if any(keyword in query_lower for keyword in plane_keywords):
        categories.append('planes')
        
    if any(keyword in query_lower for keyword in route_keywords):
        categories.append('routes')
    
    # Special patterns for routes (from X to Y)
    if re.search(r'(from|between).*(to|and)', query_lower):
        if 'routes' not in categories:
            categories.append('routes')
    
    # If no specific category detected, search all
    if not categories:
        categories = ['airports', 'airlines', 'planes', 'routes']
    
    return categories


async def intelligent_search(query: str) -> Dict[str, Any]:
    categories = classify_query(query)
    results: Dict[str, Any] = {}
    total_results = 0

    # Map outputs
    map_data = None
    has_map = False
    
    # Search each classified category
    for category in categories:
        try:
            if category == 'airports':
                airport_results = await search_airports(query)
                if airport_results:
                    results['airports'] = airport_results
                    total_results += len(airport_results)
                    
            elif category == 'airlines':
                airline_results = await search_airlines(query)
                if airline_results:
                    results['airlines'] = airline_results
                    total_results += len(airline_results)
                    
            elif category == 'planes':
                plane_results = await search_planes(query)
                if plane_results:
                    results['planes'] = plane_results
                    total_results += len(plane_results)
                    
            elif category == 'routes':
                route_results = await search_routes(query)
                if route_results:
                    results['routes'] = route_results
                    total_results += len(route_results)
                    
        except Exception as e:
            print(f"Error searching {category}: {e}")
            continue
    
    # Build map data if routes found
    if 'routes' in results and results['routes']:
        try:
            ql = query.lower()
            max_stops = 0 if any(k in ql for k in ["direct", "non-stop", "nonstop"]) else 1
            map_data = await get_route_map_data(query, max_stops=max_stops)
            has_map = bool(map_data and map_data.get("airports"))
        except Exception as e:
            print(f"Error generating route map data: {e}")
            map_data = None
            has_map = False
    print(has_map)
    print(map_data)
    # Generate summary
    summary = generate_summary(query, categories, results, total_results, has_map=has_map)
    
    return {
        "classification": categories,
        "results": results,
        "summary": summary,
        "total_results": total_results,
        "map_data": map_data,
        "has_map": has_map
    }


def generate_summary(query: str, categories: list, results: dict, total_results: int, has_map: bool = False) -> str:
    if total_results == 0:
        return f"No results found for '{query}'. Try different keywords or check spelling."
    
    summary_parts = []
    
    if 'airports' in results:
        count = len(results['airports'])
        summary_parts.append(f"{count} airport{'s' if count != 1 else ''}")
    
    if 'airlines' in results:
        count = len(results['airlines'])
        summary_parts.append(f"{count} airline{'s' if count != 1 else ''}")
        
    if 'planes' in results:
        count = len(results['planes'])
        summary_parts.append(f"{count} aircraft type{'s' if count != 1 else ''}")
        
    if 'routes' in results:
        count = len(results['routes'])
        summary_parts.append(f"{count} route{'s' if count != 1 else ''}")
    
    if len(summary_parts) == 1:
        summary = f"Found {summary_parts[0]} matching '{query}'"
    elif len(summary_parts) == 2:
        summary = f"Found {summary_parts[0]} and {summary_parts[1]} matching '{query}'"
    else:
        summary = f"Found {', '.join(summary_parts[:-1])}, and {summary_parts[-1]} matching '{query}'"
    
    if has_map and 'routes' in results:
        summary += ". Map data available"
    
    return summary
