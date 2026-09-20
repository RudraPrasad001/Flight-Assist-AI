# FlightAssist AI — Flight Data Analytics & AI Platform

**FlightAssist AI** is a data analytics and AI platform built on the **OpenFlights dataset**, combining large-scale SQL analytics with semantic search to explore global flight networks.

The project focuses on transforming raw aviation data into **actionable insights** around airlines, airports, routes, countries, flight distances, and network connectivity, while providing natural-language search for exploratory analysis.

Built for the **MariaDB Hackathon 2025**, the project demonstrates how **MariaDB ColumnStore, Vector Search, SQL analytics, Python, and interactive visualization** can work together in a single data platform.

---

## Project Overview

FlightAssist processes flight, airport, airline, and route data to answer analytical questions such as:

* Which airlines operate the largest number of routes?
* Which airports have the highest connectivity?
* What is the average route distance by airline or country?
* Which countries have the densest flight networks?
* Which routes connect major aviation hubs?
* What patterns exist in global flight connectivity?
* Can users explore the dataset using natural-language queries?

The system combines **structured analytics** with **semantic retrieval**, allowing users to move from quantitative analysis to exploratory search within the same platform.

---

## Data & Analytics Pipeline

```text
OpenFlights Dataset
        │
        ▼
Data Ingestion
        │
        ▼
Data Cleaning & Transformation
        │
        ▼
MariaDB
 ┌──────┴─────────┐
 │                │
 ▼                ▼
ColumnStore    Vector Search
 │                │
 ▼                ▼
SQL Analytics   Semantic Retrieval
 │                │
 └──────┬─────────┘
        ▼
FastAPI / Backend Services
        │
        ▼
Interactive Analytics Dashboard
        │
        ▼
Insights + Maps + Search
```

---

## Key Data Analytics Capabilities

### 1. Airline Analysis

Analyze airline operations across the dataset.

Example metrics:

* Total routes operated
* Number of destinations
* Average route distance
* Countries served
* Airport connectivity
* Route distribution

Example query:

```sql
SELECT
    airline,
    COUNT(*) AS total_routes,
    AVG(distance_km) AS average_distance
FROM routes
GROUP BY airline
ORDER BY total_routes DESC;
```

---

### 2. Airport Connectivity Analysis

Identify highly connected airports and aviation hubs.

```sql
SELECT
    airport_id,
    COUNT(*) AS route_count
FROM routes
GROUP BY airport_id
ORDER BY route_count DESC
LIMIT 20;
```

This allows the dataset to be explored as a **global transportation network** rather than simply as a collection of individual flights.

---

### 3. Route Distance Analysis

Analyze the distribution of flight distances across airlines, countries, and routes.

```sql
SELECT
    airline,
    AVG(distance_km) AS avg_distance_km,
    MIN(distance_km) AS shortest_route_km,
    MAX(distance_km) AS longest_route_km
FROM routes
GROUP BY airline
ORDER BY avg_distance_km DESC;
```

---

### 4. Country-Level Analysis

Aggregate flight connectivity by country to identify differences in aviation network density.

Example analytical dimensions:

```text
Country
 ├── Number of airports
 ├── Number of routes
 ├── Number of airlines
 ├── Average route distance
 └── International connectivity
```

These aggregations can be used to generate comparative visualizations and identify patterns in global air connectivity.

---

## Natural-Language Data Exploration

In addition to conventional SQL analytics, FlightAssist provides semantic search for exploratory analysis.

A natural-language query such as:

```text
"Find routes connecting major European cities to India"
```

is converted into a **384-dimensional embedding** using a Sentence Transformer model.

The embedding is stored in MariaDB's native `VECTOR` type and searched using cosine distance with an HNSW index.

```text
Natural-language query
        ↓
Sentence Transformer
        ↓
384-dimensional embedding
        ↓
MariaDB Vector Search
        ↓
Nearest routes / airports
        ↓
Analytical result
```

This allows users to explore aviation data without knowing the underlying database schema.

---

## Why Combine SQL Analytics and Vector Search?

The project demonstrates two complementary approaches to data exploration.

### Structured analytics

Best for questions such as:

```text
Which airline has the most routes?
What is the average distance?
Which airports have the highest connectivity?
How many routes exist between countries?
```

These are answered using **SQL and ColumnStore analytics**.

### Semantic exploration

Best for questions such as:

```text
Show me routes from major Asian hubs to Europe.
Find airports similar to Heathrow.
Find routes connecting large cities in South Asia.
```

These are handled using **vector similarity search**.

Together:

```text
Structured SQL
      +
Semantic Search
      ↓
Richer Data Exploration
```

---

# Interactive Analytics Dashboard

The React frontend provides an interactive interface for exploring the dataset.

### Analytics

Displays metrics such as:

```text
Total airlines
Total airports
Total routes
Average route distance
Top connected airports
Top airlines
Country-level connectivity
```

### Visual Exploration

Interactive maps display:

* Airports
* Flight routes
* Geographic connectivity
* Search results

The map allows users to move from aggregated statistics to individual geographic patterns.

---

# Technology Stack

### Data & Analytics

* **MariaDB ColumnStore** — analytical queries and aggregations
* **MariaDB Vector Search** — semantic retrieval
* **SQL** — analytical queries and data exploration
* **Python** — data ingestion, transformation, and embedding generation
* **Pandas** — dataset processing and transformation

### AI / Machine Learning

* Sentence Transformers
* Embeddings
* Vector similarity search
* HNSW approximate nearest-neighbor indexing

### Backend

* Python
* FastAPI
* REST APIs

### Frontend

* React
* Leaflet
* Interactive maps
* Data visualization

### Data

* OpenFlights dataset
* Airport metadata
* Airline metadata
* Route information

---

# Database Architecture

MariaDB acts as the central data platform.

```text
                    MariaDB
                       │
          ┌────────────┼─────────────┐
          │            │             │
          ▼            ▼             ▼
       Airports      Routes       Airlines
          │            │
          │            ▼
          │      Analytical Data
          │            │
          │            ▼
          │       ColumnStore
          │
          ▼
     Semantic Data
          │
          ▼
     VECTOR(384)
          │
          ▼
        HNSW
```

The architecture separates analytical workloads from semantic retrieval while keeping the data within the same database platform.

---

# Data Model

Core entities include:

```text
Airlines
    │
    ├── airline_id
    ├── name
    └── country

Airports
    │
    ├── airport_id
    ├── name
    ├── city
    ├── country
    ├── latitude
    └── longitude

Routes
    │
    ├── route_id
    ├── airline_id
    ├── source_airport
    ├── destination_airport
    └── distance_km
```

Semantic representations are maintained separately:

```sql
CREATE TABLE routes_semantic (
    route_id BIGINT PRIMARY KEY,
    text_query VARCHAR(512),
    embedding VECTOR(384) NOT NULL,
    VECTOR INDEX (embedding) M=8 DISTANCE=cosine
);
```

---

# Example Analytics Queries

## Top Airlines by Number of Routes

```sql
SELECT
    airline,
    COUNT(*) AS route_count
FROM routes
GROUP BY airline
ORDER BY route_count DESC
LIMIT 20;
```

## Average Distance by Airline

```sql
SELECT
    airline,
    AVG(distance_km) AS avg_distance_km
FROM routes
GROUP BY airline
ORDER BY avg_distance_km DESC;
```

## Most Connected Airports

```sql
SELECT
    source_airport,
    COUNT(*) AS outgoing_routes
FROM routes
GROUP BY source_airport
ORDER BY outgoing_routes DESC
LIMIT 20;
```

## Country-Level Connectivity

```sql
SELECT
    country,
    COUNT(DISTINCT airport_id) AS airports,
    COUNT(*) AS routes
FROM airports
JOIN routes
    ON airports.airport_id = routes.source_airport
GROUP BY country
ORDER BY routes DESC;
```

---

# Example Vector Search

Generate an embedding for the user's query:

```text
"Flights from London to major Indian cities"
```

Then perform nearest-neighbor retrieval:

```sql
SELECT
    route_id,
    text_query
FROM routes_semantic
ORDER BY VEC_DISTANCE_COSINE(
    embedding,
    VEC_FromText('[0.11, 0.02, ...]')
)
LIMIT 10;
```

The semantic layer enables natural-language exploration while the analytical layer provides exact numerical aggregation.

---

# Business / Analytical Use Cases

Although FlightAssist uses aviation data, the architecture demonstrates a general pattern applicable to data-intensive organizations:

### Operational Analytics

```text
Raw operational data
        ↓
Data transformation
        ↓
KPIs
        ↓
Trend analysis
        ↓
Operational decisions
```

### Data Exploration

```text
Natural-language question
        ↓
Semantic retrieval
        ↓
Relevant records
        ↓
Analytical investigation
```

### Decision Support

```text
Data
 ↓
Analysis
 ↓
Pattern identification
 ↓
Visualization
 ↓
Actionable insight
```

---

# Getting Started

## Prerequisites

* MariaDB 12.0+
* MariaDB Vector Search
* MariaDB ColumnStore
* Python 3.x
* Node.js
* Sentence Transformers
* OpenFlights dataset

---

## Database Setup

Create the required analytical and semantic tables.

Enable:

```text
MariaDB Vector Search
MariaDB ColumnStore
```

Load the OpenFlights dataset and perform the required transformations.

Generate embeddings for relevant route and airport descriptions.

---

## Backend

Configure:

```env
DATABASE_URL=<mariadb-connection-string>
MODEL_NAME=all-MiniLM-L6-v2
TOP_K=10
```

Example endpoints:

```text
POST /search

GET /analytics

GET /airlines

GET /airports

GET /routes
```

---

## Frontend

Start the React application and configure the backend API URL.

The dashboard provides:

```text
Analytics
Search
Maps
Route exploration
Airline analysis
Airport analysis
```

---

# Project Structure

```text
backend/
├── api/
├── analytics/
├── search/
└── services/

db/
├── schema/
├── migrations/
└── queries/

scripts/
├── ingestion/
├── transformation/
└── embeddings/

frontend/
├── components/
├── dashboard/
├── maps/
└── search/
```

---

# Performance Considerations

### Analytical workloads

MariaDB ColumnStore is used for analytical aggregation over large datasets.

Typical operations include:

```text
GROUP BY
COUNT
AVG
MIN / MAX
DISTINCT
Filtering
Multi-dimensional aggregation
```

### Semantic workloads

Vector Search uses:

```text
VECTOR(384)
HNSW indexing
Cosine distance
Top-K retrieval
```

This allows semantic retrieval without requiring a separate vector database.

---

# Key Takeaways

FlightAssist demonstrates an end-to-end **Data + AI workflow**:

```text
              DATA
               │
               ▼
        Ingestion & Cleaning
               │
               ▼
          Data Modeling
               │
        ┌──────┴──────┐
        ▼             ▼
   SQL Analytics   Embeddings
        │             │
        ▼             ▼
   Aggregations   Vector Search
        │             │
        └──────┬──────┘
               ▼
        Data Exploration
               │
               ▼
       Visualization
               │
               ▼
      Actionable Insights
```

The project combines **data engineering, SQL analytics, machine learning/embeddings, AI-assisted search, and interactive visualization** into a single analytical platform.

---

# Future Improvements

* Add time-series flight data for trend analysis.
* Introduce real-time streaming ingestion and analytics.
* Add anomaly detection for unusual route or airport activity.
* Build predictive models for route demand.
* Add automated insight generation from analytical results.
* Add multilingual semantic search.
* Introduce hybrid geographic + semantic ranking.
* Add an analytics layer for route-network centrality and connectivity metrics.

---

## References

* [MariaDB Vector Documentation](https://mariadb.com/docs/server/reference/sql-structure/vectors/vector-overview)
* [MariaDB Vector](https://mariadb.org/projects/mariadb-vector/)
* [MariaDB 12.0](https://mariadb.com/resources/blog/announcing-mariadb-community-server-12-0-ga/)
* [MariaDB Flight Example](https://github.com/mariadb-corporation/dev-example-flights)
* [MariaDB Vector Search Information](https://www.infoq.com/news/2025/06/mariadb-vector-search/)
* [OpenFlights Dataset](https://openflights.org/data.php)
