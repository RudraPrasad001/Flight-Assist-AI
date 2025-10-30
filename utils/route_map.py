# utils/route_map.py
from __future__ import annotations

import os
import re
from typing import Dict, Any, List, Tuple, Set, Optional

import mariadb
from dotenv import load_dotenv

load_dotenv()

# -----------------------------
# DB connection
# -----------------------------
def _db_connect():
    return mariadb.connect(
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        database=os.getenv("DB_NAME", "flightdb2"),
    )

# -----------------------------
# Helpers
# -----------------------------
def _extract_from_to(query: str) -> Tuple[Optional[str], Optional[str]]:
    q = query.strip()
    m = re.search(r"\bfrom\s+(.*?)\s+to\s+(.*)", q, flags=re.IGNORECASE)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    m2 = re.search(r"\bbetween\s+(.*?)\s+and\s+(.*)", q, flags=re.IGNORECASE)
    if m2:
        return m2.group(1).strip(), m2.group(2).strip()
    return None, None

def _looks_like_iata(token: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z]{3}", token.strip()))

def _detect_coord_columns(cur) -> tuple[str, str]:
    """
    Detect latitude/longitude columns for airports table.
    Supports latitude/longitude, lat/lon/lng, latitude_deg/longitude_deg, and y/x.
    """
    candidates_lat = ["latitude", "lat", "latitude_deg", "y"]  # y is common for latitude
    candidates_lon = ["longitude", "lon", "lng", "longitude_deg", "x"]  # x is common for longitude

    cur.execute("""
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'airports'
    """)
    cols = {row[0].lower() for row in cur.fetchall()}

    lat_col = next((c for c in candidates_lat if c in cols), None)
    lon_col = next((c for c in candidates_lon if c in cols), None)

    if not lat_col or not lon_col:
        raise ValueError(f"Airports table missing coordinate columns; looked for {candidates_lat} and {candidates_lon}")

    return lat_col, lon_col

def _resolve_place_kind(cur, token: str):
    """
    Classify token using airports data: country > city > IATA.
    """
    t = token.strip()
    if not t:
        return (None, None)

    if _looks_like_iata(t):
        return ("iata", t.upper())

    # Country exact
    cur.execute("SELECT 1 FROM airports WHERE LOWER(country) = LOWER(?) LIMIT 1", (t,))
    if cur.fetchone():
        return ("country", t.title())

    # City exact
    cur.execute("SELECT 1 FROM airports WHERE LOWER(city) = LOWER(?) LIMIT 1", (t,))
    if cur.fetchone():
        return ("city", t.title())

    # Country title-case fallback
    cur.execute("SELECT 1 FROM airports WHERE LOWER(country) = LOWER(?) LIMIT 1", (t.title(),))
    if cur.fetchone():
        return ("country", t.title())

    return (None, None)

# -----------------------------
# Queries
# -----------------------------
def _search_direct_routes_by_filters(
    cur,
    src_country: Optional[str],
    dst_country: Optional[str],
    src_city: Optional[str],
    dst_city: Optional[str],
    src_code: Optional[str],
    dst_code: Optional[str],
    limit: int = 20,
) -> List[Tuple]:
    """
    Return rows:
    (airline_code, airline_name, src_code_out, src_name, src_city, src_country,
     dst_code_out, dst_name, dst_city, dst_country, equipment, rid)
    Joins routes to airports by both IATA and ICAO and coalesces fields.
    """
    base = """
    SELECT 
        r.airline AS airline_code,
        COALESCE(al.name, r.airline) AS airline_name,

        -- Source code preference: prefer IATA if present, else ICAO, else original
        COALESCE(ap1_iata.iata, ap1_icao.icao, r.src_ap) AS src_code_out,
        COALESCE(ap1_iata.name, ap1_icao.name, r.src_ap) AS src_name,
        COALESCE(ap1_iata.city, ap1_icao.city, '') AS src_city,
        COALESCE(ap1_iata.country, ap1_icao.country, '') AS src_country,

        -- Destination code preference
        COALESCE(ap2_iata.iata, ap2_icao.icao, r.dst_ap) AS dst_code_out,
        COALESCE(ap2_iata.name, ap2_icao.name, r.dst_ap) AS dst_name,
        COALESCE(ap2_iata.city, ap2_icao.city, '') AS dst_city,
        COALESCE(ap2_iata.country, ap2_icao.country, '') AS dst_country,

        COALESCE(r.equipment, '') AS equipment,
        r.rid AS rid
    FROM routes r
    LEFT JOIN airlines al ON r.airline = al.iata
    LEFT JOIN airports ap1_iata ON r.src_ap = ap1_iata.iata
    LEFT JOIN airports ap1_icao ON r.src_ap = ap1_icao.icao
    LEFT JOIN airports ap2_iata ON r.dst_ap = ap2_iata.iata
    LEFT JOIN airports ap2_icao ON r.dst_ap = ap2_icao.icao
    """
    where = []
    params: List[Any] = []

    # Code filters: apply against either matched code
    if src_code:
        where.append("(UPPER(ap1_iata.iata) = UPPER(?) OR UPPER(ap1_icao.icao) = UPPER(?))")
        params.extend([src_code, src_code])
    if dst_code:
        where.append("(UPPER(ap2_iata.iata) = UPPER(?) OR UPPER(ap2_icao.icao) = UPPER(?))")
        params.extend([dst_code, dst_code])

    # Country / city filters via COALESCE to cover both joins
    if src_country:
        where.append("LOWER(COALESCE(ap1_iata.country, ap1_icao.country)) = LOWER(?)")
        params.append(src_country)
    if dst_country:
        where.append("LOWER(COALESCE(ap2_iata.country, ap2_icao.country)) = LOWER(?)")
        params.append(dst_country)

    if src_city:
        where.append("LOWER(COALESCE(ap1_iata.city, ap1_icao.city)) = LOWER(?)")
        params.append(src_city)
    if dst_city:
        where.append("LOWER(COALESCE(ap2_iata.city, ap2_icao.city)) = LOWER(?)")
        params.append(dst_city)

    sql = base
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " LIMIT ?"
    params.append(int(limit))

    cur.execute(sql, tuple(params))
    return cur.fetchall()

def _fetch_airport_coords(cur, codes: Set[str]) -> List[Dict[str, Any]]:
    """
    Fetch airports by either IATA or ICAO code and return coordinates using detected columns.
    """
    if not codes:
        return []
    lat_col, lon_col = _detect_coord_columns(cur)

    placeholders = ",".join(["?"] * len(codes))
    sql = f"""
        SELECT 
            iata, icao, name, city, country, {lat_col} AS latitude, {lon_col} AS longitude
        FROM airports
        WHERE iata IN ({placeholders}) OR icao IN ({placeholders})
    """
    params = tuple(codes) + tuple(codes)
    cur.execute(sql, params)

    out = []
    for (iata, icao, name, city, country, lat, lon) in cur.fetchall():
        if lat is None or lon is None:
            continue
        # Prefer IATA label if present, else ICAO
        code = iata if iata else icao
        out.append({
            "code": code,
            "iata": iata,
            "icao": icao,
            "name": name,
            "city": city,
            "country": country,
            "latitude": float(lat),
            "longitude": float(lon),
        })
    return out

def _find_one_stop(cur, origin_code: str, destination_code: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    One-stop: origin -> hub -> destination, matching codes against both IATA and ICAO.
    """
    # Find matching ICAO/IATA for origin/destination to cover either form
    cur.execute("""
        SELECT iata, icao FROM airports
        WHERE iata = ? OR icao = ?
        LIMIT 1
    """, (origin_code, origin_code))
    row_o = cur.fetchone()
    origin_iata, origin_icao = (row_o or (None, None))

    cur.execute("""
        SELECT iata, icao FROM airports
        WHERE iata = ? OR icao = ?
        LIMIT 1
    """, (destination_code, destination_code))
    row_d = cur.fetchone()
    dest_iata, dest_icao = (row_d or (None, None))

    # Build candidate match list for routes.src_ap/dst_ap (which may be ICAO in your schema)
    origin_matches = [c for c in [origin_iata, origin_icao, origin_code] if c]
    dest_matches = [c for c in [dest_iata, dest_icao, destination_code] if c]

    # Use IN lists for both legs
    ph_o = ",".join(["?"] * len(origin_matches))
    ph_d = ",".join(["?"] * len(dest_matches))

    cur.execute(f"""
        SELECT 
            r1.src_ap AS origin,
            r1.dst_ap AS hub,
            r2.dst_ap AS destination,
            COALESCE(al1.name, r1.airline) AS leg1_airline_name,
            COALESCE(al2.name, r2.airline) AS leg2_airline_name,
            COALESCE(r1.equipment, '') AS leg1_equipment,
            COALESCE(r2.equipment, '') AS leg2_equipment,
            r1.rid AS leg1_rid,
            r2.rid AS leg2_rid,

            COALESCE(ap_hub_iata.name, ap_hub_icao.name) AS hub_name,
            COALESCE(ap_hub_iata.city, ap_hub_icao.city) AS hub_city,
            COALESCE(ap_hub_iata.country, ap_hub_icao.country) AS hub_country,
            {', '.join([
                # use detected coords for hub via subselect trick (we’ll replace later)
                # Placeholder; we’ll fill hub coords via airports fetch instead of inline select
                "NULL AS hub_lat",
                "NULL AS hub_lon"
            ])}
        FROM routes r1
        JOIN routes r2 ON r1.dst_ap = r2.src_ap
        LEFT JOIN airlines al1 ON r1.airline = al1.iata
        LEFT JOIN airlines al2 ON r2.airline = al2.iata
        LEFT JOIN airports ap_hub_iata ON r1.dst_ap = ap_hub_iata.iata
        LEFT JOIN airports ap_hub_icao ON r1.dst_ap = ap_hub_icao.icao
        WHERE r1.src_ap IN (""" + ph_o + f""") AND r2.dst_ap IN ({ph_d})
        LIMIT ?
    """, tuple(origin_matches + dest_matches + [limit]))

    conns = []
    hubs: Set[str] = set()
    for row in cur.fetchall():
        (origin, hub, destination,
         leg1_airline, leg2_airline,
         leg1_equipment, leg2_equipment,
         leg1_rid, leg2_rid,
         hub_name, hub_city, hub_country, _hub_lat, _hub_lon) = row
        conns.append({
            "src": origin,
            "hub": hub,
            "dst": destination,
            "hub_name": hub_name,
            "hub_city": hub_city,
            "hub_country": hub_country,
            "hub_latitude": None,
            "hub_longitude": None,
            "leg1_airline": leg1_airline,
            "leg2_airline": leg2_airline,
            "leg1_equipment": leg1_equipment or "Unknown",
            "leg2_equipment": leg2_equipment or "Unknown",
            "leg1_rid": leg1_rid,
            "leg2_rid": leg2_rid,
            "stops": 1,
            "type": "layover"
        })
        hubs.add(hub)

    # Fill hub coordinates
    if conns and hubs:
        hub_list = list(hubs)
        lat_col, lon_col = _detect_coord_columns(cur)
        ph = ",".join(["?"] * len(hub_list))
        cur.execute(f"""
            SELECT iata, icao, {lat_col} AS lat, {lon_col} AS lon
            FROM airports
            WHERE iata IN ({ph}) OR icao IN ({ph})
        """, tuple(hub_list + hub_list))
        coord = {}
        for (iata, icao, lat, lon) in cur.fetchall():
            key1 = iata if iata else None
            key2 = icao if icao else None
            if key1:
                coord[key1] = (lat, lon)
            if key2:
                coord[key2] = (lat, lon)
        for c in conns:
            if c["hub"] in coord:
                lat, lon = coord[c["hub"]]
                if lat is not None and lon is not None:
                    c["hub_latitude"] = float(lat)
                    c["hub_longitude"] = float(lon)

    return conns

# -----------------------------
# Public API
# -----------------------------
async def get_route_map_data(query: str, max_stops: int = 1, limit: int = 20) -> Dict[str, Any]:
    """
    Map data for prompts like 'Routes from India to Japan'.
    """
    left, right = _extract_from_to(query)

    conn = _db_connect()
    try:
        cur = conn.cursor()

        # Classify endpoints using DB
        src_country = src_city = src_code = None
        dst_country = dst_city = dst_code = None

        if left:
            kind, val = _resolve_place_kind(cur, left)
            if kind == "country":
                src_country = val
            elif kind == "city":
                src_city = val.lower()
            elif kind == "iata":
                src_code = val  # may be IATA; joins also check ICAO

        if right:
            kind, val = _resolve_place_kind(cur, right)
            if kind == "country":
                dst_country = val
            elif kind == "city":
                dst_city = val.lower()
            elif kind == "iata":
                dst_code = val

        # Direct routes via flexible joins
        rows = _search_direct_routes_by_filters(
            cur,
            src_country, dst_country,
            src_city, dst_city,
            src_code, dst_code,
            limit=limit
        )

        if not rows:
            return {"airports": [], "direct_routes": [], "layover_routes": []}

        direct_routes: List[Dict[str, Any]] = []
        airport_codes: Set[str] = set()

        for (airline_code, airline_name,
             src_code_out, src_name, src_city_val, src_country_val,
             dst_code_out, dst_name, dst_city_val, dst_country_val,
             equipment, rid) in rows:

            direct_routes.append({
                "route_id": rid,
                "src": src_code_out,
                "dst": dst_code_out,
                "src_city": src_city_val,
                "src_country": src_country_val,
                "dst_city": dst_city_val,
                "dst_country": dst_country_val,
                "airline": airline_name or airline_code,
                "airline_code": airline_code,
                "equipment": equipment or "Unknown",
                "stops": 0,
                "type": "direct"
            })
            airport_codes.add(src_code_out)
            airport_codes.add(dst_code_out)

        airports = _fetch_airport_coords(cur, airport_codes)
        print(airports)
        layover_routes: List[Dict[str, Any]] = []
        if max_stops >= 1 and direct_routes:
            origin = direct_routes[0]["src"]
            destination = direct_routes[0]["dst"]
            layover_routes = _find_one_stop(cur, origin, destination, limit=10)

            # Add hub airport nodes if coords exist
            known = {(a.get("code") or a.get("iata") or a.get("icao")) for a in airports}
            for l in layover_routes:
                hub_code = l["hub"]
                if l["hub_latitude"] is None or l["hub_longitude"] is None:
                    continue
                if hub_code not in known:
                    airports.append({
                        "code": hub_code,
                        "iata": None,
                        "icao": None,
                        "name": l["hub_name"],
                        "city": l["hub_city"],
                        "country": l["hub_country"],
                        "latitude": l["hub_latitude"],
                        "longitude": l["hub_longitude"],
                    })
                    known.add(hub_code)

    finally:
        try:
            cur.close()
        except Exception:
            pass
        conn.close()
    data =  {
        "airports": airports,
        "direct_routes": direct_routes,
        "layover_routes": layover_routes
    }
    return data
