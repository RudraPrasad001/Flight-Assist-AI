import mariadb
import os
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("sentence_transformers not installed. Install with: pip install sentence-transformers")
    exit(1)
from dotenv import load_dotenv

load_dotenv()

# Debug: Print connection parameters
db_password = os.getenv("DB_PASSWORD")
print(f"Attempting to connect with password: {'*' * len(db_password) if db_password else 'None'}")

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
    print("Please check:")
    print("1. MariaDB service is running")
    print("2. Password is correct in .env file") 
    print("3. Database 'flightdb2' exists")
    print("4. User 'root' has access to the database")
    exit(1)
cur = conn.cursor()

# Add airports_embedding column if it doesn't exist
try:
    cur.execute("ALTER TABLE airports ADD COLUMN airports_embedding VECTOR(384)")
    conn.commit()  # Commit the DDL statement
    print("Added airports_embedding column")
except mariadb.Error as e:
    if "Duplicate column" in str(e) or "already exists" in str(e):
        print("airports_embedding column already exists")
    else:
        print(f"Error adding column: {e}")
        # Let's check if the column exists
        cur.execute("DESCRIBE airports")
        columns = cur.fetchall()
        print("Existing columns:", [col[0] for col in columns])

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
