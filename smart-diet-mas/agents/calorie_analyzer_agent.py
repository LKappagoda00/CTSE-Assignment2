"""
Calorie Analyzer Agent

Role: Validates the final meal plan against the user's caloric and
      macronutrient goals. Provides a pass/fail assessment and recommendations.

System Prompt:
    You are the Calorie Analyzer Agent. Analyze the final adapted meal plan
    and determine whether it meets the user's nutritional goals. Check calorie
    deviation, protein adequacy, and macro balance. Provide actionable
    recommendations if the plan falls short.

Input:  adapted_meal_plan, user_profile, target_calories, bmi_result (including medical_conditions, dietary_restrictions)
Output: calorie_analysis, final_report

Reasoning Strategy: Rule-based calculation for objective metrics,
    LLM-augmented for generating the final narrative report.
"""
from __future__ import annotations
import json
from loguru import logger
from langchain_ollama import ChatOllama
from state import AgentState
from tools.file_export import FileExportTool
from observability import tracer
from config import OLLAMA_MODEL, OLLAMA_BASE_URL, OLLAMA_TEMPERATURE, MACRO_RATIOS

SYSTEM_PROMPT = """You are a Nutrition Analyst AI. Given a meal plan analysis with calorie/macro data,
write a concise, professional nutrition report summary (150-250 words).

Include:
1. Overview of the plan's nutritional adequacy
2. Whether it meets the stated dietary goal
3. Key strengths of the plan
4. 2-3 specific improvement recommendations
5. A brief motivational closing note

Keep the tone professional but encouraging. Do NOT use markdown formatting."""


def calorie_analyzer_node(state: AgentState) -> dict:
    """
    LangGraph node for the Calorie Analyzer Agent.

    Reads: adapted_meal_plan, user_profile, target_calories, bmi_result
    Writes: calorie_analysis, final_report, export_path, messages
    """
    tracer.log_agent_start("CalorieAnalyzerAgent", {"target": state.get("target_calories")})

    profile = state.get("user_profile", {})
    plan = state.get("adapted_meal_plan") or state.get("daily_meal_plan", {})
    target_cal = state.get("target_calories", 2000)
    bmi = state.get("bmi_result", {})

    # ── Step 1: Calculate analysis metrics ─────────────────────────────────
    actual_cal = plan.get("total_daily_calories", 0)
    actual_protein = plan.get("total_protein_g", 0)
    actual_carbs = plan.get("total_carbs_g", 0)
    actual_fat = plan.get("total_fat_g", 0)

    # Calorie deviation
    deviation = ((actual_cal - target_cal) / target_cal * 100) if target_cal > 0 else 0

    # Check if plan meets goal (within 10% deviation)
    meets_goal = abs(deviation) <= 10

    # Protein adequacy (minimum 0.8g per kg body weight)
    weight = profile.get("weight_kg", 70)
    min_protein = weight * 0.8
    goal = profile.get("dietary_goal", "maintenance")
    if goal == "muscle_gain":
        min_protein = weight * 1.6
    protein_adequate = actual_protein >= min_protein
    
    # Advanced Analytics
    protein_density = round(actual_protein / (actual_cal / 100), 2) if actual_cal > 0 else 0

    # Macronutrient breakdown (percentage of total calories)
    total_macro_cal = (actual_protein * 4) + (actual_carbs * 4) + (actual_fat * 9)
    if total_macro_cal > 0:
        macro_breakdown = {
            "protein_pct": round((actual_protein * 4) / total_macro_cal * 100, 1),
            "carbs_pct": round((actual_carbs * 4) / total_macro_cal * 100, 1),
            "fat_pct": round((actual_fat * 9) / total_macro_cal * 100, 1),
        }
    else:
        macro_breakdown = {"protein_pct": 0, "carbs_pct": 0, "fat_pct": 0}

    # Generate recommendations
    recommendations = []
    if deviation > 10:
        recommendations.append(f"Reduce portion sizes — plan exceeds target by {deviation:.1f}%")
    elif deviation < -10:
        recommendations.append(f"Increase portions or add snacks — plan is {abs(deviation):.1f}% below target")
    if not protein_adequate:
        recommendations.append(f"Increase protein intake — currently {actual_protein:.0f}g, need {min_protein:.0f}g minimum")
    target_macros = MACRO_RATIOS.get(goal, MACRO_RATIOS["maintenance"])
    if macro_breakdown["fat_pct"] > target_macros["fat"] * 100 + 10:
        recommendations.append("Consider reducing fat intake by choosing leaner cooking methods")
    if macro_breakdown["protein_pct"] < target_macros["protein"] * 100 - 10:
        recommendations.append("Add more protein-rich foods to better meet macro targets")
    if not recommendations:
        recommendations.append("Plan looks well-balanced! Maintain consistency for best results.")

    analysis = {
        "target_calories": target_cal,
        "actual_calories": actual_cal,
        "calorie_deviation": round(deviation, 1),
        "meets_goal": meets_goal,
        "protein_adequate": protein_adequate,
        "min_protein_needed": round(min_protein, 1),
        "actual_protein": actual_protein,
        "macronutrient_breakdown": macro_breakdown,
        "recommendations": recommendations,
    }

    tracer.log_tool_usage("CalorieAnalysis", {
        "target": target_cal, "actual": actual_cal, "deviation": f"{deviation:.1f}%"
    }, {"meets_goal": meets_goal})

    # ── Step 2: Generate narrative report via LLM ─────────────────────────
    final_report = _generate_report_fallback(profile, bmi, plan, analysis)
    try:
        llm = ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL, temperature=0.5)
        prompt = (
            f"User: {profile.get('name')}, Goal: {goal}, BMI: {bmi.get('bmi_value')} ({bmi.get('category')})\n"
            f"Target: {target_cal} kcal | Actual: {actual_cal} kcal | Deviation: {deviation:.1f}%\n"
            f"Protein: {actual_protein}g (need {min_protein:.0f}g) | "
            f"Macros: P:{macro_breakdown['protein_pct']}% C:{macro_breakdown['carbs_pct']}% F:{macro_breakdown['fat_pct']}%\n"
            f"Meets goal: {meets_goal} | Culture: {plan.get('culture', 'N/A')}\n"
            f"Recommendations: {'; '.join(recommendations)}\n"
            f"Write a concise nutrition report summary."
        )
        tracer.log_llm_call("CalorieAnalyzerAgent", prompt[:100], "pending")
        resp = llm.invoke([{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}])
        final_report = resp.content.strip()
        tracer.log_llm_call("CalorieAnalyzerAgent", prompt[:100], final_report[:200])
    except Exception as e:
        logger.warning(f"LLM report generation failed: {e}")

    # ── Step 3: Export results ─────────────────────────────────────────────
    export_data = {
        "user_profile": profile,
        "bmi_result": bmi,
        "adapted_meal_plan": plan,
        "calorie_analysis": analysis,
        "final_report": final_report,
    }
    exporter = FileExportTool()
    tracer.log_tool_usage("FileExportTool.export_final_report", {}, {})
    try:
        json_path, txt_path = exporter.export_final_report(export_data)
        export_msg = f"Exported to {json_path} and {txt_path}"
    except Exception as e:
        logger.error(f"Export failed: {e}")
        json_path, txt_path = "", ""
        export_msg = f"Export failed: {e}"

    messages = [
        f"[CalorieAnalyzerAgent] Analysis: {actual_cal} kcal vs {target_cal} target ({deviation:.1f}%)",
        f"[CalorieAnalyzerAgent] Meets goal: {meets_goal} | Protein adequate: {protein_adequate}",
        f"[CalorieAnalyzerAgent] {export_msg}",
    ]

    output = {
        "calorie_analysis": analysis,
        "final_report": final_report,
        "export_path": txt_path,
        "messages": messages,
        "current_agent": "CalorieAnalyzerAgent",
    }

    tracer.log_agent_end("CalorieAnalyzerAgent", {"meets_goal": meets_goal, "deviation": deviation})
    return output


def _generate_report_fallback(profile: dict, bmi: dict, plan: dict, analysis: dict) -> str:
    """Generate a text report without LLM (fallback)."""
    lines = [
        f"NUTRITION REPORT FOR {profile.get('name', 'User').upper()}",
        f"{'=' * 50}",
        f"BMI: {bmi.get('bmi_value', 'N/A')} ({bmi.get('category', 'N/A')})",
        f"Goal: {profile.get('dietary_goal', 'N/A')}",
        f"Target Calories: {analysis['target_calories']} kcal/day",
        f"Actual Calories: {analysis['actual_calories']} kcal/day",
        f"Deviation: {analysis['calorie_deviation']:.1f}%",
        f"Meets Goal: {'Yes' if analysis['meets_goal'] else 'No'}",
        f"Protein Adequate: {'Yes' if analysis['protein_adequate'] else 'No'}",
        "",
        "RECOMMENDATIONS:",
    ]
    for r in analysis.get("recommendations", []):
        lines.append(f"  • {r}")
    return "\n".join(lines)
