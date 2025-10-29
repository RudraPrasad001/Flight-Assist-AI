import mariadb
import os
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

try:
    conn = mariadb.connect(
        user="root",
        password=os.getenv("DB_PASSWORD"),
        host="127.0.0.1",
        port=int(os.getenv("DB_PORT")),
        database="flightdb2"
    )
    print("Connected to MariaDB successfully!")
except mariadb.Error as e:
    print(f"Error connecting to MariaDB: {e}")
    exit(1)

cur = conn.cursor()

try:
    cur.execute("ALTER TABLE planes ADD COLUMN planes_embedding VECTOR(384)")
    conn.commit()
    print("Added planes_embedding column")
except mariadb.Error as e:
    if "Duplicate column" in str(e) or "already exists" in str(e):
        print("planes_embedding column already exists")
    else:
        print(f"Error adding column: {e}")

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
