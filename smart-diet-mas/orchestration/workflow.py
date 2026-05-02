"""
LangGraph Orchestration Workflow

Defines the multi-agent workflow as a directed graph using LangGraph.
Each node is an agent, and edges define the execution order.

Workflow:
    ┌─────────────────┐
    │   START          │
    │   (raw_input)    │
    └────────┬────────┘
             │
    ┌────────▼────────┐
    │ UserProfileAgent │  Validates input, calculates BMI/TDEE
    └────────┬────────┘
             │
    ┌────────▼─────────────┐
    │ NutritionPlannerAgent│  Generates meal plan using tools + LLM
    └────────┬─────────────┘
             │
    ┌────────▼──────────────┐
    │ CulturalAdapterAgent  │  Adapts meals to cultural preferences
    └────────┬──────────────┘
             │
    ┌────────▼──────────────┐
    │ CalorieAnalyzerAgent  │  Validates & exports final plan
    └────────┬──────────────┘
             │
    ┌────────▼────────┐
    │      END         │
    └─────────────────┘
"""
from __future__ import annotations
from loguru import logger
from langgraph.graph import StateGraph, END
from state import AgentState
from agents.user_profile_agent import user_profile_node
from agents.nutrition_planner_agent import nutrition_planner_node
from agents.cultural_adapter_agent import cultural_adapter_node
from agents.calorie_analyzer_agent import calorie_analyzer_node


def build_workflow() -> StateGraph:
    """
    Build and compile the LangGraph multi-agent workflow.

    Returns:
        Compiled LangGraph StateGraph ready for invocation.
    """
    logger.info("Building LangGraph workflow...")

    # Create the state graph
    workflow = StateGraph(AgentState)

    # ── Add Agent Nodes ────────────────────────────────────────────────────
    workflow.add_node("user_profile_agent", user_profile_node)
    workflow.add_node("nutrition_planner_agent", nutrition_planner_node)
    workflow.add_node("cultural_adapter_agent", cultural_adapter_node)
    workflow.add_node("calorie_analyzer_agent", calorie_analyzer_node)

    # ── Define Edges (Execution Order) ─────────────────────────────────────
    workflow.set_entry_point("user_profile_agent")
    workflow.add_edge("user_profile_agent", "nutrition_planner_agent")
    workflow.add_edge("nutrition_planner_agent", "cultural_adapter_agent")
    workflow.add_edge("cultural_adapter_agent", "calorie_analyzer_agent")
    workflow.add_edge("calorie_analyzer_agent", END)

    # ── Compile ────────────────────────────────────────────────────────────
    compiled = workflow.compile()
    logger.info("LangGraph workflow compiled successfully")
    return compiled


def run_workflow(user_input: dict) -> dict:
    """
    Execute the complete multi-agent workflow.

    Args:
        user_input: Dictionary with user data:
            - name (str)
            - age (int)
            - gender (str)
            - weight_kg (float)
            - height_cm (float)
            - activity_level (str)
            - dietary_goal (str)
            - allergies (list[str])
            - cultural_preference (str)

    Returns:
        Final state dictionary with all agent outputs.
    """
    logger.info("=" * 60)
    logger.info("Starting Smart Diet MAS Workflow")
    logger.info("=" * 60)

    # Initialize state
    initial_state: AgentState = {
        "raw_input": user_input,
        "user_profile": None,
        "bmi_result": None,
        "target_calories": None,
        "daily_meal_plan": None,
        "adapted_meal_plan": None,
        "calorie_analysis": None,
        "final_report": None,
        "messages": [],
        "errors": [],
        "current_agent": None,
        "export_path": None,
    }

    # Build and run workflow
    app = build_workflow()
    final_state = app.invoke(initial_state)

    logger.info("=" * 60)
    logger.info("Workflow Complete!")
    logger.info("=" * 60)

    return final_state
