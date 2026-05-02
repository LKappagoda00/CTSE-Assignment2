"""
Testing & Evaluation Suite for the Smart Diet & Nutrition MAS.

Tests cover:
    1. Tool validation (BMI calculator, food database, meal generator, file export)
    2. Agent output validation (each agent's input/output contract)
    3. Edge cases (invalid input, extreme BMI, missing data)
    4. Integration test (full workflow end-to-end)
    5. Rule-based evaluation (nutritional correctness checks)
"""
from __future__ import annotations
import json
import os
import sys
import pytest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.bmi_calculator import calculate_bmi, calculate_bmr, calculate_tdee, calculate_target_calories
from tools.food_database import FoodDatabaseTool
from tools.meal_plan_generator import MealPlanGeneratorTool
from tools.file_export import FileExportTool


# ══════════════════════════════════════════════════════════════════════════════
# 1. BMI CALCULATOR TOOL TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestBMICalculator:
    """Tests for the BMI Calculator tool."""

    def test_normal_bmi(self):
        """Normal BMI range (18.5-24.9)."""
        result = calculate_bmi(70, 175)
        assert result["category"] == "normal"
        assert 18.5 <= result["bmi_value"] < 25.0

    def test_underweight_bmi(self):
        """Underweight BMI (< 18.5)."""
        result = calculate_bmi(45, 175)
        assert result["category"] == "underweight"
        assert result["bmi_value"] < 18.5

    def test_overweight_bmi(self):
        """Overweight BMI (25-29.9)."""
        result = calculate_bmi(90, 175)
        assert result["category"] == "overweight"
        assert 25.0 <= result["bmi_value"] < 30.0

    def test_obese_bmi(self):
        """Obese BMI (>= 30)."""
        result = calculate_bmi(120, 170)
        assert result["bmi_value"] >= 30.0
        assert "obese" in result["category"]

    def test_extreme_low_weight(self):
        """Edge case: very low weight."""
        result = calculate_bmi(25, 170)
        assert result["category"] == "underweight"
        assert "bmi_value" in result

    def test_extreme_high_weight(self):
        """Edge case: very high weight."""
        result = calculate_bmi(250, 170)
        assert result["bmi_value"] >= 40
        assert result["category"] == "obese_class_3"

    def test_invalid_zero_weight(self):
        """Edge case: zero weight should raise ValueError."""
        with pytest.raises(ValueError):
            calculate_bmi(0, 170)

    def test_invalid_negative_height(self):
        """Edge case: negative height should raise ValueError."""
        with pytest.raises(ValueError):
            calculate_bmi(70, -5)

    def test_invalid_type(self):
        """Edge case: string input should raise TypeError."""
        with pytest.raises(TypeError):
            calculate_bmi("seventy", 170)

    def test_bmi_result_structure(self):
        """Verify output dictionary structure."""
        result = calculate_bmi(70, 175)
        assert "bmi_value" in result
        assert "category" in result
        assert "interpretation" in result
        assert "weight_kg" in result
        assert "height_cm" in result


class TestBMR:
    """Tests for BMR calculation."""

    def test_male_bmr(self):
        """BMR for a standard male."""
        bmr = calculate_bmr(70, 175, 25, "male")
        assert 1500 < bmr < 2000

    def test_female_bmr(self):
        """BMR for a standard female."""
        bmr = calculate_bmr(60, 165, 30, "female")
        assert 1200 < bmr < 1600

    def test_male_higher_than_female(self):
        """Male BMR should generally be higher."""
        male = calculate_bmr(70, 175, 25, "male")
        female = calculate_bmr(70, 175, 25, "female")
        assert male > female

    def test_invalid_age(self):
        """Invalid age should raise ValueError."""
        with pytest.raises(ValueError):
            calculate_bmr(70, 175, 0, "male")

    def test_tdee_calculation(self):
        """TDEE should be BMR * activity multiplier."""
        bmr = 1700
        tdee = calculate_tdee(bmr, "moderately_active")
        assert tdee == round(bmr * 1.55, 0)

    def test_target_calories_weight_loss(self):
        """Weight loss target should be TDEE - 500."""
        target = calculate_target_calories(2000, "weight_loss")
        assert target == 1500

    def test_target_calories_floor(self):
        """Target should never go below 1200 kcal."""
        target = calculate_target_calories(1300, "weight_loss")
        assert target >= 1200


# ══════════════════════════════════════════════════════════════════════════════
# 2. FOOD DATABASE TOOL TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestFoodDatabase:
    """Tests for the Food Database tool."""

    @pytest.fixture
    def db(self):
        return FoodDatabaseTool()

    def test_load_database(self, db):
        """Database should load with items."""
        assert db.total_foods > 0

    def test_get_food_by_id(self, db):
        """Should retrieve a known food."""
        food = db.get_food_by_id("rice_white")
        assert food is not None
        assert food["name"] == "White Rice (cooked)"

    def test_get_food_not_found(self, db):
        """Should return None for unknown food."""
        result = db.get_food_by_id("nonexistent_food_xyz")
        assert result is None

    def test_search_by_name(self, db):
        """Should find foods by name search."""
        results = db.search_by_name("chicken")
        assert len(results) >= 1
        assert any("chicken" in r["name"].lower() for r in results)

    def test_get_foods_by_culture(self, db):
        """Should return culturally matched foods."""
        results = db.get_foods_by_culture("sri_lankan")
        assert len(results) >= 5  # Sri Lankan has many foods

    def test_get_cultural_substitutions(self, db):
        """Should return substitution mappings."""
        subs = db.get_cultural_substitutions("sri_lankan")
        assert subs is not None
        assert "grain_staples" in subs
        assert "protein_staples" in subs

    def test_calorie_range_filter(self, db):
        """Should filter foods by calorie range."""
        results = db.find_foods_in_calorie_range(100, 200)
        for food in results:
            assert 100 <= food["calories"] <= 200

    def test_nutritional_info(self, db):
        """Should return nutritional details."""
        info = db.get_nutritional_info("rice_white")
        assert info is not None
        assert "calories" in info
        assert "protein_g" in info

    def test_all_cultures(self, db):
        """Should list supported cultures."""
        cultures = db.get_all_cultures()
        assert "sri_lankan" in cultures
        assert "western" in cultures
        assert len(cultures) >= 4


# ══════════════════════════════════════════════════════════════════════════════
# 3. MEAL PLAN GENERATOR TOOL TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestMealPlanGenerator:
    """Tests for the Meal Plan Generator tool."""

    @pytest.fixture
    def gen(self):
        return MealPlanGeneratorTool()

    def test_generate_daily_plan(self, gen):
        """Should generate a complete daily plan."""
        plan = gen.generate_daily_plan(2000, "maintenance", "western")
        assert "meals" in plan
        assert len(plan["meals"]) == 4  # breakfast, lunch, dinner, snack
        assert plan["total_daily_calories"] > 0

    def test_plan_has_all_meal_types(self, gen):
        """Plan should include all meal types."""
        plan = gen.generate_daily_plan(2000, "maintenance")
        meal_types = {m["meal_type"] for m in plan["meals"]}
        assert "breakfast" in meal_types
        assert "lunch" in meal_types
        assert "dinner" in meal_types
        assert "snack" in meal_types

    def test_cultural_plan(self, gen):
        """Sri Lankan plan should use cultural foods."""
        plan = gen.generate_daily_plan(2000, "maintenance", "sri_lankan")
        assert plan["culture"] == "sri_lankan"

    def test_invalid_calories_too_low(self, gen):
        """Should reject calories below 800."""
        with pytest.raises(ValueError):
            gen.generate_daily_plan(500, "maintenance")

    def test_invalid_calories_too_high(self, gen):
        """Should reject calories above 6000."""
        with pytest.raises(ValueError):
            gen.generate_daily_plan(7000, "maintenance")

    def test_allergy_filtering(self, gen):
        """Foods matching allergies should be excluded."""
        plan = gen.generate_daily_plan(2000, "maintenance", "western", allergies=["salmon"])
        all_foods = []
        for meal in plan["meals"]:
            for item in meal["items"]:
                all_foods.append(item["food_name"].lower())
        assert not any("salmon" in f for f in all_foods)


# ══════════════════════════════════════════════════════════════════════════════
# 4. FILE EXPORT TOOL TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestFileExport:
    """Tests for the File Export tool."""

    @pytest.fixture
    def exporter(self, tmp_path):
        return FileExportTool(output_dir=tmp_path)

    def test_export_json(self, exporter):
        """Should create a valid JSON file."""
        data = {"test": "data", "number": 42}
        path = exporter.export_json(data, "test_export.json")
        assert Path(path).exists()
        with open(path) as f:
            loaded = json.load(f)
        assert loaded["test"] == "data"

    def test_export_text(self, exporter):
        """Should create a text file."""
        data = {"user_profile": {"name": "Test"}, "bmi_result": {"bmi_value": 22}}
        path = exporter.export_text(data, "test_export.txt")
        assert Path(path).exists()
        content = Path(path).read_text()
        assert "SMART DIET" in content

    def test_export_auto_filename(self, exporter):
        """Should auto-generate filename when none provided."""
        path = exporter.export_json({"data": 1})
        assert Path(path).exists()
        assert path.endswith(".json")


# ══════════════════════════════════════════════════════════════════════════════
# 5. AGENT VALIDATION TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestUserProfileAgent:
    """Tests for the User Profile Agent."""

    def test_valid_input(self):
        from agents.user_profile_agent import validate_input
        data = {"name": "Test", "age": 25, "gender": "male", "weight_kg": 70,
                "height_cm": 175, "dietary_goal": "weight_loss", "cultural_preference": "western"}
        cleaned, errors = validate_input(data)
        assert len(errors) == 0
        assert cleaned["name"] == "Test"
        assert cleaned["age"] == 25

    def test_invalid_age(self):
        from agents.user_profile_agent import validate_input
        data = {"age": 150, "weight_kg": 70, "height_cm": 170}
        cleaned, errors = validate_input(data)
        assert len(errors) > 0
        assert cleaned["age"] == 120  # Clamped

    def test_invalid_goal(self):
        from agents.user_profile_agent import validate_input
        data = {"dietary_goal": "fly_to_moon", "weight_kg": 70, "height_cm": 170}
        cleaned, errors = validate_input(data)
        assert cleaned["dietary_goal"] == "maintenance"  # Default

    def test_string_allergies(self):
        from agents.user_profile_agent import validate_input
        data = {"allergies": "nuts, fish, dairy", "weight_kg": 70, "height_cm": 170}
        cleaned, errors = validate_input(data)
        assert len(cleaned["allergies"]) == 3


# ══════════════════════════════════════════════════════════════════════════════
# 6. RULE-BASED EVALUATION
# ══════════════════════════════════════════════════════════════════════════════

class TestNutritionalRules:
    """Rule-based evaluation of generated meal plans."""

    def test_calories_within_range(self):
        """Generated plan calories should be within 30% of target."""
        gen = MealPlanGeneratorTool()
        plan = gen.generate_daily_plan(2000, "maintenance", "western")
        actual = plan["total_daily_calories"]
        assert 1400 <= actual <= 2600, f"Calories {actual} too far from 2000"

    def test_protein_minimum(self):
        """Plan should have at least 30g protein."""
        gen = MealPlanGeneratorTool()
        plan = gen.generate_daily_plan(2000, "maintenance", "western")
        assert plan["total_protein_g"] >= 30, "Too little protein"

    def test_all_meals_have_items(self):
        """Every meal should have at least 1 food item."""
        gen = MealPlanGeneratorTool()
        plan = gen.generate_daily_plan(2000, "maintenance", "western")
        for meal in plan["meals"]:
            assert len(meal["items"]) >= 1, f"{meal['meal_type']} is empty"

    def test_no_negative_values(self):
        """No nutritional values should be negative."""
        gen = MealPlanGeneratorTool()
        plan = gen.generate_daily_plan(2000, "maintenance", "sri_lankan")
        for meal in plan["meals"]:
            for item in meal["items"]:
                assert item["calories"] >= 0
                assert item["protein_g"] >= 0
                assert item["carbs_g"] >= 0
                assert item["fat_g"] >= 0


# ══════════════════════════════════════════════════════════════════════════════
# 7. INTEGRATION TEST (No LLM required)
# ══════════════════════════════════════════════════════════════════════════════

class TestIntegration:
    """Integration tests for agent node functions (without LLM)."""

    def test_user_profile_node(self):
        """User profile node should produce valid output."""
        from agents.user_profile_agent import user_profile_node
        state = {
            "raw_input": {"name": "Test", "age": 25, "gender": "male",
                          "weight_kg": 70, "height_cm": 175,
                          "dietary_goal": "weight_loss",
                          "cultural_preference": "sri_lankan"},
            "messages": [], "errors": [],
        }
        result = user_profile_node(state)
        assert result["user_profile"] is not None
        assert result["bmi_result"] is not None
        assert result["target_calories"] > 0

    def test_full_tool_pipeline(self):
        """Test tools pipeline without LLM agents."""
        # Step 1: BMI
        bmi = calculate_bmi(70, 175)
        assert bmi["category"] == "normal"
        # Step 2: Target calories
        bmr = calculate_bmr(70, 175, 28, "male")
        tdee = calculate_tdee(bmr, "moderately_active")
        target = calculate_target_calories(tdee, "weight_loss")
        assert target > 1200
        # Step 3: Generate plan
        gen = MealPlanGeneratorTool()
        plan = gen.generate_daily_plan(target, "weight_loss", "sri_lankan")
        assert plan["total_daily_calories"] > 0
        # Step 4: Export
        import tempfile
        exp = FileExportTool(Path(tempfile.mkdtemp()))
        path = exp.export_json(plan)
        assert Path(path).exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
