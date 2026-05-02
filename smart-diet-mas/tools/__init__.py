"""
Custom Python tools for the Smart Diet & Nutrition MAS.

Tools:
    - BMI Calculator: Computes BMI and categorizes health status
    - Food Database: Queries local food database for nutritional info
    - Meal Plan Generator: Creates structured meal plans
    - File Export: Saves plans as .txt or .json
"""

from tools.bmi_calculator import calculate_bmi
from tools.food_database import FoodDatabaseTool
from tools.meal_plan_generator import MealPlanGeneratorTool
from tools.file_export import FileExportTool

__all__ = [
    "calculate_bmi",
    "FoodDatabaseTool",
    "MealPlanGeneratorTool",
    "FileExportTool",
]
