"""
User Profile Agent

Role: Collects, validates, and structures user data into a standardized profile.
Calculates BMI and determines caloric targets.

System Prompt:
    You are the User Profile Agent. Your role is to validate user health data,
    calculate BMI, and determine daily caloric needs. You must ensure all inputs
    are within safe medical ranges and flag any anomalies.

Input:  raw_input dict with user-provided data
Output: user_profile (validated JSON), bmi_result, target_calories

Reasoning Strategy: Rule-based validation + deterministic calculations.
    This agent does NOT need LLM calls — it uses pure Python logic for
    accurate medical calculations.

    NOTE: SYSTEM_PROMPT is documented here for architecture clarity and
    future LLM-based extension. This agent intentionally uses deterministic
    Python logic instead of LLM calls to ensure 100% accurate medical
    calculations with zero hallucination risk.
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from observability import tracer
from state import AgentState
from tools.bmi_calculator import (
    calculate_bmi,
    calculate_bmr,
    calculate_target_calories,
    calculate_tdee,
    calculate_water_intake,
)

# ── System Prompt (documented for architecture clarity) ────────────────────────
SYSTEM_PROMPT = """You are the User Profile Agent in a multi-agent nutrition system.

Your responsibilities:
1. Validate all user input fields (age, weight, height, gender, goal)
2. Reject or flag values outside safe medical ranges
3. Calculate BMI, BMR, TDEE, and target daily calories
4. Output a structured JSON profile for downstream agents

Constraints:
- Age must be 10-120 years
- Weight must be 20-500 kg
- Height must be 50-300 cm
- Gender must be male/female/other
- Goal must be one of: weight_loss, muscle_gain, maintenance, healthy_eating
- Activity level must be one of: sedentary, lightly_active, moderately_active,
  very_active, extra_active
- Cultural preference must be supported

You must NEVER provide medical advice. Only calculate and validate."""


VALID_GOALS = {"weight_loss", "muscle_gain", "maintenance", "healthy_eating"}
VALID_GENDERS = {"male", "female", "other"}
VALID_ACTIVITIES = {
    "sedentary",
    "lightly_active",
    "moderately_active",
    "very_active",
    "extra_active",
}
VALID_CULTURES = {
    "sri_lankan",
    "indian_north",
    "indian_south",
    "western",
    "mediterranean",
    "east_asian",
}


def validate_input(raw: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """
    Validate raw user input and return cleaned data + error list.

    Args:
        raw: Dictionary of raw user-provided input fields.

    Returns:
        A tuple of:
            - cleaned (dict): Validated and sanitized user data.
            - errors (list[str]): List of validation warning messages.

    Example:
        >>> cleaned, errors = validate_input({"age": 25, "weight_kg": 70, "height_cm": 175})
    """
    errors: list[str] = []
    cleaned: dict[str, Any] = {}

    # Name
    name = str(raw.get("name", "User")).strip()
    cleaned["name"] = name if name else "User"

    # Age
    try:
        age = int(raw.get("age", 0))
        if age < 10 or age > 120:
            errors.append(f"Age {age} outside valid range (10-120)")
        cleaned["age"] = max(10, min(120, age))
    except (ValueError, TypeError):
        errors.append(f"Invalid age: {raw.get('age')}")
        cleaned["age"] = 25

    # Gender
    gender = str(raw.get("gender", "other")).lower().strip()
    if gender not in VALID_GENDERS:
        errors.append(f"Invalid gender '{gender}', defaulting to 'other'")
        gender = "other"
    cleaned["gender"] = gender

    # Weight
    try:
        weight = float(raw.get("weight_kg", 0))
        if weight < 20 or weight > 500:
            errors.append(f"Weight {weight}kg outside range (20-500)")
        cleaned["weight_kg"] = max(20.0, min(500.0, weight))
    except (ValueError, TypeError):
        errors.append(f"Invalid weight: {raw.get('weight_kg')}")
        cleaned["weight_kg"] = 70.0

    # Height
    try:
        height = float(raw.get("height_cm", 0))
        if height < 50 or height > 300:
            errors.append(f"Height {height}cm outside range (50-300)")
        cleaned["height_cm"] = max(50.0, min(300.0, height))
    except (ValueError, TypeError):
        errors.append(f"Invalid height: {raw.get('height_cm')}")
        cleaned["height_cm"] = 170.0

    # Activity level
    activity = str(raw.get("activity_level", "moderately_active")).lower().strip()
    if activity not in VALID_ACTIVITIES:
        errors.append(f"Invalid activity '{activity}', defaulting to 'moderately_active'")
        activity = "moderately_active"
    cleaned["activity_level"] = activity

    # Dietary goal
    goal = str(raw.get("dietary_goal", "maintenance")).lower().strip()
    if goal not in VALID_GOALS:
        errors.append(f"Invalid goal '{goal}', defaulting to 'maintenance'")
        goal = "maintenance"
    cleaned["dietary_goal"] = goal

    # Allergies
    allergies = raw.get("allergies", [])
    if isinstance(allergies, str):
        allergies = [a.strip() for a in allergies.split(",") if a.strip()]
    cleaned["allergies"] = allergies

    # Cultural preference
    culture = str(raw.get("cultural_preference", "western")).lower().strip()
    if culture not in VALID_CULTURES:
        errors.append(f"Unsupported culture '{culture}', defaulting to 'western'")
        culture = "western"
    cleaned["cultural_preference"] = culture

    return cleaned, errors


def user_profile_node(state: AgentState) -> dict[str, Any]:
    """
    LangGraph node function for the User Profile Agent.

    Reads:  state['raw_input']
    Writes: user_profile, bmi_result, target_calories, hydration_target,
            analytical_logs, messages, errors, current_agent

    Args:
        state: The current LangGraph AgentState.

    Returns:
        A dictionary of state updates to be merged into AgentState.
    """
    tracer.log_agent_start("UserProfileAgent", state.get("raw_input", {}))

    raw_input: dict[str, Any] = state.get("raw_input", {})
    profile, validation_errors = validate_input(raw_input)

    # ── Calculate BMI ──────────────────────────────────────────────────────
    bmi_input = {"weight": profile["weight_kg"], "height": profile["height_cm"]}
    bmi_result = calculate_bmi(profile["weight_kg"], profile["height_cm"])
    tracer.log_tool_usage("calculate_bmi", bmi_input, bmi_result)  # FIX: log after result

    # ── Calculate BMR → TDEE → Target Calories ─────────────────────────────
    bmr = calculate_bmr(
        profile["weight_kg"],
        profile["height_cm"],
        profile["age"],
        profile["gender"],
    )
    tracer.log_tool_usage(
        "calculate_bmr",
        {"weight": profile["weight_kg"], "age": profile["age"]},
        {"bmr": bmr},  # FIX: log actual bmr value not empty dict
    )

    tdee = calculate_tdee(bmr, profile["activity_level"])
    target = calculate_target_calories(tdee, profile["dietary_goal"])

    # ── Calculate Hydration Target ─────────────────────────────────────────
    hydration = calculate_water_intake(profile["weight_kg"], profile["activity_level"])

    tracer.log_agent_end(
        "UserProfileAgent", {"target_calories": target, "hydration": hydration}
    )
    logger.info(
        f"UserProfileAgent complete: {profile['name']}, "
        f"target {target} kcal, hydration {hydration}L"
    )

    return {
        "user_profile": profile,
        "bmi_result": bmi_result,           # FIX: was bmi_res (NameError)
        "target_calories": target,
        "hydration_target": hydration,
        "analytical_logs": [
            f"Metabolic Analysis: Based on weight ({profile['weight_kg']}kg) and "
            f"activity ({profile['activity_level']}), your BMR is {round(bmr)}kcal, "
            f"TDEE is {round(tdee)}kcal. A daily intake of {target}kcal is recommended "
            f"to achieve {profile['dietary_goal'].replace('_', ' ')}."
        ],
        "messages": [f"UserProfileAgent calculated metrics for {profile['name']}."],
        "errors": validation_errors,        # FIX: was 'errors' (NameError)
        "current_agent": "UserProfileAgent",
    }