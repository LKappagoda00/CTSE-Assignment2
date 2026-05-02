# Technical Report: Smart Diet & Nutrition Multi-Agent System (CTSE)

**Course:** Cloud Technologies & Software Engineering  
**Assignment:** Multi-Agent System Design & Implementation  
**Submission Date:** May 2026  

---

## 1. System Architecture Workflow
The system is orchestrated using **LangGraph** to manage the state passed between four specialized autonomous agents. Each agent occupies a specific node in a Directed Acyclic Graph (DAG), ensuring a deterministic and traceable handoff of metabolic and nutritional data.

## 2. Professional Agent Outputs & Implementation

### Agent 1: User Profile Agent
*   **Role**: Validates user inputs and performs metabolic calculations (BMI, BMR, TDEE).
*   **System Prompt**: 
    > You are the User Profile Agent in a Multi-Agent Nutrition System. Your task is to calculate metabolic data using the Mifflin-St Jeor equation, validate inputs, and pass the data forward. All calculations must be deterministic and highly precise.

**Output Example (JSON):**
```json
{
  "agent": "user_profile_agent",
  "status": "success",
  "timestamp": "2026-05-01T11:34:00+05:30",
  "input_data": {
    "age": 28,
    "gender": "male",
    "weight_kg": 78.0,
    "height_cm": 175.0,
    "activity_factor": 1.55,
    "cultural_preference": "Sri Lankan"
  },
  "metrics": {
    "bmi": 25.47,
    "bmi_category": "Overweight",
    "bmr": 1745.2,
    "tdee": 2705.0
  }
}
```

### Agent 2: Nutrition Planner Agent
*   **Role**: Uses metabolic targets to generate a balanced 4-meal plan.
*   **System Prompt**:
    > You are the Nutrition Planner Agent. Use the TDEE provided by the User Profile Agent to construct a 4-meal plan (Breakfast, Lunch, Dinner, Snack). Do not allow caloric totals to drop below the 1200 kcal safety floor. Use the custom meal plan generator tool to build the meal structure.

**Output Example (JSON):**
```json
{
  "agent": "nutrition_planner_agent",
  "status": "success",
  "meal_plan": {
    "calories_target": 2500.0,
    "meals": [
      {
        "name": "Breakfast",
        "food": "Oats, Eggs, and Milk",
        "calories": 600,
        "macros": {"protein": 35, "carbs": 65, "fat": 15}
      },
      ...
    ]
  }
}
```

### Agent 3: Cultural Adapter Agent
*   **Role**: Swaps generic foods for culturally relevant ones.
*   **System Prompt**:
    > You are the Cultural Adapter Agent. Read the generic meal plan from the Nutrition Planner Agent, access the Food Database Tool to look up cultural food mappings, and adapt the meals to the target culture while maintaining the exact macro/calorie ranges.

**Output Example (JSON):**
```json
{
  "agent": "cultural_adapter_agent",
  "status": "success",
  "target_culture": "Sri Lankan",
  "modifications": [
    {
      "original": "Oats, Eggs, and Milk",
      "adapted": "Milk Rice (Kiri Bath) with Lunu Miris and Boiled Egg",
      "calories": 595,
      "macros": {"protein": 32, "carbs": 66, "fat": 14}
    }
  ]
}
```

### Agent 4: Calorie Analyzer Agent
*   **Role**: Checks plan accuracy, calculates macro-percentages, and generates the final report.
*   **System Prompt**:
    > You are the Calorie Analyzer Agent. Audit the adapted meal plan for nutritional balance, enforce the minimum safety caloric floor, and produce a final formatted output for the user. Ensure your system prompt instructions prevent hallucinations.

**Output Example (JSON):**
```json
{
  "agent": "calorie_analyzer_agent",
  "status": "audit_passed",
  "audit_details": {
    "total_calories": 2510.0,
    "protein_total_g": 167.0,
    "caloric_floor_status": "VALID",
    "macro_percentage": {
      "protein": "26.6%", "carbs": "39.0%", "fat": "23.6%"
    }
  },
  "summary_report": "The Smart Diet & Nutrition System has generated a culturally adapted 4-meal plan suitable for your metabolic baseline."
}
```

## 3. Recommended Individual Assignment Layout

| Team Member | Agent Developed | Custom Tool Developed | Testing / Validation Script |
| :--- | :--- | :--- | :--- |
| **Student 1** | UserProfileAgent | BMICalculatorTool | Unit test for BMR formulas |
| **Student 2** | NutritionPlannerAgent | MealPlanGeneratorTool | Safety floor constraints validation |
| **Student 3** | CulturalAdapterAgent | FoodDatabaseTool | Property-based cultural translation test |
| **Student 4** | CalorieAnalyzerAgent | FileExportTool | "LLM-as-a-Judge" accuracy test |

---

## 4. Technical Stack
- **Orchestration**: LangGraph (Shared State Graph)
- **API**: FastAPI (Uvicorn)
- **LLM**: Ollama (Llama 3.2 Locally Hosted)
- **Frontend**: React + Vite (Custom CSS Design)
- **Storage**: JSON Food Database with Cultural Mappings

## 5. Conclusion
This Multi-Agent System demonstrates industrial-grade AI development by separating deterministic medical logic from heuristic nutritional planning. The result is a robust, safe, and culturally aware health assistant.
