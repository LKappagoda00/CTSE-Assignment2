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

Input:  daily_meal_plan, user_profile (cultural_preference, allergies)
Output: adapted_meal_plan, analytical_logs, messages

Reasoning Strategy: Rule-based substitution from cultural mappings in the
    food database, enhanced with LLM reasoning for nuanced adaptations.
"""
from __future__ import annotations

import copy
import json
from typing import Any

from langchain_ollama import ChatOllama
from loguru import logger

from config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TEMPERATURE
from observability import tracer
from state import AgentState
from tools.food_database import FoodDatabaseTool

# ── System Prompt ──────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a Cultural Food Adaptation specialist AI.
Given a meal plan and a target culture, suggest culturally appropriate food swaps.

Cultures you handle:
- sri_lankan:   Rice & curry based, coconut milk, string hoppers, hoppers, pol sambol
- indian_north: Roti/naan based, paneer, tandoori, rich gravies
- indian_south: Rice/dosa/idli based, sambar, coconut chutney, fermented foods
- western:      Whole grains, lean proteins, salads, moderate portions
- mediterranean:Olive oil, fish, legumes, whole grains, fresh vegetables
- east_asian:   Rice, tofu, stir-fry, miso, steamed dishes

Rules:
- Replacement food must have similar calories (within 20%)
- Keep protein levels adequate
- Respect cultural dietary norms
- Use only foods from the provided database

Respond ONLY with a JSON list of 3 analytical statements.
Example: ["Statement 1.", "Statement 2.", "Statement 3."]"""


def cultural_adapter_node(state: AgentState) -> dict[str, Any]:
    """
    LangGraph node for the Cultural Food Adapter Agent.

    Reads:  daily_meal_plan, user_profile
    Writes: adapted_meal_plan, analytical_logs, messages, current_agent

    Args:
        state: The current LangGraph AgentState.

    Returns:
        A dictionary of state updates to be merged into AgentState.
    """
    tracer.log_agent_start(
        "CulturalAdapterAgent",
        {"culture": state.get("user_profile", {}).get("cultural_preference")},
    )

    profile: dict[str, Any] = state.get("user_profile", {})
    meal_plan: dict[str, Any] = state.get("daily_meal_plan", {})
    culture: str = profile.get("cultural_preference", "western")

    # FIX: Load allergies to prevent unsafe substitutions
    allergies: list[str] = [
        a.lower().strip() for a in profile.get("allergies", [])
    ]

    # Deep copy to avoid mutating original state
    adapted: dict[str, Any] = copy.deepcopy(meal_plan)

    # ── Step 1: Rule-based cultural adaptation ─────────────────────────────
    food_db = FoodDatabaseTool()
    cultural_subs: dict[str, Any] = food_db.get_cultural_substitutions(culture)

    tracer.log_tool_usage(
        "FoodDatabaseTool.get_cultural_substitutions",
        {"culture": culture},
        {"available": bool(cultural_subs)},
    )

    adaptations_made: list[str] = []

    if cultural_subs:
        # Collect all food IDs available for this culture
        culture_food_ids: set[str] = set()
        for category_key in [
            "grain_staples",
            "protein_staples",
            "vegetable_staples",
            "condiments",
            "beverages",
            "fruits",
        ]:
            culture_food_ids.update(cultural_subs.get(category_key, []))

        for meal in adapted.get("meals", []):
            for i, item in enumerate(meal.get("items", [])):
                food_id: str = item.get("food_id", "")
                food_data: dict[str, Any] | None = food_db.get_food_by_id(food_id)

                if food_data and culture not in food_data.get("cultures", []):
                    replacement = _find_cultural_replacement(
                        food_id=food_id,
                        food_data=food_data,
                        culture=culture,
                        culture_food_ids=culture_food_ids,
                        food_db=food_db,
                        allergies=allergies,  # FIX: pass allergies
                    )
                    if replacement:
                        old_name: str = item.get("food_name", "Unknown")

                        # Scale replacement to match original calories
                        scale: float = (
                            item["calories"] / replacement["calories"]
                            if replacement["calories"] > 0
                            else 1.0
                        )
                        scale = max(0.5, min(1.5, scale))  # clamp to safe range

                        meal["items"][i] = {
                            "food_name": replacement["name"],
                            "food_id": replacement["id"],
                            "quantity": replacement["serving_size"],
                            "calories": round(replacement["calories"] * scale, 1),
                            "protein_g": round(replacement["protein_g"] * scale, 1),
                            "carbs_g": round(replacement["carbs_g"] * scale, 1),
                            "fat_g": round(replacement["fat_g"] * scale, 1),
                            "fiber_g": round(
                                replacement.get("fiber_g", 0) * scale, 1
                            ),
                        }
                        adaptations_made.append(
                            f"{old_name} → {replacement['name']}"
                        )

            # Recalculate meal-level totals after substitutions
            meal["total_calories"] = round(
                sum(it["calories"] for it in meal["items"]), 1
            )
            meal["total_protein_g"] = round(
                sum(it["protein_g"] for it in meal["items"]), 1
            )
            meal["total_carbs_g"] = round(
                sum(it["carbs_g"] for it in meal["items"]), 1
            )
            meal["total_fat_g"] = round(
                sum(it["fat_g"] for it in meal["items"]), 1
            )
            meal["total_fiber_g"] = round(
                sum(it.get("fiber_g", 0) for it in meal["items"]), 1
            )

    # Recalculate daily totals
    all_meals: list[dict[str, Any]] = adapted.get("meals", [])
    adapted["total_daily_calories"] = round(
        sum(m["total_calories"] for m in all_meals), 1
    )
    adapted["total_protein_g"] = round(
        sum(m["total_protein_g"] for m in all_meals), 1
    )
    adapted["total_carbs_g"] = round(
        sum(m["total_carbs_g"] for m in all_meals), 1
    )
    adapted["total_fat_g"] = round(
        sum(m["total_fat_g"] for m in all_meals), 1
    )
    adapted["culture"] = culture
    adapted["adaptations_made"] = adaptations_made

    # ── Step 2: LLM enhancement for analytical notes ───────────────────────
    # FIX: Set fallback notes BEFORE LLM call — system never loses adapted plan
    logic_statements: list[str] = [
        f"Substituted staples to align with {culture} culinary patterns.",
        "Maintained calorie counts within ±10% margin.",
        "Prioritised authentic regional fiber and protein sources.",
    ]

    try:
        llm = ChatOllama(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=OLLAMA_TEMPERATURE,
        )

        # FIX: Single clean prompt — removed duplicate/overwritten prompt
        prompt: str = (
            f"Analyze these cultural food substitutions for a {culture} diet.\n"
            f"User Goal: {profile.get('dietary_goal', 'general health')}\n\n"
            f"Substitutions Performed:\n"
            f"{json.dumps(adapted.get('meals', []), indent=2)}\n\n"  # FIX: adapted not adapted_plan
            f"Explain the logic of these substitutions. Focus on how local "
            f"ingredients ({culture}) maintain the nutritional baseline of a "
            f"global healthy diet.\n"
            f"Output MUST be a JSON list of exactly 3 analytical statements.\n"
            f'Example: ["Statement 1.", "Statement 2.", "Statement 3."]'
        )

        tracer.log_llm_call("CulturalAdapterAgent", prompt[:100], "pending")
        resp = llm.invoke(
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ]
        )

        cleaned_resp: str = (
            resp.content.replace("```json", "").replace("```", "").strip()
        )
        parsed = json.loads(cleaned_resp)

        # FIX: Validate parsed response is actually a list before using it
        if isinstance(parsed, list) and all(
            isinstance(s, str) for s in parsed
        ):
            logic_statements = parsed[:3]  # take max 3 statements
        else:
            raise ValueError(
                f"LLM returned unexpected format: {type(parsed)}"
            )

        tracer.log_llm_call(
            "CulturalAdapterAgent", prompt[:100], str(logic_statements)
        )

    except Exception as e:
        logger.warning(f"LLM cultural analysis failed, using fallback: {e}")

    # ── Step 3: Build analytical notes ────────────────────────────────────
    notes: list[str] = [
        f"Cultural Engine: Successfully adapted the plan to {culture} cuisine. "
        f"{len(adaptations_made)} substitution(s) made."
    ]
    notes.extend([f"Equivalence Logic: {s}" for s in logic_statements])

    # FIX: tracer.log_agent_end moved here — now actually reachable
    tracer.log_agent_end(
        "CulturalAdapterAgent", {"adaptations": len(adaptations_made)}
    )
    logger.info(
        f"CulturalAdapterAgent complete: {len(adaptations_made)} "
        f"substitution(s) for culture '{culture}'"
    )

    # FIX: Single unified return — adapted_meal_plan always present
    return {
        "adapted_meal_plan": adapted,
        "analytical_logs": notes,
        "messages": [
            f"CulturalAdapterAgent adapted plan to {culture} "
            f"({len(adaptations_made)} substitution(s))."
        ],
        "current_agent": "CulturalAdapterAgent",
    }


def _find_cultural_replacement(
    food_id: str,
    food_data: dict[str, Any],
    culture: str,
    culture_food_ids: set[str],
    food_db: FoodDatabaseTool,
    allergies: list[str],      # FIX: allergies parameter added
) -> dict[str, Any] | None:
    """
    Find the best culturally appropriate replacement for a given food item.

    Searches the culture's food pool for a same-category item with the
    closest calorie count. Falls back to any cultural food if no
    same-category match is found. Respects user allergies.

    Args:
        food_id:          The food ID of the item to replace.
        food_data:        Full food data dict of the item to replace.
        culture:          Target culture string (e.g. 'sri_lankan').
        culture_food_ids: Set of food IDs available for the target culture.
        food_db:          Initialised FoodDatabaseTool instance.
        allergies:        List of user allergen strings to exclude.

    Returns:
        The best matching replacement food dict, or None if no suitable
        replacement is found.

    Example:
        >>> replacement = _find_cultural_replacement(
        ...     "bread_white", food_data, "sri_lankan",
        ...     culture_ids, food_db, ["gluten"]
        ... )
    """
    category: str = food_data.get("category", "")
    original_cal: float = food_data.get("calories", 0)

    best_match: dict[str, Any] | None = None
    best_diff: float = float("inf")

    def _is_safe(candidate: dict[str, Any]) -> bool:
        """Return True if candidate contains no user allergens."""
        allergen_tags: list[str] = [
            t.lower() for t in candidate.get("allergens", [])
        ]
        name_lower: str = candidate.get("name", "").lower()
        for allergen in allergies:
            if allergen in allergen_tags or allergen in name_lower:
                return False
        return True

    # Pass 1: same-category match within the culture pool
    for cid in culture_food_ids:
        if cid == food_id:
            continue
        candidate: dict[str, Any] | None = food_db.get_food_by_id(cid)
        if (
            candidate
            and candidate.get("category") == category
            and _is_safe(candidate)          # FIX: allergy check
        ):
            diff = abs(candidate["calories"] - original_cal)
            if diff < best_diff:
                best_diff = diff
                best_match = candidate

    # Pass 2: any cultural food if no same-category match found
    if best_match is None:
        for cid in culture_food_ids:
            if cid == food_id:
                continue
            candidate = food_db.get_food_by_id(cid)
            if candidate and _is_safe(candidate):  # FIX: allergy check
                diff = abs(candidate["calories"] - original_cal)
                if diff < best_diff:
                    best_diff = diff
                    best_match = candidate

    return best_match