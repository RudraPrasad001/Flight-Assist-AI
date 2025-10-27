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

# Fetch airlines data with NULL handling
cur.execute("""
    SELECT 
        alid, 
        CONCAT(
            IFNULL(name, 'Unknown'), ', ',
            'alias: ', IFNULL(alias, 'N/A'), ', ',
            'country: ', IFNULL(country, 'N/A'), ', ',
            'callsign: ', IFNULL(callsign, 'N/A')
        ) AS combined_text 
    FROM airlines
""")
rows = cur.fetchall()

print(f"Processing {len(rows)} airlines...")

# Process each airline
for row_id, text in rows:
    embedding_vector = model.encode(text).tolist()
    vector_str = "[" + ",".join(map(str, embedding_vector)) + "]"
    
    # Update airlines table with embedding
    sql = "UPDATE airlines SET airlines_embedding = VEC_FromText(?) WHERE alid = ?"
    cur.execute(sql, (vector_str, row_id))

conn.commit()
print("Airlines embeddings completed successfully!")
cur.close()
conn.close()
