# Smart Diet & Nutrition MAS with Cultural Adaptation

This project is a sophisticated **full-stack Multi-Agent AI System** designed to solve the complex problem of personalized nutrition and cultural meal adaptation. It runs 100% locally and adheres to university-level software engineering standards.

---

## 1. Project Overview
*   **Objective**: To deliver a personalized health companion that validates user metrics, calculates nutritional needs, generates custom meal plans, and adapts them to specific cultural preferences using autonomous AI agents.

## 2. Multi-Agent Architecture (MAS)
The core of the system is orchestrated using **LangGraph**, which manages a shared "Global State" between four autonomous agents:

| Agent | Responsibility | Logic Type |
| :--- | :--- | :--- |
| **User Profile Agent** | Validates user inputs and performs metabolic calculations (BMI, BMR, TDEE). | Deterministic (Python) |
| **Nutrition Planner Agent** | Uses targets to generate a balanced 4-meal plan (Breakfast, Lunch, Dinner, Snack). | Tool + LLM Augmented |
| **Cultural Adapter Agent** | Swaps generic foods for culturally relevant ones (e.g., Sri Lankan, Indian, East Asian). | Data-driven + LLM |
| **Calorie Analyzer Agent** | Checks plan accuracy, calculates macro-percentages, and generates the final report. | Logic + LLM Report |

## 3. Custom AI Tools
The system utilizes 4 specialized Python tools:
*   **BMI Calculator Tool**: Implements the Mifflin-St Jeor equation and WHO health categorization.
*   **Food Database Tool**: A local JSON engine with 50+ food items and substitution mappings for 6 distinct cultures.
*   **Meal Plan Generator Tool**: A rule-based algorithm that builds meals by selecting foods that fit within specific caloric "buckets."
*   **File Export Tool**: An automated reporter that saves every generated plan as both machine-readable `.json` and human-readable `.txt` files.

## 4. Technical Stack
*   **Backend**: Python, FastAPI (Web Layer), LangGraph (MAS Orchestration), Pydantic (State Validation)
*   **LLM Interface**: Ollama (locally running llama3.2) handled via langchain-ollama
*   **Frontend**: React.js (Vite), Vanilla CSS (Custom Design System), Lucide-React (Iconography)
*   **Observability**: Loguru for structured logging and a custom AgentTracer for execution flow tracking

## 5. Project Structure
```text
smart-diet-mas/
├── api.py                    # Gateway bridging MAS to the Web Dashboard
├── main.py                   # CLI version for testing and direct MAS runs
├── state.py                  # Defines the shared memory (TypedDict) between agents
├── config.py                 # Central management for LLM and Nutrition settings
├── observability.py          # The "Flight Recorder" logging all agent actions
│
├── agents/                   # THE AGENTS (The brain of the system)
│   ├── user_profile_agent.py
│   ├── nutrition_planner_agent.py
│   ├── cultural_adapter_agent.py
│   └── calorie_analyzer_agent.py
│
├── tools/                    # THE TOOLS (The hands of the system)
│   ├── bmi_calculator.py
│   ├── food_database.py
│   ├── meal_plan_generator.py
│   └── file_export.py
│
├── frontend/                 # THE DASHBOARD (The face of the system)
│   ├── src/App.jsx           # Interactive React UI
│   └── src/index.css         # Premium Glassmorphic Design System
│
├── tests/                    # THE VALIDATION (45 test cases)
└── output/                   # Auto-generated plans saved here
```

## 6. Key Innovations
*   **Cultural Mapping**: Uses a hard-coded cultural database in `data/food_database.json` to ensure nutritional accuracy during food swaps.
*   **Trace Visibility**: The "Technical Trace" feature on the dashboard proves the multi-agent collaboration.
*   **Safety Floor**: Includes a hard caloric floor (1200 kcal) for medical safety.

## 7. Installation & Setup

### Prerequisites
- Python 3.10+
- Node.js & npm
- [Ollama](https://ollama.com/) (running locally)

### Setup
1. Clone the repository and navigate to the root:
   ```bash
   cd smart-diet-mas
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Pull the required model in Ollama:
   ```bash
   ollama pull llama3.2
   ```

## 8. Development & Testing
- **Run API**: `python api.py`
- **Run Frontend**: `cd frontend && npm run dev`
- **Run Tests**: `pytest tests/test_system.py`

---
*Developed for CTSE Cloud Technologies & Software Engineering — April 2026*
