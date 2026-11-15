import os

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from routers.user import router as user_router
from routers.nutrition import router as nutrition_router
# from routers.parser import router as parser_router
from routers.insights import router as insights_router
from routers.memory import router as memory_router
from routers.chat import router as chat_router
from routers.symptoms import router as symptoms_router
from routers.NearbyHospital import locRouter as hospital_router
from routers.NearbyFoodOutlet import router as food_outlet_router
from routers.MealPlanner import meal_router

app = FastAPI(title="CareNest API")

# CORS - required for the web build to call this API from a browser
_default_origins = "http://localhost:8081,http://localhost:19006,http://127.0.0.1:8081,http://127.0.0.1:19006"
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", _default_origins).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(user_router)
app.include_router(nutrition_router)
# app.include_router(parser_router)
app.include_router(insights_router)
app.include_router(memory_router)
app.include_router(chat_router)
app.include_router(symptoms_router)
app.include_router(hospital_router)
app.include_router(food_outlet_router)
app.include_router(meal_router)


@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
    )
