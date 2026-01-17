import uvicorn
from fastapi import FastAPI

from routers.user import router as user_router
from routers.nutrition import router as nutrition_router
# from routers.parser import router as parser_router
from routers.insights import router as insights_router
from routers.memory import router as memory_router
from routers.chat import router as chat_router
from routers.symptoms import router as symptoms_router
from routers.NearbyHospital import locRouter as hospital_router
from routers.NearbyFoodOutlet import router as food_outlet_router

app = FastAPI()

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

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}



if __name__ == "__main__":
    uvicorn.run(app, host="10.156.65.50", port=8000)