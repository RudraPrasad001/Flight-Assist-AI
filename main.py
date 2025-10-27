from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import your routers
from routers.test_router import router as example_router

app = FastAPI(
    title="My FastAPI Application",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(example_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Welcome to FastAPI!"}
