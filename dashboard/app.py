from fastapi import FastAPI
from users.routers import router as user_router
from events.routers import router as event_router
from participants.routers import router as participant_router
from testrouters import router as test_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.include_router(user_router,prefix="/user",tags=["Users"])
app.include_router(event_router,prefix="/event",tags=["Events"])
app.include_router(participant_router,prefix="/participant",tags=["Participants"])
app.include_router(test_router, prefix="/test",tags=["Test"])

origins = [
    "http://localhost",
    "http://localhost:5173", 
    "http://127.0.0.1:3000", 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # allow these domains to access your API
    allow_credentials=True,
    allow_methods=["*"],         # allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],         # allow all headers
)

@app.get("/health")
async def health_check():
    return "API Working"
