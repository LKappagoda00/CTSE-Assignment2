"""
File Export Tool

Saves generated meal plans and reports as .txt or .json files locally.
Supports structured JSON export and human-readable text export.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

from config import OUTPUT_DIR


class FileExportTool:
    """
    Exports meal plans and nutrition reports to local files.

    Supports both structured JSON and human-readable plain-text formats.
    Output directory is created automatically if it does not exist.

    Example:
        >>> tool = FileExportTool()
        >>> json_path, txt_path = tool.export_final_report(state)
        >>> print(json_path)
        '/outputs/meal_plan_20240101_120000.json'
    """

    def __init__(self, output_dir: Path | None = None) -> None:
        """
        Initialize FileExportTool with output directory.

        Args:
            output_dir: Optional custom output Path. Defaults to OUTPUT_DIR
                        from config. Directory is created if it does not exist.
        """
        self._output_dir: Path = output_dir or OUTPUT_DIR
        self._output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"FileExportTool initialized: {self._output_dir}")

    def export_json(
        self,
        data: dict[str, Any],
        filename: str | None = None,
    ) -> str:
        """
        Export data as a formatted JSON file.

        Args:
            data:     Dictionary to serialize and export.
            filename: Optional custom filename (with or without .json extension).
                      Auto-generated with timestamp if None.

        Returns:
            Absolute path to the exported JSON file as a string.

        Raises:
            TypeError:  If data is not a dict or is not JSON-serializable.
            OSError:    If the file cannot be written (e.g. disk full,
                        permission denied).

        Example:
            >>> tool = FileExportTool()
            >>> path = tool.export_json({"key": "value"}, "test_export")
            >>> path.endswith(".json")
            True
        """
        # FIX: Validate input type before attempting serialization
        if not isinstance(data, dict):
            raise TypeError(f"data must be a dict, got {type(data).__name__}")

        if filename is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"meal_plan_{ts}.json"
        if not filename.endswith(".json"):
            filename += ".json"

        filepath: Path = self._output_dir / filename
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"JSON exported: {filepath}")
            return str(filepath)
        except (TypeError, ValueError, OSError) as e:   # FIX: added OSError
            logger.error(f"JSON export failed: {e}")
            raise

    def export_text(
        self,
        data: dict[str, Any],
        filename: str | None = None,
    ) -> str:
        """
        Export meal plan as a human-readable plain-text file.

        Args:
            data:     Meal plan / state dictionary to format and export.
            filename: Optional custom filename (with or without .txt extension).
                      Auto-generated with timestamp if None.

        Returns:
            Absolute path to the exported text file as a string.

        Raises:
            OSError: If the file cannot be written.

        Example:
            >>> tool = FileExportTool()
            >>> path = tool.export_text(state, "my_plan")
            >>> path.endswith(".txt")
            True
        """
        if filename is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"meal_plan_{ts}.txt"
        if not filename.endswith(".txt"):
            filename += ".txt"

        filepath: Path = self._output_dir / filename
        try:
            text = self._format_plan_text(data)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(text)
            logger.info(f"Text exported: {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Text export failed: {e}")
            raise

    def _format_plan_text(self, data: dict[str, Any]) -> str:
        """
        Convert a meal plan state dictionary into formatted plain text.

        Args:
            data: Complete state dictionary containing user_profile,
                  bmi_result, adapted_meal_plan, calorie_analysis,
                  and final_report sections.

        Returns:
            A formatted multi-line string ready to write to a .txt file.
        """
        lines: list[str] = []
        lines.append("=" * 60)
        lines.append("  SMART DIET & NUTRITION — PERSONALIZED MEAL PLAN")
        lines.append("=" * 60)
        lines.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("")

        # ── User Profile Section ───────────────────────────────────────────
        profile: dict[str, Any] = data.get("user_profile", {})
        if profile:
            lines.append("─" * 60)
            lines.append("  USER PROFILE")
            lines.append("─" * 60)
            for k, v in profile.items():
                lines.append(f"  {k.replace('_', ' ').title():.<30} {v}")
            lines.append("")

        # ── BMI Section ────────────────────────────────────────────────────
        bmi: dict[str, Any] = data.get("bmi_result", {})
        if bmi:
            lines.append("─" * 60)
            lines.append("  BMI ANALYSIS")
            lines.append("─" * 60)
            lines.append(f"  BMI Value: {bmi.get('bmi_value', 'N/A')}")
            lines.append(f"  Category:  {bmi.get('category', 'N/A')}")
            lines.append(f"  Note:      {bmi.get('interpretation', '')}")
            lines.append("")

        # ── Meal Plan Section ──────────────────────────────────────────────
        plan: dict[str, Any] = (
            data.get("adapted_meal_plan") or data.get("daily_meal_plan", {})
        )
        if plan:
            lines.append("─" * 60)
            lines.append(f"  DAILY MEAL PLAN (Day {plan.get('day', 1)})")
            lines.append(f"  Culture: {plan.get('culture', 'N/A')}")
            lines.append(f"  Target:  {plan.get('target_calories', 'N/A')} kcal")
            lines.append("─" * 60)

            for meal in plan.get("meals", []):
                mtype: str = meal.get("meal_type", "").upper()
                lines.append(
                    f"\n  ◆ {mtype} ({meal.get('total_calories', 0)} kcal)"
                )
                lines.append("  " + "·" * 40)
                for item in meal.get("items", []):
                    # FIX: use .get() with safe defaults — prevents KeyError crash
                    food_name: str = item.get("food_name", "Unknown")
                    quantity: str = str(item.get("quantity", "N/A"))
                    calories: float = item.get("calories", 0)
                    protein_g: float = item.get("protein_g", 0)
                    carbs_g: float = item.get("carbs_g", 0)
                    fat_g: float = item.get("fat_g", 0)
                    lines.append(
                        f"    • {food_name:<30} {quantity:<20} "
                        f"{calories} kcal | P:{protein_g}g "
                        f"C:{carbs_g}g F:{fat_g}g"
                    )

            lines.append("\n  ── DAILY TOTALS ──")
            lines.append(f"  Calories: {plan.get('total_daily_calories', 0)} kcal")
            lines.append(f"  Protein:  {plan.get('total_protein_g', 0)} g")
            lines.append(f"  Carbs:    {plan.get('total_carbs_g', 0)} g")
            lines.append(f"  Fat:      {plan.get('total_fat_g', 0)} g")
            lines.append("")

        # ── Calorie Analysis Section ───────────────────────────────────────
        analysis: dict[str, Any] = data.get("calorie_analysis", {})
        if analysis:
            lines.append("─" * 60)
            lines.append("  CALORIE ANALYSIS")
            lines.append("─" * 60)
            lines.append(f"  Target:    {analysis.get('target_calories', 0)} kcal")
            lines.append(f"  Actual:    {analysis.get('actual_calories', 0)} kcal")
            lines.append(
                f"  Deviation: {analysis.get('calorie_deviation', 0):.1f}%"
            )
            lines.append(
                f"  Meets Goal: {'✓ Yes' if analysis.get('meets_goal') else '✗ No'}"
            )
            recs: list[str] = analysis.get("recommendations", [])
            if recs:
                lines.append("\n  Recommendations:")
                for r in recs:
                    lines.append(f"    → {r}")
            lines.append("")

        # FIX: Render LLM narrative report section (was missing entirely)
        final_report: str = data.get("final_report", "")
        if final_report:
            lines.append("─" * 60)
            lines.append("  NUTRITION REPORT SUMMARY")
            lines.append("─" * 60)
            # Wrap long lines for readability
            for line in final_report.splitlines():
                lines.append(f"  {line}")
            lines.append("")

        lines.append("=" * 60)
        lines.append("  End of Report")
        lines.append("=" * 60)
        return "\n".join(lines)

    def export_final_report(self, state: dict[str, Any]) -> tuple[str, str]:
        """
        Export both JSON and TXT versions of the final nutrition report.

        Args:
            state: Complete agent state dictionary containing all sections
                   (user_profile, bmi_result, adapted_meal_plan,
                   calorie_analysis, final_report).

        Returns:
            A tuple of (json_path, txt_path) — absolute paths to the
            exported files as strings.

        Raises:
            TypeError: If state is not a dict.
            OSError:   If either file cannot be written.

        Example:
            >>> tool = FileExportTool()
            >>> json_path, txt_path = tool.export_final_report(state)
            >>> json_path.endswith(".json")
            True
            >>> txt_path.endswith(".txt")
            True
        """
        ts: str = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path: str = self.export_json(state, f"meal_plan_{ts}.json")
        txt_path: str = self.export_text(state, f"meal_plan_{ts}.txt")
        return json_path, txt_path