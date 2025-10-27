import mariadb
import os
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

conn = mariadb.connect(
    user="root",
    password=os.getenv("DB_PASSWORD"),
    host="127.0.0.1",
    port=3306,
    database="flightdb2"
)
cur = conn.cursor()

model = SentenceTransformer('all-MiniLM-L6-v2')

# Fetch planes data with NULL handling
cur.execute("""
    SELECT 
        plid, 
        CONCAT(
            IFNULL(name, 'Unknown'), ', ',
            'abbreviation: ', IFNULL(abbr, 'N/A'), ', ',
            'IATA: ', IFNULL(iata, 'N/A'), ', ',
            'ICAO: ', IFNULL(icao, 'N/A')
        ) AS combined_text 
    FROM planes
""")
rows = cur.fetchall()

print(f"Processing {len(rows)} planes...")

# Process each plane
for row_id, text in rows:
    embedding_vector = model.encode(text).tolist()
    vector_str = "[" + ",".join(map(str, embedding_vector)) + "]"
    
    # Update planes table with embedding
    sql = "UPDATE planes SET planes_embedding = VEC_FromText(?) WHERE plid = ?"
    cur.execute(sql, (vector_str, row_id))

conn.commit()
print("Planes embeddings completed successfully!")
cur.close()
conn.close()
