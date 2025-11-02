# FlightAssist AI — MariaDB Hackathon 2025

AI‑driven flight search and analytics showcasing MariaDB 12.0 native Vector Search for semantic retrieval and ColumnStore for instant analytics on large flight datasets. Natural‑language queries, meaning‑aware results, interactive maps, and one‑click booking links.[1][2][11]

***

## Tech focus

MariaDB Vector, ColumnStore, HTAP, React + Leaflet front end, Python/TypeScript services.[2][11][1]

***

## Key Features

- Semantic flight search: Convert user prompts to 384‑dim embeddings and retrieve nearest routes/airports using cosine distance on MariaDB’s native VECTOR type with HNSW indexing.[1][2]
- Instant analytics: ColumnStore powers aggregates like flight counts by airline and average distances without impacting transactional workloads.[12]
- Interactive map: Visualize airports and flight paths using a clean React Leaflet interface for exploratory discovery.[13]
- One‑click booking: Deep links from result cards to external booking for immediate action.[13]

***

## Why MariaDB

- Native VECTOR data type, functions like VEC_FromText and VEC_DISTANCE_COSINE, and optimizer support for ORDER BY VEC_DISTANCE_* with LIMIT for efficient ANN search.[2][1]
- ColumnStore enables sub‑second scans and aggregates over large datasets for a unified OLTP + analytics pattern.[12]

***

## Architecture

- Data layer: MariaDB 12.0 with tables for airports, routes, and a VECTOR(384) column plus HNSW index for embeddings.[1][2]
- Query layer: ANN retrieval using cosine distance; ColumnStore for analytics queries.[2][12]
- App layer: Backend services in Python/TypeScript expose search and analytics endpoints; frontend in React + Leaflet renders maps and result cards.[13]

***

## Getting Started

### Prerequisites

- MariaDB 12.0 with Vector Search enabled and ColumnStore available.[4][11]
- Node.js (for frontend/services) and Python (for embedding/ingest).[13]
- Sentence Transformer model for 384‑dim embeddings (e.g., all‑MiniLM‑L6‑v2).[14]

### Setup

#### Database

- Create tables with VECTOR columns and HNSW index; install/enable ColumnStore.[12][1][2]
- Load airports/routes (e.g., OpenFlights) and compute embeddings for text fields like “source → destination” and airport descriptors.[12]

#### Backend

- Configure DB connection string and model path; provide endpoints:[1][2]
  - POST /search: accepts a natural‑language query, embeds it, returns top‑k routes/airports ordered by VEC_DISTANCE_COSINE.[1]
  - GET /analytics: returns aggregates (counts by airline, average distance, per‑country stats) via ColumnStore queries.[12]

#### Frontend

- Start React app; configure base API URL; render:[13]
  - Search bar, semantic results, deep links to booking, and a React Leaflet map of paths and airports.[13]

***

## Example SQL

```sql
-- Semantic table
CREATE TABLE routes_semantic (
  route_id BIGINT PRIMARY KEY,
  text_query VARCHAR(512),
  embedding VECTOR(384) NOT NULL,
  VECTOR INDEX (embedding) M=8 DISTANCE=cosine
);

-- Insert embedding from JSON-like text
INSERT INTO routes_semantic (route_id, text_query, embedding)
VALUES (1001, 'London to Delhi', VEC_FromText('[0.12, 0.03, ...]'));

-- ANN search (cosine)
SELECT route_id, text_query
FROM routes_semantic
ORDER BY VEC_DISTANCE_COSINE(
  embedding, VEC_FromText('[0.11, 0.02, ...]')
)
LIMIT 10;
```

### Analytics example (ColumnStore)

```sql
SELECT airline, AVG(distance_km) AS avg_km
FROM routes
GROUP BY airline
ORDER BY avg_km DESC
LIMIT 20;
```

***

## Performance Notes

- Nearest‑neighbor search uses HNSW vector index; MariaDB optimizer accelerates ORDER BY VEC_DISTANCE_* with LIMIT.[2]
- ColumnStore provides fast aggregates across large datasets with minimal impact on interactive queries.[12]

***

## Project Structure

```
backend/  — Python/TypeScript services for embedding, search, and analytics APIs
db/       — SQL DDL, sample data loaders, and config for Vector + ColumnStore
frontend/ — React + Leaflet UI with search, cards, map, and deep links
scripts/  — Data ingestion and embedding utilities
```

***

## Environment Variables

- DATABASE_URL: MariaDB connection string.[13]
- MODEL_NAME: Sentence Transformer model id.[14]
- TOP_K: Default semantic result size.[2]

***

## Development

- Run DB locally or via container; apply DDL and load sample data.[12]
- Start backend (Python/TS) with hot reload; configure model cache.[14]
- Start frontend; verify search, map rendering, analytics, and deep links.[13]

***

## Roadmap

- Real‑time flight status ingestion and streaming analytics.[13]
- Multilingual embeddings; richer airport/route metadata.[11]
- Hybrid geo + vector ranking for nearest alternates and hub routes.[13]

[1](https://mariadb.com/docs/server/reference/sql-structure/vectors/vector-overview)
[2](https://mariadb.org/projects/mariadb-vector/)
[3](https://mariadb.org/wp-content/uploads/2024/02/MariaDB-Vector.pdf)
[4](https://mariadb.com/resources/blog/announcing-mariadb-community-server-12-0-ga/)
[5](https://mariadb.org/vector-preview/)
[6](https://foss-north.se/2025/slides/rsilen-mariadb-vector-slides.pdf)
[7](https://mariadb.org/mariadb-vector-is-available-on-opea/)
[8](https://www.youtube.com/watch?v=XkB2DLK60JU)
[9](https://dzone.com/articles/mariadb-vector-edition-hands-on-review)
[10](http://smalldatum.blogspot.com/2025/01/evaluating-vector-indexes-in-mariadb.html)
[11](https://www.infoq.com/news/2025/06/mariadb-vector-search/)
[12](https://github.com/mariadb-corporation/dev-example-flights)
[13](https://www.youtube.com/watch?v=zv8pbwlCQRg)
[14](https://www.youtube.com/watch?v=gNyzcy_6qJM)
