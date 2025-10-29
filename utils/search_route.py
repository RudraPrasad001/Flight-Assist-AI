import mariadb
import os
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv


load_dotenv()


# Load embedding model globally
model = SentenceTransformer('all-MiniLM-L6-v2')


async def semantic_search(query_text, top_k=5):
    """
    Given a query string, embed it and perform a vector similarity search
    against the 'routes' table in MariaDB, returning top_k closest matches
    with full airline and airport names.
    """
    # Embed query text
    query_vector = model.encode(query_text).tolist()
    # Convert embedding list to JSON vector string format (no spaces)
    query_vector_str = "[" + ",".join(map(str, query_vector)) + "]"


    # Connect to MariaDB
    try:
        conn = mariadb.connect(
            user="root",
            password=os.getenv("DB_PASSWORD"),  # Direct password
            host="127.0.0.1",
            port=os.getenv("DB_PORT"),  # Correct MariaDB port
            database="flightdb2"
        )
    except mariadb.Error as e:
        print(f"Database connection error: {e}")
        return []
    cur = conn.cursor()


    # SQL: JOIN with airlines and airports to get full names
    sql = f"""
    SELECT 
        r.airline,
        IFNULL(al.name, r.airline) AS airline_name,
        r.src_ap,
        IFNULL(ap1.name, r.src_ap) AS src_airport_name,
        IFNULL(ap1.city, '') AS src_city,
        r.dst_ap,
        IFNULL(ap2.name, r.dst_ap) AS dst_airport_name,
        IFNULL(ap2.city, '') AS dst_city,
        r.equipment,
        r.rid,
        VEC_DISTANCE_COSINE(r.routes_embedding, VEC_FromText(?)) AS dist
    FROM routes r
    LEFT JOIN airlines al ON r.airline = al.iata
    LEFT JOIN airports ap1 ON r.src_ap = ap1.iata
    LEFT JOIN airports ap2 ON r.dst_ap = ap2.iata
    ORDER BY dist ASC
    LIMIT {top_k};
    """


    cur.execute(sql, (query_vector_str,))
    results = cur.fetchall()


    cur.close()
    conn.close()


    return results



# Example usage:
#if __name__ == "__main__":
#    query = "flights from London to New York"
#    results = semantic_search(query)
#    for airline_code, airline_name, src_code, src_name, src_city, dst_code, dst_name, dst_city, equipment, rid, distance in results:
#        print(f"{airline_name} ({airline_code}): {src_name} ({src_code}, {src_city}) → {dst_name} ({dst_code}, {dst_city})")
#        print(f"  Aircraft: {equipment} | Route ID: {rid} | Distance: {distance:.4f}\n")
