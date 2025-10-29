import os
import re
import mariadb
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Optional: use pycountry if available for robust country detection
try:
    import pycountry
except ImportError:
    pycountry = None

load_dotenv()

# Load embedding model globally
model = SentenceTransformer('all-MiniLM-L6-v2')

# Common aliases for country names that users type differently
COUNTRY_ALIASES = {
    "uk": "United Kingdom",
    "u.k.": "United Kingdom",
    "england": "United Kingdom",
    "scotland": "United Kingdom",
    "wales": "United Kingdom",
    "u.s.": "United States",
    "usa": "United States",
    "us": "United States",
    "u.s.a.": "United States",
    "uae": "United Arab Emirates",
    "korea": "South Korea",
    "south korea": "South Korea",
    "north korea": "North Korea",
    "russia": "Russian Federation",
    "vietnam": "Viet Nam",
    "iran": "Iran, Islamic Republic of",
    "bolivia": "Bolivia, Plurinational State of",
    "tanzania": "Tanzania, United Republic of",
    "venezuela": "Venezuela, Bolivarian Republic of",
    "laos": "Lao People's Democratic Republic",
    "moldova": "Moldova, Republic of",
    "czech republic": "Czechia",
    "turkiye": "Turkey",
}

def normalize_country_name(name: str) -> str:
    if not name:
        return ""
    n = name.strip().lower()
    if n in COUNTRY_ALIASES:
        return COUNTRY_ALIASES[n]
    # Try pycountry for canonicalization
    if pycountry:
        # Exact name
        for c in pycountry.countries:
            if c.name.lower() == n:
                return c.name
            if getattr(c, "official_name", "").lower() == n:
                return c.name
            if getattr(c, "alpha_2", "").lower() == n or getattr(c, "alpha_3", "").lower() == n:
                return c.name
        # Fuzzy contains
        for c in pycountry.countries:
            if n in c.name.lower() or n in getattr(c, "official_name", "").lower():
                return c.name
    # Fallback: title case the input
    return name.strip().title()

def extract_from_to_spans(q: str):
    """
    Extract the 'from ... to ...' spans if present.
    Returns (left, right) strings or (None, None).
    """
    ql = q.lower()
    # Support "from X to Y" or "X to Y" or "X -> Y"
    m = re.search(r"\bfrom\s+(.*?)\s+(?:to|->)\s+(.*)", ql)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    m2 = re.search(r"^(.*?)[\s]+(?:to|->)[\s]+(.*)$", ql)
    if m2:
        return m2.group(1).strip(), m2.group(2).strip()
    return None, None

def looks_like_iata(token: str) -> bool:
    t = token.strip().upper()
    return bool(re.fullmatch(r"[A-Z]{3}", t))

def classify_place(text: str):
    """
    Classify a free-text place string as (country, city, iata).
    Strategy:
      - If it matches an IATA-like code (3 letters), treat as airport IATA.
      - If it matches a known/aliased country, return as country.
      - Otherwise treat as city string.
    """
    s = text.strip()
    # Try to isolate the main token (drop punctuation)
    token = re.sub(r"[^A-Za-z\s]", " ", s).strip()
    token = re.sub(r"\s+", " ", token)

    # IATA code?
    if looks_like_iata(token):
        return None, None, token.upper()

    # Try country normalization
    country_guess = normalize_country_name(token)
    # If normalization changed case meaningfully or matched pycountry/alias, accept it
    if country_guess and country_guess.lower() != token.lower():
        return country_guess, None, None
    if pycountry:
        for c in pycountry.countries:
            if token.lower() == c.name.lower() or token.lower() == getattr(c, "official_name", "").lower():
                return c.name, None, None

    # Fallback: treat as city
    city = token.title()
    return None, city, None

def detect_locations(query_text: str):
    """
    Returns a dict with keys:
      src_country, dst_country, src_city, dst_city, src_iata, dst_iata, any_side (list)
    any_side is used when direction is not specified; items may be countries, cities, or IATA codes.
    """
    src, dst = extract_from_to_spans(query_text)
    result = {
        "src_country": None,
        "dst_country": None,
        "src_city": None,
        "dst_city": None,
        "src_iata": None,
        "dst_iata": None,
        "any_side": []
    }

    if src or dst:
        if src:
            ctry, city, iata = classify_place(src)
            result["src_country"] = ctry
            result["src_city"] = city
            result["src_iata"] = iata
        if dst:
            ctry, city, iata = classify_place(dst)
            result["dst_country"] = ctry
            result["dst_city"] = city
            result["dst_iata"] = iata
    else:
        # No clear direction; collect any countries/cities/IATAs mentioned after keywords
        # Simple split on connective words
        tokens = re.split(r"[,;/]| and | or | to | from ", query_text, flags=re.IGNORECASE)
        for t in tokens:
            t = t.strip()
            if not t:
                continue
            ctry, city, iata = classify_place(t)
            if ctry:
                result["any_side"].append(("country", ctry))
            elif city:
                result["any_side"].append(("city", city))
            elif iata:
                result["any_side"].append(("iata", iata))

    return result

async def semantic_search(query_text: str, top_k: int = 5):
    """
    Embed the query and perform a vector similarity search against routes,
    adding country/city/IATA filters via the airports table when detected.
    """
    # Embed query
    query_vector = model.encode(query_text).tolist()
    query_vector_str = "[" + ",".join(map(str, query_vector)) + "]"

    # DB connect
    try:
        conn = mariadb.connect(
            user="root",
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=int(os.getenv("DB_PORT", "3306")),
            database=os.getenv("DB_NAME", "flightdb2")
        )
    except mariadb.Error as e:
        print(f"Database connection error: {e}")
        return []

    cur = conn.cursor()

    # Detect locations
    loc = detect_locations(query_text)

    # Base SQL
    sql = """
    SELECT
        r.airline,
        IFNULL(al.name, r.airline) AS airline_name,
        r.src_ap,
        IFNULL(ap1.name, r.src_ap) AS src_airport_name,
        IFNULL(ap1.city, '') AS src_city,
        IFNULL(ap1.country, '') AS src_country,
        r.dst_ap,
        IFNULL(ap2.name, r.dst_ap) AS dst_airport_name,
        IFNULL(ap2.city, '') AS dst_city,
        IFNULL(ap2.country, '') AS dst_country,
        r.equipment,
        r.rid,
        VEC_DISTANCE_COSINE(r.routes_embedding, VEC_FromText(?)) AS dist
    FROM routes r
    JOIN airports ap1 ON r.src_ap = ap1.iata
    JOIN airports ap2 ON r.dst_ap = ap2.iata
    LEFT JOIN airlines al ON r.airline = al.iata
    """
    params = [query_vector_str]
    where_clauses = []

    # Directional filters
    if loc["src_country"]:
        where_clauses.append("LOWER(ap1.country) = LOWER(?)")
        params.append(loc["src_country"])
    if loc["dst_country"]:
        where_clauses.append("LOWER(ap2.country) = LOWER(?)")
        params.append(loc["dst_country"])
    if loc["src_city"]:
        where_clauses.append("LOWER(ap1.city) = LOWER(?)")
        params.append(loc["src_city"])
    if loc["dst_city"]:
        where_clauses.append("LOWER(ap2.city) = LOWER(?)")
        params.append(loc["dst_city"])
    if loc["src_iata"]:
        where_clauses.append("UPPER(ap1.iata) = UPPER(?)")
        params.append(loc["src_iata"])
    if loc["dst_iata"]:
        where_clauses.append("UPPER(ap2.iata) = UPPER(?)")
        params.append(loc["dst_iata"])

    # Non-directional filters: apply as (ap1 X IN (...) OR ap2 X IN (...))
    if not any([loc["src_country"], loc["dst_country"], loc["src_city"], loc["dst_city"], loc["src_iata"], loc["dst_iata"]]) and loc["any_side"]:
        countries = [v for t, v in loc["any_side"] if t == "country"]
        cities = [v for t, v in loc["any_side"] if t == "city"]
        iatas = [v for t, v in loc["any_side"] if t == "iata"]

        or_parts = []
        if countries:
            ph = ", ".join(["LOWER(?)"] * len(countries))
            or_parts.append(f"LOWER(ap1.country) IN ({ph}) OR LOWER(ap2.country) IN ({ph})")
            params.extend(countries + countries)
        if cities:
            ph = ", ".join(["LOWER(?)"] * len(cities))
            or_parts.append(f"LOWER(ap1.city) IN ({ph}) OR LOWER(ap2.city) IN ({ph})")
            params.extend(cities + cities)
        if iatas:
            ph = ", ".join(["UPPER(?)"] * len(iatas))
            or_parts.append(f"UPPER(ap1.iata) IN ({ph}) OR UPPER(ap2.iata) IN ({ph})")
            params.extend(iatas + iatas)

        if or_parts:
            where_clauses.append("(" + " OR ".join(or_parts) + ")")

    if where_clauses:
        sql += " WHERE " + " AND ".join(where_clauses)

    sql += f" ORDER BY dist ASC LIMIT {int(top_k)};"

    try:
        cur.execute(sql, tuple(params))
        rows = cur.fetchall()
    except mariadb.Error as e:
        print(f"Error searching routes: {e}")
        rows = []
    finally:
        cur.close()
        conn.close()

    return rows

# Example usage
if __name__ == "__main__":
    import asyncio

    async def demo(q):
        results = await semantic_search(q, top_k=5)
        for (airline_code, airline_name,
             src_code, src_name, src_city, src_country,
             dst_code, dst_name, dst_city, dst_country,
             equipment, rid, distance) in results:
            print(f"{airline_name} ({airline_code}): {src_name} ({src_code}, {src_city}, {src_country}) → {dst_name} ({dst_code}, {dst_city}, {dst_country})")
            print(f"  Aircraft: {equipment} | Route ID: {rid} | Cosine dist: {distance:.4f}\n")

    queries = [
        "routes from Japan to India",
        "Search flights from India to London",
        "flights from LHR to JFK",
        "India to UAE",
        "Delhi to Tokyo",
    ]
    for q in queries:
        print(f"Query: {q}\n" + "-"*60)
        asyncio.run(demo(q))
