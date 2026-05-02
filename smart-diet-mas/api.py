"""
FastAPI Server for Smart Diet & Nutrition MAS.
Bridges the LangGraph multi-agent workflow to a web frontend.
"""
from __future__ import annotations
from typing import Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from loguru import logger

from orchestration.workflow import run_workflow
from config import SUPPORTED_CULTURES

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
    height_cm: float = Field(gt=50, lt=300, default=170)
    activity_level: str = Field(default="moderately_active")
    dietary_goal: str = Field(default="maintenance")
    allergies: list[str] = Field(default_factory=list)
    cultural_preference: str = Field(default="western")

# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"status": "online", "message": "Smart Diet MAS API is active"}

@app.get("/cultures")
async def get_cultures():
    return {"cultures": SUPPORTED_CULTURES}

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
        
        # Return the final state
        # Note: We filter out internal objects if necessary, but LangGraph state
        # is generally JSON serializable if we use dicts/lists.
        return result_state
        
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
