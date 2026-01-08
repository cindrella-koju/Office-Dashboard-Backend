from fastapi import FastAPI
from users.routers import router as user_router
from events.routers import router as event_router

app = FastAPI()
app.include_router(user_router,prefix="/user",tags=["Users"])
app.include_router(event_router,prefix="/event",tags=["Events"])

@app.get("/health")
async def health_check():
    return "API Working"
