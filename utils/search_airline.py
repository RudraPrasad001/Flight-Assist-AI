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
    against the 'airlines' table in MariaDB, returning top_k closest matches.
    """
    # Embed query text
    query_vector = model.encode(query_text).tolist()
    # Convert embedding list to JSON vector string format (no spaces)
    query_vector_str = "[" + ",".join(map(str, query_vector)) + "]"


    # Connect to MariaDB
    conn = mariadb.connect(
        user="root",
        password=os.getenv("DB_PASSWORD"),
        host="127.0.0.1",
        port=3306,
        database="flightdb2"
    )
    cur = conn.cursor()


    # SQL: Use VEC_DISTANCE_COSINE for cosine similarity distance,
    # order ascending, limit for top_k results.
    sql = f"""
    SELECT name, country, callsign, alid, VEC_DISTANCE_COSINE(airlines_embedding, VEC_FromText(?)) AS dist
    FROM airlines
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
#    query = "Indian airlines with Mumbai hub"
#    results = semantic_search(query)
#    for name, country, callsign, alid, distance in results:
#        print(f"{name} ({country}) - Callsign: {callsign} - ID: {alid} (distance: {distance})")
