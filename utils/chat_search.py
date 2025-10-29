import re
from utils.search_airport import semantic_search as search_airports
from utils.search_airline import semantic_search as search_airlines  
from utils.search_plane import semantic_search as search_planes
from utils.search_route import semantic_search as search_routes

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

async def intelligent_search(query: str) -> dict:
    categories = classify_query(query)
    results = {}
    total_results = 0
    
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
    
    # Generate summary
    summary = generate_summary(query, categories, results, total_results)
    
    return {
        "classification": categories,
        "results": results,
        "summary": summary,
        "total_results": total_results
    }

def generate_summary(query: str, categories: list, results: dict, total_results: int) -> str:
    # Generating Human Response
    
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
    
    return summary