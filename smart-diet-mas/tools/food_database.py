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
from typing import Any

from loguru import logger

from config import DATA_DIR


class FoodDatabaseTool:
    """
    Tool for querying the local food nutrition database.

    The database is stored as a JSON file and loaded into memory
    on initialization for fast O(1) ID-based lookups.

    Example:
        >>> db = FoodDatabaseTool()
        >>> food = db.get_food_by_id("rice_white")
        >>> food["name"]
        'White Rice (cooked)'
    """

    def __init__(self, db_path: Path | None = None) -> None:
        """
        Initialize the food database tool.

        Args:
            db_path: Path to the food_database.json file.
                     Defaults to DATA_DIR / 'food_database.json'.

        Raises:
            FileNotFoundError: If the database file does not exist.
            json.JSONDecodeError: If the database file is malformed JSON.
            ValueError: If the database structure is invalid.
        """
        self._db_path: Path = db_path or DATA_DIR / "food_database.json"

        if not self._db_path.exists():
            raise FileNotFoundError(
                f"Food database not found at {self._db_path}"
            )

        with open(self._db_path, "r", encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)

        # FIX: Validate database structure before using it
        if not isinstance(data.get("foods"), list):
            raise ValueError(
                "Database format invalid: 'foods' key must be a list."
            )

        self._foods: list[dict[str, Any]] = data.get("foods", [])
        self._substitutions: dict[str, Any] = data.get(
            "cultural_substitutions", {}
        )

        # FIX: Skip entries missing 'id' to prevent KeyError during indexing
        self._food_index: dict[str, dict[str, Any]] = {
            food["id"]: food for food in self._foods if "id" in food
        }

        skipped = len(self._foods) - len(self._food_index)
        if skipped > 0:
            logger.warning(
                f"{skipped} food entries skipped due to missing 'id' field."
            )

        logger.info(
            f"Food database loaded: {len(self._food_index)} items "
            f"from {self._db_path}"
        )

    def get_food_by_id(self, food_id: str) -> dict[str, Any] | None:
        """
        Retrieve a food item by its unique ID.

        Args:
            food_id: The unique identifier of the food item.

        Returns:
            Food item dictionary, or None if not found.

        Example:
            >>> db = FoodDatabaseTool()
            >>> db.get_food_by_id("rice_white")
            {'id': 'rice_white', 'name': 'White Rice (cooked)', ...}
            >>> db.get_food_by_id("nonexistent")
            None
        """
        result = self._food_index.get(food_id)
        if result is None:
            logger.warning(f"Food not found: '{food_id}'")
        return result

    def search_by_name(self, query: str) -> list[dict[str, Any]]:
        """
        Search foods by name using a case-insensitive partial match.

        Args:
            query: Search query string.

        Returns:
            List of matching food item dictionaries.

        Example:
            >>> db = FoodDatabaseTool()
            >>> results = db.search_by_name("rice")
            >>> len(results) > 0
            True
        """
        query_lower = query.lower().strip()
        if not query_lower:
            return []

        # FIX: use .get("name", "") to prevent KeyError on malformed entries
        results: list[dict[str, Any]] = [
            food for food in self._foods
            if query_lower in food.get("name", "").lower()
        ]
        logger.info(f"Search '{query}': {len(results)} result(s)")
        return results

    def get_foods_by_category(self, category: str) -> list[dict[str, Any]]:
        """
        Get all foods belonging to a specific category.

        Args:
            category: Food category string (e.g. 'grains', 'protein',
                      'vegetable').

        Returns:
            List of food item dictionaries in the specified category.

        Example:
            >>> db = FoodDatabaseTool()
            >>> grains = db.get_foods_by_category("grains")
            >>> all(f["category"] == "grains" for f in grains)
            True
        """
        category_lower = category.lower().strip()
        results: list[dict[str, Any]] = [
            food for food in self._foods
            if food.get("category", "").lower() == category_lower
        ]
        logger.info(f"Category '{category}': {len(results)} item(s)")
        return results

    def get_foods_by_culture(self, culture: str) -> list[dict[str, Any]]:
        """
        Get all foods associated with a specific culture.

        Args:
            culture: Cultural identifier (e.g. 'sri_lankan', 'western').

        Returns:
            List of food item dictionaries belonging to the specified culture.

        Example:
            >>> db = FoodDatabaseTool()
            >>> foods = db.get_foods_by_culture("sri_lankan")
            >>> len(foods) > 0
            True
        """
        culture_lower = culture.lower().strip()
        results: list[dict[str, Any]] = [
            food for food in self._foods
            if culture_lower in [
                c.lower() for c in food.get("cultures", [])
            ]
        ]
        logger.info(f"Culture '{culture}': {len(results)} item(s)")
        return results

    def get_cultural_substitutions(
        self, culture: str
    ) -> dict[str, Any] | None:
        """
        Get the cultural substitution mapping for meal adaptation.

        Returns category-grouped food ID lists (grain_staples,
        protein_staples, vegetable_staples, condiments, beverages, fruits)
        that can be used to adapt a meal plan to the target culture.

        Args:
            culture: Cultural identifier (e.g. 'sri_lankan', 'western').

        Returns:
            Dictionary with substitution category lists,
            or None if the culture is not supported.

        Example:
            >>> db = FoodDatabaseTool()
            >>> subs = db.get_cultural_substitutions("sri_lankan")
            >>> "grain_staples" in subs
            True
        """
        result = self._substitutions.get(culture.lower().strip())
        if result is None:
            logger.warning(
                f"No cultural substitutions found for: '{culture}'"
            )
        return result

    def find_foods_in_calorie_range(
        self,
        min_calories: float = 0,
        max_calories: float = 9999,
        culture: str | None = None,
        category: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Find foods within a calorie range, with optional culture and
        category filters.

        Args:
            min_calories: Minimum calories per serving (inclusive).
            max_calories: Maximum calories per serving (inclusive).
            culture:      Optional culture filter string.
            category:     Optional food category filter string.

        Returns:
            List of food item dictionaries matching all criteria.

        Example:
            >>> db = FoodDatabaseTool()
            >>> foods = db.find_foods_in_calorie_range(100, 300, culture="western")
            >>> all(100 <= f["calories"] <= 300 for f in foods)
            True
        """
        results: list[dict[str, Any]] = []

        for food in self._foods:
            cal: float = food.get("calories", 0)
            if cal < min_calories or cal > max_calories:
                continue
            if culture and culture.lower() not in [
                c.lower() for c in food.get("cultures", [])
            ]:
                continue
            if category and food.get("category", "").lower() != category.lower():
                continue
            results.append(food)

        logger.info(
            f"Calorie range [{min_calories}-{max_calories}] "
            f"culture={culture} category={category}: {len(results)} result(s)"
        )
        return results

    def get_nutritional_info(self, food_id: str) -> dict[str, Any] | None:
        """
        Get a concise nutritional summary for a specific food item.

        Args:
            food_id: The unique identifier of the food item.

        Returns:
            Dictionary with key nutritional fields, or None if not found.

        Example:
            >>> db = FoodDatabaseTool()
            >>> info = db.get_nutritional_info("rice_white")
            >>> "calories" in info
            True
        """
        food = self.get_food_by_id(food_id)
        if food is None:
            return None

        # FIX: use .get() with safe defaults on all fields — prevents KeyError
        # FIX: include 'allergens' field — required by cultural_adapter_agent
        return {
            "name": food.get("name", "Unknown"),
            "serving_size": food.get("serving_size", "N/A"),
            "calories": food.get("calories", 0),
            "protein_g": food.get("protein_g", 0),
            "carbs_g": food.get("carbs_g", 0),
            "fat_g": food.get("fat_g", 0),
            "fiber_g": food.get("fiber_g", 0),
            "allergens": food.get("allergens", []),  # FIX: needed for allergy checks
        }

    def get_all_cultures(self) -> list[str]:
        """
        Get a list of all supported culture identifiers.

        Returns:
            List of culture identifier strings present in the database.

        Example:
            >>> db = FoodDatabaseTool()
            >>> "sri_lankan" in db.get_all_cultures()
            True
        """
        return list(self._substitutions.keys())

    @property
    def total_foods(self) -> int:
        """
        Total number of valid food entries loaded from the database.

        Returns:
            Integer count of indexed food items.
        """
        return len(self._food_index)