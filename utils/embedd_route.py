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

# Fetch routes data with NULL handling and enriched context
cur.execute("""
    SELECT 
        rid, 
        CONCAT(
            'Flight from ', IFNULL(src_ap, 'Unknown'), 
            ' to ', IFNULL(dst_ap, 'Unknown'), 
            ' by airline ', IFNULL(airline, 'Unknown'), 
            ' on ', IFNULL(equipment, 'N/A')
        ) AS combined_text 
    FROM routes
""")
rows = cur.fetchall()

print(f"Processing {len(rows)} routes...")

# Process each route
for row_id, text in rows:
    embedding_vector = model.encode(text).tolist()
    vector_str = "[" + ",".join(map(str, embedding_vector)) + "]"
    
    # Update routes table with embedding
    sql = "UPDATE routes SET routes_embedding = VEC_FromText(?) WHERE rid = ?"
    cur.execute(sql, (vector_str, row_id))

conn.commit()
print("Routes embeddings completed successfully!")
cur.close()
conn.close()
