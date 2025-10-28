import mariadb
import os
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

try:
    conn = mariadb.connect(
        user="root",
        password=os.getenv("DB_PASSWORD"),  # Direct password
        host="127.0.0.1", # or use localhost da
        port=os.getenv("DB_PORT"),  # Correct MariaDB port
        database="flightdb2"
    )
    print("Connected to MariaDB successfully!")
except mariadb.Error as e:
    print(f"Error connecting to MariaDB: {e}")
    exit(1)
cur = conn.cursor()

# Add airlines_embedding column if it doesn't exist
try:
    cur.execute("ALTER TABLE airlines ADD COLUMN airlines_embedding VECTOR(384)")
    conn.commit()  # Commit the DDL statement
    print("Added airlines_embedding column")
except mariadb.Error as e:
    if "Duplicate column" in str(e) or "already exists" in str(e):
        print("airlines_embedding column already exists")
    else:
        print(f"Error adding column: {e}")

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
