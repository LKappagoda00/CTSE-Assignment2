from __future__ import annotations
import operator
from typing import Annotated, Any, Optional, TypedDict
from pydantic import BaseModel, Field

# ── Pydantic Models for State Validation ───────────────────────────────────────

class FoodItem(BaseModel):
    food_id: str
    food_name: str
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    quantity: str
    category: str

class Meal(BaseModel):
    meal_type: str
    items: list[FoodItem]
    total_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float

class MealPlan(BaseModel):
    meals: list[Meal]
    total_daily_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    culture: str
    cultural_tips: list[str] = Field(default_factory=list)

# ── Global Agent State Definition ──────────────────────────────────────────────

class AgentState(TypedDict):
    """
    The Global State object passed between agents in the LangGraph workflow.
    Uses Annotated[list, operator.add] to allow messages and logs to accumulate.
    """
    # ── User Input ──
    raw_input: dict[str, Any]
    
    # ── User Profile Agent Outputs ──
    user_profile: Optional[dict[str, Any]]
    bmi_result: Optional[dict[str, Any]]
    target_calories: Optional[float]
    hydration_target: Optional[float]

    # ── Nutrition Planner Agent Outputs ──
    daily_meal_plan: Optional[dict[str, Any]]

    # ── Cultural Adapter Agent Outputs ──
    adapted_meal_plan: Optional[dict[str, Any]]

    # ── Calorie Analyzer Agent Outputs ──
    calorie_analysis: Optional[dict[str, Any]]
    final_report: Optional[str]
    
    # ── Intelligence & Analytics ──
    # This key uses operator.add to ensure notes from all agents are preserved
    analytical_logs: Annotated[list[str], operator.add] 

    # ── Metadata ──
    messages: Annotated[list[str], operator.add]  # Execution trace log
    errors: Annotated[list[str], operator.add]    # Error log
    current_agent: Optional[str]                  # Name of the active agent
    export_path: Optional[str]                    # Internal path to the saved file
