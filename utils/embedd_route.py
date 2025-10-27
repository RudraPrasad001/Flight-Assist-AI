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
# Enhanced routes embedding with full names
cur.execute("""
    SELECT 
        r.rid, 
        CONCAT(
            'Flight from ', IFNULL(ap1.name, r.src_ap), ' (', IFNULL(r.src_ap, 'N/A'), ') ',
            'to ', IFNULL(ap2.name, r.dst_ap), ' (', IFNULL(r.dst_ap, 'N/A'), ') ',
            'by airline ', IFNULL(al.name, r.airline), ' ',
            'on ', IFNULL(r.equipment, 'N/A')
        ) AS combined_text 
    FROM routes r
    LEFT JOIN airports ap1 ON r.src_ap = ap1.iata
    LEFT JOIN airports ap2 ON r.dst_ap = ap2.iata
    LEFT JOIN airlines al ON r.airline = al.iata
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
