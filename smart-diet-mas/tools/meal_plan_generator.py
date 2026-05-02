"""
Meal Plan Generator Tool

Creates structured daily meal plans by selecting appropriate foods
from the database to meet target calorie and macronutrient goals.

Calorie distribution:
    - Breakfast: 25%  |  Lunch: 35%  |  Dinner: 30%  |  Snack: 10%
"""
from __future__ import annotations
import random
from typing import Optional
from loguru import logger
from tools.food_database import FoodDatabaseTool
from config import MACRO_RATIOS

MEAL_DISTRIBUTION = {"breakfast": 0.25, "lunch": 0.35, "dinner": 0.30, "snack": 0.10}

class MealPlanGeneratorTool:
    """Generates structured daily meal plans using the food database."""

    def __init__(self, food_db: Optional[FoodDatabaseTool] = None) -> None:
        self._food_db = food_db or FoodDatabaseTool()
        logger.info("MealPlanGeneratorTool initialized")

    def generate_daily_plan(self, target_calories: float, dietary_goal: str,
                            culture: str = "western", allergies: Optional[list[str]] = None,
                            day_number: int = 1) -> dict:
        """Generate a complete daily meal plan.

        Args:
            target_calories: Target daily calorie intake (800-6000).
            dietary_goal: weight_loss | muscle_gain | maintenance | healthy_eating.
            culture: Cultural food preference identifier.
            allergies: List of food allergies to avoid.
            day_number: Day number in the meal plan.
        Returns:
            Dictionary representing the daily meal plan.
        Raises:
            ValueError: If target_calories is outside valid range.
        """
        if target_calories < 800 or target_calories > 6000:
            raise ValueError(f"Target calories must be 800-6000, got {target_calories}")
        allergies = [a.lower() for a in (allergies or [])]
        available = self._food_db.get_foods_by_culture(culture)
        if not available:
            logger.warning(f"No foods for '{culture}', fallback to 'western'")
            available = self._food_db.get_foods_by_culture("western")
        if allergies:
            available = [f for f in available if not any(a in f["name"].lower() for a in allergies)]
        by_cat = {}
        for f in available:
            by_cat.setdefault(f.get("category", "other"), []).append(f)
        meals, totals = [], {"cal": 0, "p": 0, "c": 0, "f": 0, "fi": 0}
        for mtype, frac in MEAL_DISTRIBUTION.items():
            meal = self._build_meal(mtype, target_calories * frac, by_cat)
            meals.append(meal)
            totals["cal"] += meal["total_calories"]
            totals["p"] += meal["total_protein_g"]
            totals["c"] += meal["total_carbs_g"]
            totals["f"] += meal["total_fat_g"]
            totals["fi"] += meal.get("total_fiber_g", 0)
        plan = {"day": day_number, "meals": meals,
                "total_daily_calories": round(totals["cal"], 1),
                "total_protein_g": round(totals["p"], 1),
                "total_carbs_g": round(totals["c"], 1),
                "total_fat_g": round(totals["f"], 1),
                "total_fiber_g": round(totals["fi"], 1),
                "target_calories": target_calories, "culture": culture,
                "dietary_goal": dietary_goal}
        logger.info(f"Day {day_number}: {plan['total_daily_calories']} kcal (target: {target_calories})")
        return plan

    def _build_meal(self, meal_type: str, target_cal: float, by_cat: dict) -> dict:
        """Build a single meal from available food categories."""
        items, cur = [], 0.0
        if meal_type == "breakfast":
            comps = [("grains", 1), ("protein", 1), ("fruit", 1), ("beverage", 1)]
        elif meal_type in ("lunch", "dinner"):
            comps = [("grains", 1), ("protein", 1), ("vegetable", 1), ("condiment", 0.5)]
        else:
            comps = [("fruit", 1), ("snack", 0.7)]
        for cat, prob in comps:
            if random.random() > prob:
                continue
            foods = by_cat.get(cat, [])
            if not foods:
                for alt in ["protein", "grains", "vegetable", "fruit"]:
                    if alt != cat and alt in by_cat:
                        foods = by_cat[alt]; break
            if not foods:
                continue
            rem = target_cal - cur
            ok = [f for f in foods if f["calories"] <= rem + 50] or foods
            sel = random.choice(ok)
            scale = min(1.0, rem / sel["calories"]) if sel["calories"] > rem and rem > 0 else 1.0
            scale = max(scale, 0.5)
            item = {"food_name": sel["name"], "food_id": sel["id"],
                    "quantity": sel["serving_size"] if scale >= 0.9 else f"~{int(scale*100)}% of {sel['serving_size']}",
                    "calories": round(sel["calories"] * scale, 1),
                    "protein_g": round(sel["protein_g"] * scale, 1),
                    "carbs_g": round(sel["carbs_g"] * scale, 1),
                    "fat_g": round(sel["fat_g"] * scale, 1),
                    "fiber_g": round(sel.get("fiber_g", 0) * scale, 1)}
            items.append(item); cur += item["calories"]
        return {"meal_type": meal_type, "items": items,
                "total_calories": round(sum(i["calories"] for i in items), 1),
                "total_protein_g": round(sum(i["protein_g"] for i in items), 1),
                "total_carbs_g": round(sum(i["carbs_g"] for i in items), 1),
                "total_fat_g": round(sum(i["fat_g"] for i in items), 1),
                "total_fiber_g": round(sum(i["fiber_g"] for i in items), 1)}

    def generate_weekly_plan(self, target_calories: float, dietary_goal: str,
                             culture: str = "western", allergies: Optional[list[str]] = None) -> list[dict]:
        """Generate a 7-day meal plan."""
        return [self.generate_daily_plan(target_calories, dietary_goal, culture, allergies, d) for d in range(1, 8)]
