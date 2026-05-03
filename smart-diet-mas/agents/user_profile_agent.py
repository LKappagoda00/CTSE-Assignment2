"""
User Profile Agent

Role: Collects, validates, and structures user data into a standardized profile.
Calculates BMI and determines caloric targets.

System Prompt:
    You are the User Profile Agent. Your role is to validate user health data,
    calculate BMI, and determine daily caloric needs. You must ensure all inputs
    are within safe medical ranges and flag any anomalies.

Input:  raw_input dict with user-provided data including name, age, gender, weight_kg, height_cm (required for BMI), activity_level, dietary_goal, allergies, cultural_preference, medical_conditions, dietary_restrictions, preferred_foods, disliked_foods, budget_per_day, cooking_time_available
Output: user_profile (validated JSON), bmi_result, target_calories

Reasoning Strategy: Rule-based validation + deterministic calculations.
    This agent does NOT need LLM calls — it uses pure Python logic for
    accurate medical calculations.
"""
from __future__ import annotations
from loguru import logger
from state import AgentState
from tools.bmi_calculator import calculate_bmi, calculate_bmr, calculate_tdee, calculate_target_calories
from observability import tracer


# ── System Prompt (for documentation / LLM-based extension) ───────────────────
SYSTEM_PROMPT = """You are the User Profile Agent in a multi-agent nutrition system.

Your responsibilities:
1. Validate all user input fields (age, weight, height, gender, goal)
2. Reject or flag values outside safe medical ranges
3. Calculate BMI, BMR, TDEE, and target daily calories
4. Output a structured JSON profile for downstream agents

Constraints:
- Age must be 10-120 years
- Weight must be 20-500 kg
- Height must be 50-300 cm (required for BMI calculation)
- Gender must be male/female/other
- Goal must be one of: weight_loss, muscle_gain, maintenance, healthy_eating
- Activity level must be one of: sedentary, lightly_active, moderately_active, very_active, extra_active
- Cultural preference must be supported
- Dietary restrictions must be from: vegetarian, vegan, gluten_free, dairy_free, keto, paleo, low_carb, high_protein
- Cooking time must be quick/moderate/extensive

You must NEVER provide medical advice. Only calculate and validate."""


VALID_GOALS = {"weight_loss", "muscle_gain", "maintenance", "healthy_eating"}
VALID_GENDERS = {"male", "female", "other"}
VALID_ACTIVITIES = {"sedentary", "lightly_active", "moderately_active", "very_active", "extra_active"}
VALID_CULTURES = {"sri_lankan", "indian_north", "indian_south", "western", "mediterranean", "east_asian"}
VALID_DIETARY_RESTRICTIONS = {"vegetarian", "vegan", "gluten_free", "dairy_free", "keto", "paleo", "low_carb", "high_protein"}
VALID_COOKING_TIMES = {"quick", "moderate", "extensive"}


def validate_input(raw: dict) -> tuple[dict, list[str]]:
    """Validate raw user input and return cleaned data + error list."""
    errors = []
    cleaned = {}

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
        cleaned["weight_kg"] = max(20, min(500, weight))
    except (ValueError, TypeError):
        errors.append(f"Invalid weight: {raw.get('weight_kg')}")
        cleaned["weight_kg"] = 70.0

    # Height
    try:
        height = float(raw.get("height_cm", 0))
        if height < 50 or height > 300:
            errors.append(f"Height {height}cm outside range (50-300)")
        cleaned["height_cm"] = max(50, min(300, height))
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

    # Medical conditions
    medical_conditions = raw.get("medical_conditions", [])
    if isinstance(medical_conditions, str):
        medical_conditions = [c.strip() for c in medical_conditions.split(",") if c.strip()]
    cleaned["medical_conditions"] = medical_conditions

    # Dietary restrictions
    dietary_restrictions = raw.get("dietary_restrictions", [])
    if isinstance(dietary_restrictions, str):
        dietary_restrictions = [r.strip().lower() for r in dietary_restrictions.split(",") if r.strip()]
    invalid_restrictions = [r for r in dietary_restrictions if r not in VALID_DIETARY_RESTRICTIONS]
    if invalid_restrictions:
        errors.append(f"Invalid dietary restrictions: {invalid_restrictions}, ignoring them")
        dietary_restrictions = [r for r in dietary_restrictions if r in VALID_DIETARY_RESTRICTIONS]
    cleaned["dietary_restrictions"] = dietary_restrictions

    # Preferred foods
    preferred_foods = raw.get("preferred_foods", [])
    if isinstance(preferred_foods, str):
        preferred_foods = [f.strip() for f in preferred_foods.split(",") if f.strip()]
    cleaned["preferred_foods"] = preferred_foods

    # Disliked foods
    disliked_foods = raw.get("disliked_foods", [])
    if isinstance(disliked_foods, str):
        disliked_foods = [f.strip() for f in disliked_foods.split(",") if f.strip()]
    cleaned["disliked_foods"] = disliked_foods

    # Budget per day
    try:
        budget = float(raw.get("budget_per_day", 0))
        if budget < 0:
            errors.append(f"Budget {budget} cannot be negative")
            budget = 0
        cleaned["budget_per_day"] = budget
    except (ValueError, TypeError):
        errors.append(f"Invalid budget: {raw.get('budget_per_day')}")
        cleaned["budget_per_day"] = 0.0

    # Cooking time available
    cooking_time = str(raw.get("cooking_time_available", "moderate")).lower().strip()
    if cooking_time not in VALID_COOKING_TIMES:
        errors.append(f"Invalid cooking time '{cooking_time}', defaulting to 'moderate'")
        cooking_time = "moderate"
    cleaned["cooking_time_available"] = cooking_time

    return cleaned, errors


def user_profile_node(state: AgentState) -> dict:
    """
    LangGraph node function for the User Profile Agent.

    Reads: state['raw_input']
    Writes: user_profile, bmi_result, target_calories, messages, errors
    """
    tracer.log_agent_start("UserProfileAgent", state.get("raw_input", {}))

    raw_input = state.get("raw_input", {})
    profile, validation_errors = validate_input(raw_input)

    # Calculate BMI
    tracer.log_tool_usage("calculate_bmi", {"weight": profile["weight_kg"], "height": profile["height_cm"]}, {})
    bmi_result = calculate_bmi(profile["weight_kg"], profile["height_cm"])

    # Calculate BMR → TDEE → Target Calories
    bmr = calculate_bmr(profile["weight_kg"], profile["height_cm"], profile["age"], profile["gender"])
    tracer.log_tool_usage("calculate_bmr", {"weight": profile["weight_kg"], "age": profile["age"]}, bmr)

    tdee = calculate_tdee(bmr, profile["activity_level"])
    target = calculate_target_calories(tdee, profile["dietary_goal"])
    
    tracer.log_agent_end("UserProfileAgent", {"target": target})
    logger.info(f"UserProfileAgent complete: {profile['name']}, target {target} kcal")
    
    return {
        "user_profile": profile,
        "bmi_result": bmi_result,
        "target_calories": target,
        "analytical_logs": [
            f"Metabolic Analysis: Based on weight ({profile['weight_kg']}kg) and activity ({profile['activity_level']}), "
            f"your BMR is {round(bmr)}kcal, TDEE is {round(tdee)}kcal. A daily intake of {target}kcal is recommended "
            f"to achieve {profile['dietary_goal'].replace('_', ' ')}."
        ],
        "messages": [f"UserProfileAgent calculated metrics for {profile['name']}."],
        "errors": validation_errors,
        "current_agent": "UserProfileAgent",
    }
