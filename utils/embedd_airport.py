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

cur.execute("SELECT apid, CONCAT(name, ', ', city, ', ', country) AS combined_text FROM airports")
rows = cur.fetchall()

for row_id, text in rows:
    embedding_vector = model.encode(text).tolist()
    vector_str = "[" + ",".join(map(str, embedding_vector)) + "]"

    # Use VEC_FromText to convert string to VECTOR
    sql = "UPDATE airports SET airports_embedding = VEC_FromText(?) WHERE apid = ?"
    cur.execute(sql, (vector_str, row_id))

conn.commit()
cur.close()
conn.close()
