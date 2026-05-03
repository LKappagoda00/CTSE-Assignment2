"""
FastAPI Server for Smart Diet & Nutrition MAS.
Bridges the LangGraph multi-agent workflow to a web frontend.
"""
from __future__ import annotations
from typing import Any
import json
import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from loguru import logger

from orchestration.workflow import run_workflow
from config import SUPPORTED_CULTURES

# Create data directory if it doesn't exist
DATA_DIR = "saved_data"
os.makedirs(DATA_DIR, exist_ok=True)

app = FastAPI(
    title="Smart Diet MAS API",
    description="API for the Multi-Agent Diet & Nutrition System",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request Models ─────────────────────────────────────────────────────────────

class UserInput(BaseModel):
    name: str = Field(default="User", examples=["Kasun Perera"])
    age: int = Field(ge=10, le=120, default=25)
    gender: str = Field(default="male", pattern="^(male|female|other)$")
    weight_kg: float = Field(gt=20, lt=500, default=70)
    height_cm: float = Field(gt=50, lt=300)  # Required for BMI calculation
    activity_level: str = Field(default="moderately_active")
    dietary_goal: str = Field(default="maintenance")
    allergies: list[str] = Field(default_factory=list)
    cultural_preference: str = Field(default="western")
    medical_conditions: list[str] = Field(default_factory=list, examples=[["diabetes", "hypertension"]])
    dietary_restrictions: list[str] = Field(default_factory=list, examples=[["vegetarian", "vegan", "gluten_free"]])
    preferred_foods: list[str] = Field(default_factory=list, examples=[["chicken", "rice", "vegetables"]])
    disliked_foods: list[str] = Field(default_factory=list, examples=[["spinach", "fish"]])
    budget_per_day: float = Field(default=0, ge=0, examples=[50.0])
    cooking_time_available: str = Field(default="moderate", examples=["quick", "moderate", "extensive"])

# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/cultures")
async def get_cultures():
    """
    Returns the list of supported cultures.
    """
    return {"cultures": SUPPORTED_CULTURES}

@app.get("/past-data")
async def get_past_data():
    """
    Returns a list of all saved plan data.
    """
    try:
        files = [f for f in os.listdir(DATA_DIR) if f.endswith('.json')]
        past_data = []
        for file in sorted(files, reverse=True):  # Most recent first
            with open(os.path.join(DATA_DIR, file), 'r') as f:
                data = json.load(f)
                past_data.append({
                    "id": file,
                    "timestamp": data["timestamp"],
                    "user_name": data["user_input"]["name"],
                    "dietary_goal": data["user_input"]["dietary_goal"],
                    "target_calories": data["result"].get("target_calories"),
                    "bmi": data["result"].get("bmi_result", {}).get("bmi_value")
                })
        return {"past_data": past_data}
    except Exception as e:
        logger.error(f"Failed to load past data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/past-data/{plan_id}")
async def get_past_data_detail(plan_id: str):
    """
    Returns detailed data for a specific plan.
    """
    try:
        filepath = os.path.join(DATA_DIR, plan_id)
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="Plan not found")
        with open(filepath, 'r') as f:
            data = json.load(f)
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to load plan detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-plan")
async def generate_plan(user_input: UserInput):
    """
    Triggers the multi-agent workflow and returns the complete result.
    """
    logger.info(f"Received web request for user: {user_input.name}")
    try:
        # Convert Pydantic model to dict
        input_data = user_input.model_dump()
        
        # Run the workflow
        result_state = run_workflow(input_data)
        
        # Save the result
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{DATA_DIR}/plan_{user_input.name.replace(' ', '_')}_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump({
                "timestamp": timestamp,
                "user_input": input_data,
                "result": result_state
            }, f, indent=2)
        logger.info(f"Saved plan data to {filename}")
        
        # Return the final state
        return result_state
        
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
