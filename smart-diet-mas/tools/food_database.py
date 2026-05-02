"""
Food Database Tool

Provides access to a local JSON food database containing nutritional
information for foods across multiple cultural cuisines.

Features:
    - Load and query food items by ID, name, category, or culture
    - Retrieve nutritional information for specific foods
    - Find cultural substitutions for meal adaptation
    - Search foods within a calorie range
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from loguru import logger

from config import DATA_DIR


class FoodDatabaseTool:
    """
    Tool for querying the local food nutrition database.

    The database is stored as a JSON file and loaded into memory
    on initialization for fast lookups.
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        """
        Initialize the food database tool.

        Args:
            db_path: Path to the food_database.json file.
                     Defaults to DATA_DIR / 'food_database.json'.

        Raises:
            FileNotFoundError: If the database file does not exist.
            json.JSONDecodeError: If the database file is malformed.
        """
        self._db_path = db_path or DATA_DIR / "food_database.json"

        if not self._db_path.exists():
            raise FileNotFoundError(f"Food database not found at {self._db_path}")

        with open(self._db_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self._foods: list[dict] = data.get("foods", [])
        self._substitutions: dict = data.get("cultural_substitutions", {})

        # Build lookup index by ID
        self._food_index: dict[str, dict] = {
            food["id"]: food for food in self._foods
        }

        logger.info(f"Food database loaded: {len(self._foods)} items from {self._db_path}")

    def get_food_by_id(self, food_id: str) -> Optional[dict]:
        """
        Retrieve a food item by its unique ID.

        Args:
            food_id: The unique identifier of the food item.

        Returns:
            Food item dictionary or None if not found.

        Example:
            >>> db = FoodDatabaseTool()
            >>> db.get_food_by_id("rice_white")
            {'id': 'rice_white', 'name': 'White Rice (cooked)', ...}
        """
        result = self._food_index.get(food_id)
        if result is None:
            logger.warning(f"Food not found: {food_id}")
        return result

    def search_by_name(self, query: str) -> list[dict]:
        """
        Search foods by name (case-insensitive partial match).

        Args:
            query: Search query string.

        Returns:
            List of matching food items.
        """
        query_lower = query.lower().strip()
        if not query_lower:
            return []

        results = [
            food for food in self._foods
            if query_lower in food["name"].lower()
        ]
        logger.info(f"Search '{query}': {len(results)} results")
        return results

    def get_foods_by_category(self, category: str) -> list[dict]:
        """
        Get all foods belonging to a specific category.

        Args:
            category: Food category (e.g., 'grains', 'protein', 'vegetable').

        Returns:
            List of food items in the specified category.
        """
        category_lower = category.lower().strip()
        results = [
            food for food in self._foods
            if food.get("category", "").lower() == category_lower
        ]
        logger.info(f"Category '{category}': {len(results)} items")
        return results

    def get_foods_by_culture(self, culture: str) -> list[dict]:
        """
        Get all foods associated with a specific culture.

        Args:
            culture: Cultural identifier (e.g., 'sri_lankan', 'western').

        Returns:
            List of food items that belong to the specified culture.
        """
        culture_lower = culture.lower().strip()
        results = [
            food for food in self._foods
            if culture_lower in [c.lower() for c in food.get("cultures", [])]
        ]
        logger.info(f"Culture '{culture}': {len(results)} items")
        return results

    def get_cultural_substitutions(self, culture: str) -> Optional[dict]:
        """
        Get the cultural substitution mapping for meal adaptation.

        Args:
            culture: Cultural identifier.

        Returns:
            Dictionary with grain_staples, protein_staples, etc.
            or None if culture is not supported.
        """
        result = self._substitutions.get(culture.lower().strip())
        if result is None:
            logger.warning(f"No cultural substitutions found for: {culture}")
        return result

    def find_foods_in_calorie_range(
        self,
        min_calories: float = 0,
        max_calories: float = 9999,
        culture: Optional[str] = None,
        category: Optional[str] = None,
    ) -> list[dict]:
        """
        Find foods within a calorie range, optionally filtered by culture and category.

        Args:
            min_calories: Minimum calories per serving.
            max_calories: Maximum calories per serving.
            culture: Optional cultural filter.
            category: Optional food category filter.

        Returns:
            List of food items matching the criteria.
        """
        results = []
        for food in self._foods:
            cal = food.get("calories", 0)
            if cal < min_calories or cal > max_calories:
                continue
            if culture and culture.lower() not in [c.lower() for c in food.get("cultures", [])]:
                continue
            if category and food.get("category", "").lower() != category.lower():
                continue
            results.append(food)

        logger.info(
            f"Calorie range [{min_calories}-{max_calories}] "
            f"culture={culture} category={category}: {len(results)} results"
        )
        return results

    def get_nutritional_info(self, food_id: str) -> Optional[dict]:
        """
        Get detailed nutritional information for a specific food.

        Args:
            food_id: The unique identifier of the food item.

        Returns:
            Dictionary with nutritional details, or None if not found.
        """
        food = self.get_food_by_id(food_id)
        if food is None:
            return None

        return {
            "name": food["name"],
            "serving_size": food["serving_size"],
            "calories": food["calories"],
            "protein_g": food["protein_g"],
            "carbs_g": food["carbs_g"],
            "fat_g": food["fat_g"],
            "fiber_g": food["fiber_g"],
        }

    def get_all_cultures(self) -> list[str]:
        """
        Get list of all supported cultures.

        Returns:
            List of culture identifiers.
        """
        return list(self._substitutions.keys())

    @property
    def total_foods(self) -> int:
        """Return total number of foods in the database."""
        return len(self._foods)
