from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import confluence, onboarding

# TODO: maybe add rate limiting later? 
# not sure if we need it for internal tool but better safe than sorry
app = FastAPI(
    title="Eddie - Onboarding API",
    description="Because reading confluence docs shouldn't feel like homework",
    version="0.1.0"
)

# CORS - allowing frontend to talk to us
# TODO: lock this down before prod (currently too permissive)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # vite runs on 5173, CRA on 3000
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check - because everyone needs one
@app.get("/")
async def root():
    return {"message": "Eddie is alive and well 👋", "status": "running"}

@app.get("/health")
async def health_check():
    # TODO: actually check if confluence is reachable
    return {"status": "healthy", "service": "onboarding-api"}

# Include routers
app.include_router(confluence.router, prefix="/api/confluence", tags=["confluence"])
app.include_router(onboarding.router, prefix="/api/onboarding", tags=["onboarding"])

# Run with: uvicorn app.main:app --reload
# Don't forget the --reload flag or you'll be restarting manually like a caveman
