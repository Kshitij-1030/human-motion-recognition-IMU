from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
import json

app = FastAPI()

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store latest sensor data
latest_data = {"x": 0, "y": 0, "z": 0, "timestamp": 0}

class SensorData(BaseModel):
    x: float
    y: float
    z: float
    timestamp: float

@app.post("/api/sensor")
async def receive_sensor_data(request: Request):
    global latest_data
    try:
        body = await request.json()
        
        # Parse if it's a string
        if isinstance(body, str):
            body = json.loads(body)
        
        print(f"Parsed body: {body}")
        
        data = SensorData(**body)
        latest_data = data.model_dump()
        print(f"Received: x={data.x:.2f}, y={data.y:.2f}, z={data.z:.2f}, t={data.timestamp:.2f}")
        return {"status": "success"}
    except Exception as e:
        print(f"Error: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/api/sensor")
async def get_sensor_data():
    return latest_data

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)