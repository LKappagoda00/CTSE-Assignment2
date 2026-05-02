"""
BMI Calculator Tool

Calculates Body Mass Index (BMI) from height and weight,
and returns the BMI value along with its health category.

WHO BMI Categories:
    - Underweight: < 18.5
    - Normal weight: 18.5 – 24.9
    - Overweight: 25 – 29.9
    - Obese Class I: 30 – 34.9
    - Obese Class II: 35 – 39.9
    - Obese Class III: >= 40
"""

from __future__ import annotations

from loguru import logger


def calculate_bmi(weight_kg: float, height_cm: float) -> dict[str, any]:
    """
    Calculate Body Mass Index (BMI) and return categorized result.

    Args:
        weight_kg: Body weight in kilograms. Must be > 0.
        height_cm: Height in centimeters. Must be > 0.

    Returns:
        A dictionary containing:
            - bmi_value (float): The calculated BMI rounded to 1 decimal
            - category (str): WHO BMI category
            - interpretation (str): Human-friendly health interpretation
            - weight_kg (float): Input weight
            - height_cm (float): Input height

    Raises:
        ValueError: If weight or height is non-positive or unrealistic.

    Example:
        >>> calculate_bmi(70, 175)
        {'bmi_value': 22.9, 'category': 'normal', ...}
    """
    # ── Input Validation ───────────────────────────────────────────────────
    if not isinstance(weight_kg, (int, float)):
        raise TypeError(f"weight_kg must be numeric, got {type(weight_kg).__name__}")
    if not isinstance(height_cm, (int, float)):
        raise TypeError(f"height_cm must be numeric, got {type(height_cm).__name__}")

    if weight_kg <= 0:
        raise ValueError(f"Weight must be positive, got {weight_kg} kg")
    if height_cm <= 0:
        raise ValueError(f"Height must be positive, got {height_cm} cm")

    if weight_kg < 20 or weight_kg > 500:
        logger.warning(f"Unusual weight value: {weight_kg} kg — proceeding with caution")
    if height_cm < 50 or height_cm > 300:
        logger.warning(f"Unusual height value: {height_cm} cm — proceeding with caution")

    # ── BMI Calculation ────────────────────────────────────────────────────
    height_m = height_cm / 100.0
    bmi_value = round(weight_kg / (height_m ** 2), 1)

    # ── Categorization ─────────────────────────────────────────────────────
    if bmi_value < 18.5:
        category = "underweight"
        interpretation = (
            f"BMI of {bmi_value} is classified as Underweight. "
            "Consider a calorie-surplus diet to reach a healthy weight."
        )
    elif 18.5 <= bmi_value < 25.0:
        category = "normal"
        interpretation = (
            f"BMI of {bmi_value} is within the Normal range. "
            "Maintain a balanced diet and regular physical activity."
        )
    elif 25.0 <= bmi_value < 30.0:
        category = "overweight"
        interpretation = (
            f"BMI of {bmi_value} is classified as Overweight. "
            "A moderate calorie deficit with exercise is recommended."
        )
    elif 30.0 <= bmi_value < 35.0:
        category = "obese_class_1"
        interpretation = (
            f"BMI of {bmi_value} is classified as Obese (Class I). "
            "A structured weight-loss plan with medical guidance is advised."
        )
    elif 35.0 <= bmi_value < 40.0:
        category = "obese_class_2"
        interpretation = (
            f"BMI of {bmi_value} is classified as Obese (Class II). "
            "Professional medical and dietary intervention is strongly recommended."
        )
    else:
        category = "obese_class_3"
        interpretation = (
            f"BMI of {bmi_value} is classified as Obese (Class III — Severe). "
            "Immediate consultation with healthcare professionals is critical."
        )

    result = {
        "bmi_value": bmi_value,
        "category": category,
        "interpretation": interpretation,
        "weight_kg": weight_kg,
        "height_cm": height_cm,
    }

    logger.info(f"BMI calculated: {bmi_value} ({category}) for {weight_kg}kg / {height_cm}cm")
    return result


def calculate_bmr(
    weight_kg: float,
    height_cm: float,
    age: int,
    gender: str,
) -> float:
    """
    Calculate Basal Metabolic Rate (BMR) using the Mifflin-St Jeor equation.

    Args:
        weight_kg: Body weight in kilograms.
        height_cm: Height in centimeters.
        age: Age in years.
        gender: 'male' or 'female'.

    Returns:
        BMR in kilocalories per day.

    Raises:
        ValueError: If inputs are invalid.
    """
    if age <= 0 or age > 120:
        raise ValueError(f"Age must be between 1 and 120, got {age}")

    gender = gender.lower().strip()
    if gender not in ("male", "female", "other"):
        raise ValueError(f"Gender must be 'male', 'female', or 'other', got '{gender}'")

    # Mifflin-St Jeor Equation
    bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age
    if gender == "male":
        bmr += 5
    else:
        bmr -= 161  # For female and other

    logger.info(f"BMR calculated: {bmr:.0f} kcal/day for {gender}, age {age}")
    return round(bmr, 0)


def calculate_tdee(bmr: float, activity_level: str) -> float:
    """
    Calculate Total Daily Energy Expenditure (TDEE).

    Args:
        bmr: Basal Metabolic Rate in kcal/day.
        activity_level: One of 'sedentary', 'lightly_active',
                        'moderately_active', 'very_active', 'extra_active'.

    Returns:
        TDEE in kcal/day.
    """
    from config import DEFAULT_ACTIVITY_MULTIPLIER

    activity_level = activity_level.lower().strip()
    if activity_level not in DEFAULT_ACTIVITY_MULTIPLIER:
        logger.warning(f"Unknown activity level '{activity_level}', defaulting to 'moderately_active'")
        activity_level = "moderately_active"

    multiplier = DEFAULT_ACTIVITY_MULTIPLIER[activity_level]
    tdee = round(bmr * multiplier, 0)

    logger.info(f"TDEE calculated: {tdee:.0f} kcal/day (activity: {activity_level}, multiplier: {multiplier})")
    return tdee


def calculate_target_calories(tdee: float, goal: str) -> float:
    """
    Adjust TDEE based on dietary goal to get target daily calories.

    Args:
        tdee: Total Daily Energy Expenditure.
        goal: 'weight_loss', 'muscle_gain', 'maintenance', or 'healthy_eating'.

    Returns:
        Target daily calorie intake.
    """
    goal = goal.lower().strip()
    adjustments = {
        "weight_loss": -500,       # ~0.45 kg/week loss
        "muscle_gain": +300,       # Lean bulk surplus
        "maintenance": 0,
        "healthy_eating": 0,
    }

    if goal not in adjustments:
        logger.warning(f"Unknown goal '{goal}', defaulting to 'maintenance'")
        goal = "maintenance"

    target = round(tdee + adjustments[goal], 0)
    target = max(target, 1200)  # Safety floor: never below 1200 kcal

    logger.info(f"Target calories: {target:.0f} kcal/day (goal: {goal}, TDEE: {tdee:.0f})")
    return target
