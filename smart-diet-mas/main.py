"""
Smart Diet & Nutrition Multi-Agent System — Main Entry Point

This is the primary executable for the multi-agent system.
It demonstrates the complete workflow with example user input
and provides an interactive CLI mode.

Usage:
    python main.py                  # Run with default example input
    python main.py --interactive    # Interactive CLI mode
"""
from __future__ import annotations
import sys
import json
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# Must import observability first to configure logging
import observability
from observability import tracer
from orchestration.workflow import run_workflow
from config import SUPPORTED_CULTURES

console = Console()


# ── Example Inputs ─────────────────────────────────────────────────────────────
EXAMPLE_INPUTS = {
    "sri_lankan_user": {
        "name": "Kasun Perera",
        "age": 28,
        "gender": "male",
        "weight_kg": 78,
        "height_cm": 175,
        "activity_level": "moderately_active",
        "dietary_goal": "weight_loss",
        "allergies": [],
        "cultural_preference": "sri_lankan",
    },
    "indian_user": {
        "name": "Priya Sharma",
        "age": 32,
        "gender": "female",
        "weight_kg": 62,
        "height_cm": 160,
        "activity_level": "lightly_active",
        "dietary_goal": "healthy_eating",
        "allergies": ["fish"],
        "cultural_preference": "indian_north",
    },
    "western_user": {
        "name": "John Smith",
        "age": 45,
        "gender": "male",
        "weight_kg": 95,
        "height_cm": 180,
        "activity_level": "sedentary",
        "dietary_goal": "weight_loss",
        "allergies": ["nuts"],
        "cultural_preference": "western",
    },
}


def display_results(state: dict) -> None:
    """Display workflow results using rich formatting."""
    console.print()
    # Header
    console.print(Panel.fit(
        "[bold cyan]Smart Diet & Nutrition — Results[/bold cyan]",
        border_style="cyan",
    ))

    # User Profile
    profile = state.get("user_profile", {})
    bmi = state.get("bmi_result", {})
    table = Table(title="[Profile]", border_style="blue")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")
    for k, v in profile.items():
        table.add_row(k.replace("_", " ").title(), str(v))
    table.add_row("BMI", f"{bmi.get('bmi_value', 'N/A')} ({bmi.get('category', 'N/A')})")
    table.add_row("Target Calories", f"{state.get('target_calories', 'N/A')} kcal/day")
    console.print(table)

    # Meal Plan
    plan = state.get("adapted_meal_plan") or state.get("daily_meal_plan", {})
    if plan:
        console.print()
        meal_table = Table(title=f"Meal Plan — {plan.get('culture', 'N/A').replace('_', ' ').title()} Cuisine",
                          border_style="green")
        meal_table.add_column("Meal", style="bold yellow")
        meal_table.add_column("Food", style="white")
        meal_table.add_column("Qty", style="dim")
        meal_table.add_column("Cal", style="cyan", justify="right")
        meal_table.add_column("P(g)", justify="right")
        meal_table.add_column("C(g)", justify="right")
        meal_table.add_column("F(g)", justify="right")

        for meal in plan.get("meals", []):
            first = True
            for item in meal.get("items", []):
                meal_table.add_row(
                    meal["meal_type"].upper() if first else "",
                    item["food_name"],
                    item["quantity"][:20],
                    str(item["calories"]),
                    str(item["protein_g"]),
                    str(item["carbs_g"]),
                    str(item["fat_g"]),
                )
                first = False
            meal_table.add_row("", "", "", "───", "───", "───", "───")

        meal_table.add_row(
            "[bold]TOTAL[/bold]", "", "",
            f"[bold]{plan.get('total_daily_calories', 0)}[/bold]",
            f"[bold]{plan.get('total_protein_g', 0)}[/bold]",
            f"[bold]{plan.get('total_carbs_g', 0)}[/bold]",
            f"[bold]{plan.get('total_fat_g', 0)}[/bold]",
        )
        console.print(meal_table)

    # Analysis
    analysis = state.get("calorie_analysis", {})
    if analysis:
        console.print()
        status = "✅ PASS" if analysis.get("meets_goal") else "❌ NEEDS ADJUSTMENT"
        console.print(Panel(
            f"[bold]Calorie Analysis[/bold]\n\n"
            f"Target:    {analysis.get('target_calories', 0)} kcal\n"
            f"Actual:    {analysis.get('actual_calories', 0)} kcal\n"
            f"Deviation: {analysis.get('calorie_deviation', 0):.1f}%\n"
            f"Status:    {status}\n"
            f"Protein:   {'✅ Adequate' if analysis.get('protein_adequate') else '⚠️ Insufficient'}\n\n"
            f"Macros: P:{analysis.get('macronutrient_breakdown', {}).get('protein_pct', 0)}% "
            f"C:{analysis.get('macronutrient_breakdown', {}).get('carbs_pct', 0)}% "
            f"F:{analysis.get('macronutrient_breakdown', {}).get('fat_pct', 0)}%",
            title="Analysis",
            border_style="yellow",
        ))

        if analysis.get("recommendations"):
            console.print()
            for r in analysis["recommendations"]:
                console.print(f"  * {r}")

    # Final Report
    report = state.get("final_report", "")
    if report:
        console.print()
        console.print(Panel(report, title="Nutrition Report", border_style="magenta"))

    # Export path
    if state.get("export_path"):
        console.print(f"\nReport saved to: {state['export_path']}")

    # Execution trace
    console.print()
    console.print(tracer.get_summary())


def interactive_mode() -> dict:
    """Collect user input interactively via CLI."""
    console.print(Panel.fit(
        "[bold cyan]Smart Diet & Nutrition MAS — Interactive Mode[/bold cyan]",
        border_style="cyan",
    ))
    console.print()

    data = {}
    data["name"] = console.input("[cyan]Your name: [/cyan]") or "User"
    data["age"] = int(console.input("[cyan]Age: [/cyan]") or "25")
    data["gender"] = console.input("[cyan]Gender (male/female/other): [/cyan]") or "other"
    data["weight_kg"] = float(console.input("[cyan]Weight (kg): [/cyan]") or "70")
    data["height_cm"] = float(console.input("[cyan]Height (cm): [/cyan]") or "170")

    console.print("\n[dim]Activity levels: sedentary, lightly_active, moderately_active, very_active, extra_active[/dim]")
    data["activity_level"] = console.input("[cyan]Activity level: [/cyan]") or "moderately_active"

    console.print("[dim]Goals: weight_loss, muscle_gain, maintenance, healthy_eating[/dim]")
    data["dietary_goal"] = console.input("[cyan]Dietary goal: [/cyan]") or "maintenance"

    allergies = console.input("[cyan]Allergies (comma-separated, or press Enter for none): [/cyan]")
    data["allergies"] = [a.strip() for a in allergies.split(",") if a.strip()] if allergies else []

    console.print(f"[dim]Cultures: {', '.join(SUPPORTED_CULTURES)}[/dim]")
    data["cultural_preference"] = console.input("[cyan]Cultural preference: [/cyan]") or "western"

    return data


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Smart Diet & Nutrition Multi-Agent System")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive CLI mode")
    parser.add_argument("--example", "-e", choices=list(EXAMPLE_INPUTS.keys()),
                        default="sri_lankan_user", help="Run with example input")
    args = parser.parse_args()

    if args.interactive:
        user_input = interactive_mode()
    else:
        user_input = EXAMPLE_INPUTS[args.example]
        console.print(f"[dim]Using example: {args.example}[/dim]")
        console.print(f"[dim]Input: {json.dumps(user_input, indent=2)}[/dim]")

    console.print()
    console.print("[bold yellow]Running Multi-Agent Workflow...[/bold yellow]")
    console.print()

    # Run the workflow
    final_state = run_workflow(user_input)

    # Display results
    display_results(final_state)


if __name__ == "__main__":
    main()
