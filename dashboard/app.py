from fastapi import FastAPI, Request
from users.routers import router as user_router
from events.routers import router as event_router
from participants.routers import router as participant_router
from roles.routers import router as roles_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from exception import APIError

app = FastAPI()
app.include_router(user_router,prefix="/user",tags=["Users"])
app.include_router(event_router,prefix="/event",tags=["Events"])
app.include_router(participant_router,prefix="/participant",tags=["Participants"])
app.include_router(roles_router,prefix="/role", tags=["Roles"])
origins = [
    "http://localhost",
    "http://localhost:5173", 
    "http://127.0.0.1:3000", 
    "http://192.168.1.190:5173"
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

@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    return JSONResponse(
        status_code=exc.http_code,
        content=exc.as_response()
    )