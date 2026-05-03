"""
Smart Diet & Nutrition Multi-Agent System — Main Entry Point

This starts the FastAPI server that receives meal plan requests from the frontend.
The server runs continuously and processes user inputs through the multi-agent workflow.

Usage:
    python main.py    # Start FastAPI web server
"""
from __future__ import annotations
from rich.console import Console

# Must import observability first to configure logging
import observability

console = Console()


def main():
    """Main entry point - starts the FastAPI server."""
    console.print("[bold green]Starting Smart Diet MAS FastAPI Server...[/bold green]")
    console.print("[dim]Server will be available at http://localhost:8000[/dim]")
    console.print("[dim]Ready to receive meal plan requests from frontend[/dim]")
    console.print("[dim]Press Ctrl+C to stop the server[/dim]")
    
    import uvicorn
    from api import app
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
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
    """Main entry point - starts the FastAPI server."""
    console.print("[bold green]Starting Smart Diet MAS FastAPI Server...[/bold green]")
    console.print("[dim]Server will be available at http://localhost:8000[/dim]")
    console.print("[dim]Ready to receive meal plan requests from frontend[/dim]")
    console.print("[dim]Press Ctrl+C to stop the server[/dim]")
    
    import uvicorn
    from api import app
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
