"""
File Export Tool

Saves generated meal plans and reports as .txt or .json files locally.
Supports structured JSON export and human-readable text export.
"""
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from loguru import logger
from config import OUTPUT_DIR


class FileExportTool:
    """Exports meal plans and reports to local files."""

    def __init__(self, output_dir: Optional[Path] = None) -> None:
        """Initialize with output directory. Creates it if needed."""
        self._output_dir = output_dir or OUTPUT_DIR
        self._output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"FileExportTool initialized: {self._output_dir}")

    def export_json(self, data: dict, filename: Optional[str] = None) -> str:
        """Export data as a formatted JSON file.

        Args:
            data: Dictionary to export.
            filename: Optional custom filename. Auto-generated if None.
        Returns:
            Absolute path to the exported file.
        Raises:
            TypeError: If data is not serializable.
        """
        if filename is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"meal_plan_{ts}.json"
        if not filename.endswith(".json"):
            filename += ".json"
        filepath = self._output_dir / filename
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"JSON exported: {filepath}")
            return str(filepath)
        except (TypeError, ValueError) as e:
            logger.error(f"JSON export failed: {e}")
            raise

    def export_text(self, data: dict, filename: Optional[str] = None) -> str:
        """Export meal plan as human-readable text.

        Args:
            data: Meal plan dictionary.
            filename: Optional custom filename.
        Returns:
            Absolute path to the exported file.
        """
        if filename is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"meal_plan_{ts}.txt"
        if not filename.endswith(".txt"):
            filename += ".txt"
        filepath = self._output_dir / filename
        try:
            text = self._format_plan_text(data)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(text)
            logger.info(f"Text exported: {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Text export failed: {e}")
            raise

    def _format_plan_text(self, data: dict) -> str:
        """Convert meal plan dict to formatted text."""
        lines = []
        lines.append("=" * 60)
        lines.append("  SMART DIET & NUTRITION — PERSONALIZED MEAL PLAN")
        lines.append("=" * 60)
        lines.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("")

        # User profile section
        profile = data.get("user_profile", {})
        if profile:
            lines.append("─" * 60)
            lines.append("  USER PROFILE")
            lines.append("─" * 60)
            for k, v in profile.items():
                lines.append(f"  {k.replace('_', ' ').title():.<30} {v}")
            lines.append("")

        # BMI section
        bmi = data.get("bmi_result", {})
        if bmi:
            lines.append("─" * 60)
            lines.append("  BMI ANALYSIS")
            lines.append("─" * 60)
            lines.append(f"  BMI Value: {bmi.get('bmi_value', 'N/A')}")
            lines.append(f"  Category:  {bmi.get('category', 'N/A')}")
            lines.append(f"  Note:      {bmi.get('interpretation', '')}")
            lines.append("")

        # Meal plan section
        plan = data.get("adapted_meal_plan") or data.get("daily_meal_plan", {})
        if plan:
            lines.append("─" * 60)
            lines.append(f"  DAILY MEAL PLAN (Day {plan.get('day', 1)})")
            lines.append(f"  Culture: {plan.get('culture', 'N/A')}")
            lines.append(f"  Target: {plan.get('target_calories', 'N/A')} kcal")
            lines.append("─" * 60)
            for meal in plan.get("meals", []):
                mtype = meal.get("meal_type", "").upper()
                lines.append(f"\n  ◆ {mtype} ({meal.get('total_calories', 0)} kcal)")
                lines.append("  " + "·" * 40)
                for item in meal.get("items", []):
                    lines.append(
                        f"    • {item['food_name']:<30} {item['quantity']:<20} "
                        f"{item['calories']} kcal | P:{item['protein_g']}g "
                        f"C:{item['carbs_g']}g F:{item['fat_g']}g"
                    )
            lines.append(f"\n  ── DAILY TOTALS ──")
            lines.append(f"  Calories:  {plan.get('total_daily_calories', 0)} kcal")
            lines.append(f"  Protein:   {plan.get('total_protein_g', 0)} g")
            lines.append(f"  Carbs:     {plan.get('total_carbs_g', 0)} g")
            lines.append(f"  Fat:       {plan.get('total_fat_g', 0)} g")
            lines.append("")

        # Analysis section
        analysis = data.get("calorie_analysis", {})
        if analysis:
            lines.append("─" * 60)
            lines.append("  CALORIE ANALYSIS")
            lines.append("─" * 60)
            lines.append(f"  Target:    {analysis.get('target_calories', 0)} kcal")
            lines.append(f"  Actual:    {analysis.get('actual_calories', 0)} kcal")
            lines.append(f"  Deviation: {analysis.get('calorie_deviation', 0):.1f}%")
            lines.append(f"  Meets Goal: {'✓ Yes' if analysis.get('meets_goal') else '✗ No'}")
            recs = analysis.get("recommendations", [])
            if recs:
                lines.append("\n  Recommendations:")
                for r in recs:
                    lines.append(f"    → {r}")

        lines.append("\n" + "=" * 60)
        lines.append("  End of Report")
        lines.append("=" * 60)
        return "\n".join(lines)

    def export_final_report(self, state: dict) -> tuple[str, str]:
        """Export both JSON and TXT versions of the final report.

        Args:
            state: Complete agent state dictionary.
        Returns:
            Tuple of (json_path, txt_path).
        """
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = self.export_json(state, f"meal_plan_{ts}.json")
        txt_path = self.export_text(state, f"meal_plan_{ts}.txt")
        return json_path, txt_path
