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
    against the 'planes' table in MariaDB, returning top_k closest matches.
    """
    # Embed query text
    query_vector = model.encode(query_text).tolist()
    # Convert embedding list to JSON vector string format (no spaces)
    query_vector_str = "[" + ",".join(map(str, query_vector)) + "]"


    # Connect to MariaDB
    try:
        conn = mariadb.connect(
            user="root",
            password=os.getenv("DB_PASSWORD"),
            host="127.0.0.1",
            port=int(os.getenv("DB_PORT")),
            database="flightdb2"
        )
    except mariadb.Error as e:
        print(f"Database connection error: {e}")
        return []
    cur = conn.cursor()


    # SQL: Use VEC_DISTANCE_COSINE for cosine similarity distance,
    # order ascending, limit for top_k results.
    sql = f"""
    SELECT name, abbr, iata, icao, plid, VEC_DISTANCE_COSINE(planes_embedding, VEC_FromText(?)) AS dist
    FROM planes
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
#    query = "Boeing 737"
#    results = semantic_search(query)
#    for name, abbr, iata, icao, plid, distance in results:
#        print(f"{name} ({abbr}) - IATA: {iata}, ICAO: {icao} - ID: {plid} (distance: {distance})")
