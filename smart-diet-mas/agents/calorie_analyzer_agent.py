"""
Calorie Analyzer Agent

Role: Validates the final meal plan against the user's caloric and
      macronutrient goals. Provides a pass/fail assessment and recommendations.

System Prompt:
    You are the Calorie Analyzer Agent. Analyze the final adapted meal plan
    and determine whether it meets the user's nutritional goals. Check calorie
    deviation, protein adequacy, and macro balance. Provide actionable
    recommendations if the plan falls short.

Input:  adapted_meal_plan, user_profile, target_calories, bmi_result
Output: calorie_analysis, final_report

Reasoning Strategy: Rule-based calculation for objective metrics,
    LLM-augmented for generating the final narrative report.
"""
from __future__ import annotations

from typing import Any

from loguru import logger
from langchain_ollama import ChatOllama

from config import MACRO_RATIOS, OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TEMPERATURE
from observability import tracer
from state import AgentState
from tools.file_export import FileExportTool

# ── System Prompt ──────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a Nutrition Analyst AI. Given a meal plan analysis with calorie/macro data,
write a concise, professional nutrition report summary (150-250 words).

Include:
1. Overview of the plan's nutritional adequacy
2. Whether it meets the stated dietary goal
3. Key strengths of the plan
4. 2-3 specific improvement recommendations
5. A brief motivational closing note

Keep the tone professional but encouraging. Do NOT use markdown formatting."""


def calorie_analyzer_node(state: AgentState) -> dict[str, Any]:
    """
    LangGraph node for the Calorie Analyzer Agent.

    Reads:  adapted_meal_plan, user_profile, target_calories, bmi_result
    Writes: calorie_analysis, final_report, export_paths, messages, current_agent

    Args:
        state: The current LangGraph AgentState.

    Returns:
        A dictionary of state updates to be merged into AgentState.
    """
    tracer.log_agent_start(
        "CalorieAnalyzerAgent", {"target": state.get("target_calories")}
    )

    profile: dict[str, Any] = state.get("user_profile", {})
    plan: dict[str, Any] = state.get("adapted_meal_plan") or state.get("daily_meal_plan", {})
    target_cal: float = state.get("target_calories", 2000)
    bmi: dict[str, Any] = state.get("bmi_result", {})

    # ── Step 1: Calculate analysis metrics ────────────────────────────────
    actual_cal: float = plan.get("total_daily_calories", 0)
    actual_protein: float = plan.get("total_protein_g", 0)
    actual_carbs: float = plan.get("total_carbs_g", 0)
    actual_fat: float = plan.get("total_fat_g", 0)

    # Calorie deviation
    deviation: float = (
        ((actual_cal - target_cal) / target_cal * 100) if target_cal > 0 else 0
    )

    # Check if plan meets goal (within ±10% deviation)
    meets_goal: bool = abs(deviation) <= 10

    # Protein adequacy (minimum 0.8g per kg body weight)
    weight: float = profile.get("weight_kg", 70)
    goal: str = profile.get("dietary_goal", "maintenance")
    min_protein: float = weight * 1.6 if goal == "muscle_gain" else weight * 0.8
    protein_adequate: bool = actual_protein >= min_protein

    # Protein density per 100 kcal (FIX: now included in analysis output)
    protein_density: float = (
        round(actual_protein / (actual_cal / 100), 2) if actual_cal > 0 else 0
    )

    # Macronutrient breakdown (percentage of total calories)
    total_macro_cal: float = (
        (actual_protein * 4) + (actual_carbs * 4) + (actual_fat * 9)
    )
    if total_macro_cal > 0:
        macro_breakdown: dict[str, float] = {
            "protein_pct": round((actual_protein * 4) / total_macro_cal * 100, 1),
            "carbs_pct": round((actual_carbs * 4) / total_macro_cal * 100, 1),
            "fat_pct": round((actual_fat * 9) / total_macro_cal * 100, 1),
        }
    else:
        macro_breakdown = {"protein_pct": 0.0, "carbs_pct": 0.0, "fat_pct": 0.0}

    # Generate recommendations
    recommendations: list[str] = []
    if deviation > 10:
        recommendations.append(
            f"Reduce portion sizes — plan exceeds target by {deviation:.1f}%"
        )
    elif deviation < -10:
        recommendations.append(
            f"Increase portions or add snacks — plan is {abs(deviation):.1f}% below target"
        )
    if not protein_adequate:
        recommendations.append(
            f"Increase protein intake — currently {actual_protein:.0f}g, "
            f"need {min_protein:.0f}g minimum"
        )

    target_macros: dict[str, float] = MACRO_RATIOS.get(goal, MACRO_RATIOS["maintenance"])
    if macro_breakdown["fat_pct"] > target_macros["fat"] * 100 + 10:
        recommendations.append(
            "Consider reducing fat intake by choosing leaner cooking methods"
        )
    if macro_breakdown["protein_pct"] < target_macros["protein"] * 100 - 10:
        recommendations.append(
            "Add more protein-rich foods to better meet macro targets"
        )
    if not recommendations:
        recommendations.append(
            "Plan looks well-balanced! Maintain consistency for best results."
        )

    analysis: dict[str, Any] = {
        "target_calories": target_cal,
        "actual_calories": actual_cal,
        "calorie_deviation": round(deviation, 1),
        "meets_goal": meets_goal,
        "protein_adequate": protein_adequate,
        "min_protein_needed": round(min_protein, 1),
        "actual_protein": actual_protein,
        "protein_density_per_100kcal": protein_density,   # FIX: now included
        "macronutrient_breakdown": macro_breakdown,
        "recommendations": recommendations,
    }

    tracer.log_tool_usage(
        "CalorieAnalysis",
        {"target": target_cal, "actual": actual_cal, "deviation": f"{deviation:.1f}%"},
        {"meets_goal": meets_goal},
    )

    # ── Step 2: Generate narrative report via LLM ─────────────────────────
    # Set deterministic fallback first — system never crashes if LLM is down
    final_report: str = _generate_report_fallback(profile, bmi, plan, analysis)

    # FIX: Safely resolve bmi values before passing to LLM prompt
    bmi_value: Any = bmi.get("bmi_value", "N/A")
    bmi_category: str = bmi.get("category", "N/A")

    try:
        llm = ChatOllama(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=OLLAMA_TEMPERATURE,
        )
        prompt = (
            f"User: {profile.get('name', 'User')}, Goal: {goal}, "
            f"BMI: {bmi_value} ({bmi_category})\n"
            f"Target: {target_cal} kcal | Actual: {actual_cal} kcal | "
            f"Deviation: {deviation:.1f}%\n"
            f"Protein: {actual_protein}g (need {min_protein:.0f}g) | "
            f"Macros: P:{macro_breakdown['protein_pct']}% "
            f"C:{macro_breakdown['carbs_pct']}% "
            f"F:{macro_breakdown['fat_pct']}%\n"
            f"Meets goal: {meets_goal} | Culture: {plan.get('culture', 'N/A')}\n"
            f"Recommendations: {'; '.join(recommendations)}\n"
            f"Write a concise nutrition report summary."
        )

        tracer.log_llm_call("CalorieAnalyzerAgent", prompt[:100], "pending")
        resp = llm.invoke(
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ]
        )
        llm_text: str = resp.content.strip()

        # FIX: Strip markdown formatting in case LLM ignores the instruction
        for md_token in ("**", "##", "# ", "```", "---"):
            llm_text = llm_text.replace(md_token, "")

        final_report = llm_text
        tracer.log_llm_call(
            "CalorieAnalyzerAgent", prompt[:100], final_report[:200]
        )

    except Exception as e:
        logger.warning(f"LLM report generation failed, using fallback: {e}")

    # ── Step 3: Export results ─────────────────────────────────────────────
    export_data: dict[str, Any] = {
        "user_profile": profile,
        "bmi_result": bmi,
        "adapted_meal_plan": plan,
        "calorie_analysis": analysis,
        "final_report": final_report,
    }

    exporter = FileExportTool()
    json_path: str = ""
    txt_path: str = ""

    try:
        json_path, txt_path = exporter.export_final_report(export_data)
        export_msg = f"Exported to {json_path} and {txt_path}"
        # FIX: log_tool_usage called AFTER export with actual result paths
        tracer.log_tool_usage(
            "FileExportTool.export_final_report",
            {"data_keys": list(export_data.keys())},
            {"json_path": json_path, "txt_path": txt_path},
        )
    except Exception as e:
        logger.error(f"Export failed: {e}")
        export_msg = f"Export failed: {e}"

    messages: list[str] = [
        f"[CalorieAnalyzerAgent] Analysis: {actual_cal} kcal vs "
        f"{target_cal} target ({deviation:.1f}%)",
        f"[CalorieAnalyzerAgent] Meets goal: {meets_goal} | "
        f"Protein adequate: {protein_adequate}",
        f"[CalorieAnalyzerAgent] {export_msg}",
    ]

    output: dict[str, Any] = {
        "calorie_analysis": analysis,
        "final_report": final_report,
        # FIX: both paths preserved in state — not just txt_path
        "export_paths": {"json": json_path, "txt": txt_path},
        "messages": messages,
        "current_agent": "CalorieAnalyzerAgent",
    }

    tracer.log_agent_end(
        "CalorieAnalyzerAgent", {"meets_goal": meets_goal, "deviation": deviation}
    )
    return output


def _generate_report_fallback(
    profile: dict[str, Any],
    bmi: dict[str, Any],
    plan: dict[str, Any],
    analysis: dict[str, Any],
) -> str:
    """
    Generate a plain-text nutrition report without LLM (deterministic fallback).

    Used automatically when the Ollama LLM is unavailable or returns an error.

    Args:
        profile: Validated user profile dictionary.
        bmi:     BMI result dictionary from calculate_bmi().
        plan:    Adapted meal plan dictionary.
        analysis: Calorie analysis metrics dictionary.

    Returns:
        A formatted plain-text nutrition report string.

    Example:
        >>> report = _generate_report_fallback(profile, bmi, plan, analysis)
        >>> print(report[:30])
        'NUTRITION REPORT FOR ...'
    """
    lines: list[str] = [
        f"NUTRITION REPORT FOR {profile.get('name', 'User').upper()}",
        "=" * 50,
        f"BMI:             {bmi.get('bmi_value', 'N/A')} ({bmi.get('category', 'N/A')})",
        f"Goal:            {profile.get('dietary_goal', 'N/A')}",
        f"Target Calories: {analysis['target_calories']} kcal/day",
        f"Actual Calories: {analysis['actual_calories']} kcal/day",
        f"Deviation:       {analysis['calorie_deviation']:.1f}%",
        f"Meets Goal:      {'Yes' if analysis['meets_goal'] else 'No'}",
        f"Protein Adequate:{'Yes' if analysis['protein_adequate'] else 'No'}",
        "",
        "RECOMMENDATIONS:",
    ]
    for rec in analysis.get("recommendations", []):
        lines.append(f"  • {rec}")
    return "\n".join(lines)