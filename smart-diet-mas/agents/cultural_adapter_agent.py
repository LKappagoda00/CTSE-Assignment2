"""
Cultural Food Adapter Agent

Role: Adapts the generated meal plan to match cultural and regional food
      preferences. Replaces generic foods with culturally appropriate alternatives
      while maintaining nutritional targets.

System Prompt:
    You are the Cultural Food Adapter Agent. Given a meal plan and a target
    culture, replace food items with culturally appropriate alternatives.
    Maintain similar calorie counts and macronutrient profiles. Use the
    food database's cultural substitution mappings.

Input:  daily_meal_plan, user_profile (cultural_preference)
Output: adapted_meal_plan

Reasoning Strategy: Rule-based substitution from cultural mappings in the
    food database, enhanced with LLM reasoning for nuanced adaptations.
"""
from __future__ import annotations
import json
import copy
from loguru import logger
from langchain_ollama import ChatOllama
from state import AgentState
from tools.food_database import FoodDatabaseTool
from observability import tracer
from config import OLLAMA_MODEL, OLLAMA_BASE_URL, OLLAMA_TEMPERATURE

SYSTEM_PROMPT = """You are a Cultural Food Adaptation specialist AI. 
Given a meal plan and a target culture, suggest culturally appropriate food swaps.

Cultures you handle:
- sri_lankan: Rice & curry based, coconut milk, string hoppers, hoppers, pol sambol
- indian_north: Roti/naan based, paneer, tandoori, rich gravies
- indian_south: Rice/dosa/idli based, sambar, coconut chutney, fermented foods
- western: Whole grains, lean proteins, salads, moderate portions
- mediterranean: Olive oil, fish, legumes, whole grains, fresh vegetables
- east_asian: Rice, tofu, stir-fry, miso, steamed dishes

Rules:
- Replacement food must have similar calories (within 20%)
- Keep protein levels adequate
- Respect cultural dietary norms
- Use only foods from the provided database

Respond ONLY with JSON: {"adaptations": [{"original": "food_id", "replacement": "food_id", "reason": "..."}]}"""


def cultural_adapter_node(state: AgentState) -> dict:
    """
    LangGraph node for the Cultural Food Adapter Agent.

    Reads: daily_meal_plan, user_profile
    Writes: adapted_meal_plan, messages
    """
    tracer.log_agent_start("CulturalAdapterAgent", {
        "culture": state.get("user_profile", {}).get("cultural_preference"),
    })

    profile = state.get("user_profile", {})
    meal_plan = state.get("daily_meal_plan", {})
    culture = profile.get("cultural_preference", "western")

    # Deep copy to avoid mutating original
    adapted = copy.deepcopy(meal_plan)

    # ── Step 1: Rule-based cultural adaptation ────────────────────────────
    food_db = FoodDatabaseTool()
    cultural_subs = food_db.get_cultural_substitutions(culture)

    tracer.log_tool_usage("FoodDatabaseTool.get_cultural_substitutions", {"culture": culture}, 
                          {"available": bool(cultural_subs)})

    adaptations_made = []

    if cultural_subs:
        # Get all food IDs available for this culture
        culture_food_ids = set()
        for category_key in ["grain_staples", "protein_staples", "vegetable_staples", 
                             "condiments", "beverages", "fruits"]:
            culture_food_ids.update(cultural_subs.get(category_key, []))

        for meal in adapted.get("meals", []):
            for i, item in enumerate(meal.get("items", [])):
                food_id = item.get("food_id", "")
                
                # Check if the food belongs to the target culture
                food_data = food_db.get_food_by_id(food_id)
                if food_data and culture not in food_data.get("cultures", []):
                    # Find a replacement from the same category
                    replacement = _find_cultural_replacement(
                        food_id, food_data, culture, culture_food_ids, food_db
                    )
                    if replacement:
                        old_name = item["food_name"]
                        # Scale to match similar calories
                        scale = item["calories"] / replacement["calories"] if replacement["calories"] > 0 else 1.0
                        scale = max(0.5, min(1.5, scale))

                        meal["items"][i] = {
                            "food_name": replacement["name"],
                            "food_id": replacement["id"],
                            "quantity": replacement["serving_size"],
                            "calories": round(replacement["calories"] * scale, 1),
                            "protein_g": round(replacement["protein_g"] * scale, 1),
                            "carbs_g": round(replacement["carbs_g"] * scale, 1),
                            "fat_g": round(replacement["fat_g"] * scale, 1),
                            "fiber_g": round(replacement.get("fiber_g", 0) * scale, 1),
                        }
                        adaptations_made.append(f"{old_name} → {replacement['name']}")

            # Recalculate meal totals
            meal["total_calories"] = round(sum(it["calories"] for it in meal["items"]), 1)
            meal["total_protein_g"] = round(sum(it["protein_g"] for it in meal["items"]), 1)
            meal["total_carbs_g"] = round(sum(it["carbs_g"] for it in meal["items"]), 1)
            meal["total_fat_g"] = round(sum(it["fat_g"] for it in meal["items"]), 1)
            meal["total_fiber_g"] = round(sum(it.get("fiber_g", 0) for it in meal["items"]), 1)

    # Recalculate daily totals
    all_meals = adapted.get("meals", [])
    adapted["total_daily_calories"] = round(sum(m["total_calories"] for m in all_meals), 1)
    adapted["total_protein_g"] = round(sum(m["total_protein_g"] for m in all_meals), 1)
    adapted["total_carbs_g"] = round(sum(m["total_carbs_g"] for m in all_meals), 1)
    adapted["total_fat_g"] = round(sum(m["total_fat_g"] for m in all_meals), 1)
    adapted["culture"] = culture
    adapted["adaptations_made"] = adaptations_made

    # ── Step 2: LLM enhancement for cultural notes ────────────────────────
    # Skip LLM for now to avoid issues
    tracer.log_agent_end("CulturalAdapterAgent", {"adaptations": len(adaptations_made)})
    return {
        "adapted_meal_plan": adapted,
        "analytical_logs": [f"Cultural Engine: Adapted to {culture} cuisine with {len(adaptations_made)} substitutions."],
        "messages": [f"CulturalAdapterAgent adapted plan to {culture}."],
        "current_agent": "CulturalAdapterAgent"
    }


def _find_cultural_replacement(food_id: str, food_data: dict, culture: str,
                                culture_food_ids: set, food_db: FoodDatabaseTool) -> dict | None:
    """Find a culturally appropriate replacement food."""
    category = food_data.get("category", "")
    original_cal = food_data.get("calories", 0)

    best_match = None
    best_diff = float("inf")

    for cid in culture_food_ids:
        if cid == food_id:
            continue
        candidate = food_db.get_food_by_id(cid)
        if candidate and candidate.get("category") == category:
            diff = abs(candidate["calories"] - original_cal)
            if diff < best_diff:
                best_diff = diff
                best_match = candidate

    # If no same-category match, try any cultural food
    if best_match is None:
        for cid in culture_food_ids:
            candidate = food_db.get_food_by_id(cid)
            if candidate:
                diff = abs(candidate["calories"] - original_cal)
                if diff < best_diff:
                    best_diff = diff
                    best_match = candidate

    return best_match
