"""
Nutrition Planner Agent

Role: Generates a structured meal plan based on target calories, dietary goal,
      and user profile. Uses the Meal Plan Generator tool and optionally
      consults the local LLM for meal recommendations.

System Prompt:
    You are the Nutrition Planner Agent. Your job is to create a balanced daily
    meal plan that meets the user's caloric target and macronutrient goals.
    Use the food database and meal generator tools. Distribute calories across
    breakfast (25%), lunch (35%), dinner (30%), and snack (10%).

Input:  user_profile, bmi_result, target_calories
Output: daily_meal_plan

Reasoning Strategy: Tool-augmented generation. The agent uses the MealPlanGenerator
    tool for structured plan creation, then optionally uses the LLM to refine
    or add variety suggestions.
"""
from __future__ import annotations
import json
from loguru import logger
from langchain_ollama import ChatOllama
from state import AgentState
from tools.meal_plan_generator import MealPlanGeneratorTool
from tools.food_database import FoodDatabaseTool
from observability import tracer
from config import OLLAMA_MODEL, OLLAMA_BASE_URL, OLLAMA_TEMPERATURE

SYSTEM_PROMPT = """You are a professional nutritionist AI agent. Given a user's profile and caloric needs, 
you must review the generated meal plan and provide brief improvement suggestions.

Rules:
- Consider the user's BMI category when suggesting portions
- Ensure adequate protein for muscle maintenance (min 0.8g per kg body weight)
- For weight loss, prioritize high-protein, high-fiber foods
- For muscle gain, increase protein to 1.6g per kg body weight
- Always include vegetables in lunch and dinner
- Keep suggestions concise (3-5 bullet points)

Respond ONLY with a JSON object: {"suggestions": ["suggestion1", "suggestion2", ...]}"""


def nutrition_planner_node(state: AgentState) -> dict:
    """
    LangGraph node for the Nutrition Planner Agent.

    Reads: user_profile, bmi_result, target_calories
    Writes: daily_meal_plan, messages
    """
    tracer.log_agent_start("NutritionPlannerAgent", {
        "target_calories": state.get("target_calories"),
        "goal": state.get("user_profile", {}).get("dietary_goal"),
    })

    profile = state.get("user_profile", {})
    target_cal = state.get("target_calories", 2000)
    bmi = state.get("bmi_result", {})

    # ── Step 1: Generate meal plan using tool ──────────────────────────────
    food_db = FoodDatabaseTool()
    generator = MealPlanGeneratorTool(food_db)

    tracer.log_tool_usage("MealPlanGeneratorTool.generate_daily_plan", {
        "target_calories": target_cal,
        "dietary_goal": profile.get("dietary_goal", "maintenance"),
        "culture": profile.get("cultural_preference", "western"),
    }, {})

    meal_plan = generator.generate_daily_plan(
        target_calories=target_cal,
        dietary_goal=profile.get("dietary_goal", "maintenance"),
        culture=profile.get("cultural_preference", "western"),
        allergies=profile.get("allergies", []),
    )

    # ── Step 2: Consult LLM for nutritional suggestions ───────────────────
    suggestions = []
    try:
        llm = ChatOllama(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=OLLAMA_TEMPERATURE,
        )

        user_prompt = (
            f"User: {profile.get('name')}, Age: {profile.get('age')}, "
            f"Gender: {profile.get('gender')}, Weight: {profile.get('weight_kg')}kg, "
            f"Height: {profile.get('height_cm')}cm, BMI: {bmi.get('bmi_value')} ({bmi.get('category')})\n"
            f"Goal: {profile.get('dietary_goal')}, Target: {target_cal} kcal/day\n"
            f"Generated plan has {meal_plan['total_daily_calories']} kcal, "
            f"Protein: {meal_plan['total_protein_g']}g, "
            f"Carbs: {meal_plan['total_carbs_g']}g, "
            f"Fat: {meal_plan['total_fat_g']}g\n"
            f"Review this plan and provide improvement suggestions."
        )

        tracer.log_llm_call("NutritionPlannerAgent", user_prompt, "pending...")
        
        response = llm.invoke([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ])

        resp_text = response.content.strip()
        prompt = f"""
        You are an expert Clinical Nutritionist. Review the baseline 4-meal plan constructed for {profile['name']}.
        Target: {state['target_calories']} kcal | Gender: {profile['gender']} | Goal: {profile['dietary_goal']}
        
        Baseline Meals:
        {json.dumps(meal_plan, indent=2)}
        
        Provide 4 brief analytical improvements or meal-timing strategies that this user should follow to maximize their {profile['dietary_goal']} results.
        Focus on protein distribution, hydration timing, and energy management.
        Output MUST be a valid JSON list of 4 strings.
        """
        
        try:
            resp = llm.invoke(prompt)
            # Remove markdown logic if LLM includes it
            cleaned_resp = resp.content.replace('```json', '').replace('```', '').strip()
            suggestions = json.loads(cleaned_resp)
        except Exception as e:
            logger.warning(f"LLM suggestion failed: {e}")
            suggestions = ["Optimize hydration between meals", "Ensure high-protein breakfast", "Space meals 3-4 hours apart", "Avoid heavy meals late at night"]

        # Add to analytical logs
        analytical_notes = [
            f"Nutritional Strategy: Distributed {state['target_calories']} kcal across 4 meals. prioritized "
            f"{'protein' if profile['dietary_goal'] == 'muscle_gain' else 'fiber'} density based on the user's primary goal."
        ]
        analytical_notes.extend([f"Agent Recommendation: {s}" for s in suggestions])

        return {
            "daily_meal_plan": meal_plan,
            "analytical_logs": analytical_notes,
            "messages": [f"NutritionPlannerAgent generated foundation plan."],
            "current_agent": "NutritionPlannerAgent"
        }

    except Exception as e:
        logger.warning(f"LLM call failed (system will use tool-only plan): {e}")
        suggestions = ["LLM unavailable — plan generated using rule-based tools only."]

    meal_plan["llm_suggestions"] = suggestions

    messages = [
        f"[NutritionPlannerAgent] Generated meal plan: {meal_plan['total_daily_calories']} kcal",
        f"[NutritionPlannerAgent] Protein: {meal_plan['total_protein_g']}g | "
        f"Carbs: {meal_plan['total_carbs_g']}g | Fat: {meal_plan['total_fat_g']}g",
        f"[NutritionPlannerAgent] LLM suggestions: {len(suggestions)} items",
    ]

    output = {
        "daily_meal_plan": meal_plan,
        "messages": messages,
        "current_agent": "NutritionPlannerAgent",
    }

    tracer.log_agent_end("NutritionPlannerAgent", {"total_calories": meal_plan["total_daily_calories"]})
    return output
