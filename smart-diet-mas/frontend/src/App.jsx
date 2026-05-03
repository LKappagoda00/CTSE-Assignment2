import React, { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import { 
  Activity, User, Utensils, ChevronRight, ChevronLeft, CheckCircle2, 
  Loader2, AlertCircle, Zap, Globe, Target, FileText, BrainCircuit, 
  Calculator, Scale, ArrowRight, Terminal, Cpu, Database, Droplet, BarChart3,
  Lightbulb, Info, ShieldCheck
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

const API_BASE = 'http://localhost:8000'

const STEPS = [
  { id: 0, name: 'Input Profile', icon: User, color: '#f8fafc' },
  { id: 1, name: 'UserProfileAgent', icon: Calculator, sub: 'Metabolic Logic', color: '#4ade80' },
  { id: 2, name: 'NutritionPlannerAgent', icon: Utensils, sub: 'Meal Architecture', color: '#8b5cf6' },
  { id: 3, name: 'CulturalAdapterAgent', icon: Globe, sub: 'Cuisine Adaptation', color: '#fbbf24' },
  { id: 4, name: 'CalorieAnalyzerAgent', icon: Scale, sub: 'Nutrition Audit', color: '#f43f5e' }
]

function App() {
  const [currentStep, setCurrentStep] = useState(0)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [cultures, setCultures] = useState([])
  const [logIndex, setLogIndex] = useState(0)
  const logEndRef = useRef(null)
  const [pastData, setPastData] = useState([])
  const [formData, setFormData] = useState({
    name: 'Kasun Perera', age: 28, gender: 'male', weight_kg: 78, height_cm: 175,
    activity_level: 'moderately_active', dietary_goal: 'weight_loss', cultural_preference: 'sri_lankan', allergies: [],
    medical_conditions: [], dietary_restrictions: [], preferred_foods: ['rice', 'chicken', 'vegetables'], disliked_foods: ['fish'],
    budget_per_day: 30, cooking_time_available: 'moderate'
  })

  useEffect(() => { fetchCultures() }, [])
  useEffect(() => { fetchPastData() }, [])  // Fetch past data on load
  useEffect(() => { if (loading && result) scrollToBottom() }, [logIndex])

  const scrollToBottom = () => logEndRef.current?.scrollIntoView({ behavior: 'smooth' })

  const fetchCultures = async () => {
    try {
      const resp = await axios.get(`${API_BASE}/cultures`)
      setCultures(resp.data.cultures)
    } catch (err) { console.error('Failed to fetch cultures', err) }
  }

  const fetchPastData = async () => {
    try {
      const resp = await axios.get(`${API_BASE}/past-data`)
      setPastData(resp.data.past_data)
    } catch (err) { console.error('Failed to fetch past data', err) }
  }

  const loadPastPlan = async (planId) => {
    try {
      const resp = await axios.get(`${API_BASE}/past-data/${planId}`)
      setResult(resp.data.result)
      setCurrentStep(1)
    } catch (err) { console.error('Failed to load past plan', err) }
  }

  const runWorkflow = async () => {
    setLoading(true)
    setError(null)
    setLogIndex(0)
    setResult(null)
    try {
      const resp = await axios.post(`${API_BASE}/generate-plan`, formData)
      // Pulsing logs simulation
      for (let i = 0; i < resp.data.messages.length; i++) {
        setLogIndex(i + 1)
        await new Promise(r => setTimeout(r, 400))
      }
      setResult(resp.data)
      setCurrentStep(1)
      fetchPastData()  // Refresh past data after new run
    } catch (err) {
      setError(err.response?.data?.detail || 'Is the backend active? (python api.py)')
    } finally {
      setLoading(false)
    }
  }

  // ── Helper Components ────────────────────────────────────────────────────────

  const HandoffCard = ({ text, color }) => (
    <div className="handoff-card" style={{ borderLeft: `4px solid ${color}` }}>
      <div style={{ display: 'flex', gap: '0.75rem' }}>
        <Cpu size={18} color={color} />
        <div>
          <div style={{ fontSize: '0.75rem', fontWeight: '800', color: 'var(--text-dim)', marginBottom: '0.2rem' }}>DATA HANDOFF</div>
          <p style={{ fontSize: '0.85rem' }}>{text}</p>
        </div>
      </div>
    </div>
  )

  const IntelligenceLog = ({ logs }) => (
    <div className="glass-card intel-sidebar">
      <div className="sidebar-header">
        <Lightbulb size={20} color="var(--primary)" />
        <h4>Agent Intelligence</h4>
      </div>
      <div className="log-container">
        {logs && logs.length > 0 ? logs.map((log, i) => (
          <motion.div initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.1 }} key={i} className="log-item">
            <div className="log-dot" />
            {log}
          </motion.div>
        )) : (
          <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-dim)', fontSize: '0.8rem' }}>
            Awaiting agent execution...
          </div>
        )}
      </div>
      <div className="sidebar-footer">
        <ShieldCheck size={14} /> Verified Logical Reasoning
      </div>
    </div>
  )

  const nextStep = () => setCurrentStep(prev => Math.min(prev + 1, 4))
  const prevStep = () => setCurrentStep(prev => Math.max(prev - 1, 0))

  return (
    <div className="app-container">
      {/* Header */}
      <nav className="nav fade-in">
        <div className="logo" onClick={() => {setResult(null); setCurrentStep(0)}} style={{ cursor: 'pointer' }}>VITALITY MAS</div>
        <div className="dashboard-pill">
          <div className="pulse-dot"></div> MULTI-AGENT ORCHESTRATOR
        </div>
      </nav>

      {/* Stepper */}
      <div className="stepper-track fade-in">
        {STEPS.map((step, idx) => (
          <div key={idx} className={`step-node ${currentStep === idx ? 'current' : ''} ${currentStep > idx ? 'done' : ''}`} onClick={() => result && setCurrentStep(idx)}>
            <div className="node-circle" style={{ borderColor: currentStep >= idx ? step.color : 'rgba(255,255,255,0.1)' }}>
              <step.icon size={16} color={currentStep >= idx ? step.color : 'var(--text-dim)'} />
            </div>
            <div className="node-label">
              <span className="node-name">{step.name}</span>
              <span className="node-sub">{step.sub}</span>
            </div>
          </div>
        ))}
      </div>

      <main style={{ marginTop: '2rem' }}>
        <AnimatePresence mode="wait">
          {currentStep === 0 && (
            <motion.div key="st0" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="grid" style={{ gridTemplateColumns: '1fr 1fr 1fr', gap: '2rem' }}>
              <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
                  <BrainCircuit size={28} color="var(--primary)" />
                  <h3 style={{ fontSize: '1.5rem' }}>Personalized Nutrition Intelligence</h3>
                </div>
                <div className="workflow-diagram">
                   {/* Visual nodes with dotted lines */}
                   {STEPS.slice(1).map((s, i) => (
                     <React.Fragment key={i}>
                       <div className="diag-node">
                         <s.icon size={20} />
                         <span>{s.name.replace('Agent', '')}</span>
                       </div>
                       {i < 3 && <div className="diag-line" />}
                     </React.Fragment>
                   ))}
                </div>
                <div className="console-preview">
                  <div className="console-header"><Terminal size={12} /> SESSION_LOG</div>
                  <div className="console-body">
                    {loading ? result?.messages.slice(0, logIndex).map((m, i) => <div key={i} className="c-line text-green">{m}</div>) : <div className="c-line text-dim">Click "Launch Intelligence System" to start the workflow.</div>}
                    <div ref={logEndRef} />
                  </div>
                </div>
              </div>

              <div className="glass-card">
                <h3>Biometric Input</h3>
                <form onSubmit={e => { e.preventDefault(); runWorkflow() }} className="form-grid">
                  <div className="fg full"><label>NAME</label><input type="text" name="name" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} /></div>
                  <div className="fg"><label>AGE</label><input type="number" name="age" value={formData.age} onChange={e => setFormData({...formData, age: e.target.value})} /></div>
                  <div className="fg"><label>GENDER</label>
                    <select name="gender" value={formData.gender} onChange={e => setFormData({...formData, gender: e.target.value})}>
                      <option value="male">Male</option><option value="female">Female</option><option value="other">Other</option>
                    </select>
                  </div>
                  <div className="fg"><label>WEIGHT (KG)</label><input type="number" name="weight_kg" value={formData.weight_kg} onChange={e => setFormData({...formData, weight_kg: e.target.value})} /></div>
                  <div className="fg"><label>HEIGHT (CM)*</label><input type="number" name="height_cm" value={formData.height_cm} onChange={e => setFormData({...formData, height_cm: e.target.value})} required /></div>
                  <div className="fg"><label>ACTIVITY LEVEL</label>
                    <select name="activity_level" value={formData.activity_level} onChange={e => setFormData({...formData, activity_level: e.target.value})}>
                      <option value="sedentary">Sedentary</option><option value="lightly_active">Lightly Active</option><option value="moderately_active">Moderately Active</option><option value="very_active">Very Active</option><option value="extra_active">Extra Active</option>
                    </select>
                  </div>
                  <div className="fg"><label>DIETARY GOAL</label>
                    <select name="dietary_goal" value={formData.dietary_goal} onChange={e => setFormData({...formData, dietary_goal: e.target.value})}>
                      <option value="weight_loss">Weight Loss</option><option value="muscle_gain">Muscle Gain</option><option value="maintenance">Maintenance</option><option value="healthy_eating">Healthy Eating</option>
                    </select>
                  </div>
                  <div className="fg"><label>CULTURE</label>
                    <select name="cultural_preference" value={formData.cultural_preference} onChange={e => setFormData({...formData, cultural_preference: e.target.value})}>
                      {cultures.map(c => <option key={c} value={c}>{c.toUpperCase()}</option>)}
                    </select>
                  </div>
                  <div className="fg"><label>ALLERGIES</label><input type="text" name="allergies" value={formData.allergies.join(', ')} onChange={e => setFormData({...formData, allergies: e.target.value.split(',').map(s => s.trim()).filter(s => s)})} placeholder="e.g., nuts, fish" /></div>
                  <div className="fg"><label>MEDICAL CONDITIONS</label><input type="text" name="medical_conditions" value={formData.medical_conditions.join(', ')} onChange={e => setFormData({...formData, medical_conditions: e.target.value.split(',').map(s => s.trim()).filter(s => s)})} placeholder="e.g., diabetes, hypertension" /></div>
                  <div className="fg"><label>DIETARY RESTRICTIONS</label><input type="text" name="dietary_restrictions" value={formData.dietary_restrictions.join(', ')} onChange={e => setFormData({...formData, dietary_restrictions: e.target.value.split(',').map(s => s.trim()).filter(s => s)})} placeholder="e.g., vegetarian, gluten_free" /></div>
                  <div className="fg"><label>PREFERRED FOODS</label><input type="text" name="preferred_foods" value={formData.preferred_foods.join(', ')} onChange={e => setFormData({...formData, preferred_foods: e.target.value.split(',').map(s => s.trim()).filter(s => s)})} placeholder="e.g., rice, chicken, vegetables" /></div>
                  <div className="fg"><label>DISLIKED FOODS</label><input type="text" name="disliked_foods" value={formData.disliked_foods.join(', ')} onChange={e => setFormData({...formData, disliked_foods: e.target.value.split(',').map(s => s.trim()).filter(s => s)})} placeholder="e.g., spinach, fish" /></div>
                  <div className="fg"><label>BUDGET PER DAY ($)</label><input type="number" name="budget_per_day" value={formData.budget_per_day} onChange={e => setFormData({...formData, budget_per_day: parseFloat(e.target.value) || 0})} /></div>
                  <div className="fg"><label>COOKING TIME</label>
                    <select name="cooking_time_available" value={formData.cooking_time_available} onChange={e => setFormData({...formData, cooking_time_available: e.target.value})}>
                      <option value="quick">Quick</option><option value="moderate">Moderate</option><option value="extensive">Extensive</option>
                    </select>
                  </div>
                  <button type="submit" className="btn-launch" disabled={loading}>
                    {loading ? <Loader2 className="spinning" /> : <Zap size={18} />} LAUNCH INTELLIGENCE SYSTEM
                  </button>
                </form>
                {error && <div className="err-msg">{error}</div>}
              </div>

              <div className="glass-card">
                <h3>Past Plans</h3>
                <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
                  {pastData.length > 0 ? pastData.map((plan, i) => (
                    <div key={i} className="past-plan-item" onClick={() => loadPastPlan(plan.id)} style={{ cursor: 'pointer', padding: '0.75rem', borderBottom: '1px solid rgba(255,255,255,0.1)', marginBottom: '0.5rem' }}>
                      <div style={{ fontWeight: 'bold' }}>{plan.user_name}</div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>{plan.timestamp.replace(/_/g, ' ').replace(/(\d{4})(\d{2})(\d{2}) (\d{2})(\d{2})(\d{2})/, '$1-$2-$3 $4:$5:$6')}</div>
                      <div style={{ fontSize: '0.8rem' }}>Goal: {plan.dietary_goal.replace('_', ' ')} | BMI: {plan.bmi} | Calories: {plan.target_calories}</div>
                    </div>
                  )) : <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-dim)' }}>No past plans yet</div>}
                </div>
              </div>
            </motion.div>
          )}

          {result && currentStep > 0 && (
            <motion.div key={`st${currentStep}`} initial={{ opacity: 0, x: 50 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -50 }} className="agent-page-grid">
              <div className="agent-main">
                <div className="page-header">
                  <div className="agent-badge" style={{ background: STEPS[currentStep].color }}>AGENT 0{currentStep}</div>
                  <h2 style={{ fontSize: '2.5rem', fontWeight: '800' }}>{STEPS[currentStep].name}</h2>
                </div>

                {currentStep === 1 && result.bmi_result && result.target_calories && (
                  <div className="agent-details fade-in">
                    <div className="grid">
                      <div className="glass-card data-box">
                        <div className="db-label">COMPUTED BMI</div>
                        <div className="db-value">{result.bmi_result.bmi_value}</div>
                        <div className="db-sub" style={{ color: STEPS[1].color }}>{result.bmi_result.category.toUpperCase()}</div>
                      </div>
                      <div className="glass-card data-box">
                        <div className="db-label">TARGET CALORIES</div>
                        <div className="db-value">{result.target_calories} kcal</div>
                        <div className="db-sub">DAILY INTAKE</div>
                      </div>
                    </div>
                    <HandoffCard color={STEPS[1].color} text={`UserProfileAgent translated raw inputs into a Metabolic Baseline of ${result.target_calories} kcal/day.`} />
                  </div>
                )}

                {currentStep === 1 && (!result.bmi_result || !result.target_calories) && (
                  <div className="agent-details fade-in">
                    <div className="glass-card primary-output" style={{ borderLeft: `4px solid ${STEPS[1].color}` }}>
                       <h4 style={{ color: STEPS[1].color }}>PROFILE ANALYSIS IN PROGRESS</h4>
                       <p>The UserProfileAgent is calculating your BMI and metabolic baseline...</p>
                    </div>
                    <HandoffCard color={STEPS[1].color} text={`UserProfileAgent is processing your profile data.`} />
                  </div>
                )}

                {currentStep === 2 && result.daily_meal_plan && (
                  <div className="agent-details fade-in">
                     <div className="grid" style={{ gridTemplateColumns: 'repeat(2, 1fr)' }}>
                        {result.daily_meal_plan.meals.map((m, i) => (
                          <div key={i} className="glass-card meal-view">
                            <div className="mv-type">{m.meal_type}</div>
                            <div className="mv-name">{m.items[0].food_name}</div>
                            <div className="mv-kcal">{m.total_calories} KCAL</div>
                          </div>
                        ))}
                     </div>
                     <HandoffCard color={STEPS[2].color} text={`NutritionPlannerAgent constructed a stable 4-meal architecture based on the computed TDEE of ${Math.round(result.target_calories + 500)}.`} />
                  </div>
                )}

                {currentStep === 2 && !result.daily_meal_plan && (
                  <div className="agent-details fade-in">
                     <div className="glass-card primary-output" style={{ borderLeft: `4px solid ${STEPS[2].color}` }}>
                        <h4 style={{ color: STEPS[2].color }}>MEAL PLAN GENERATION IN PROGRESS</h4>
                        <p>The NutritionPlannerAgent is currently generating your personalized meal plan...</p>
                     </div>
                     <HandoffCard color={STEPS[2].color} text={`NutritionPlannerAgent is constructing a meal architecture based on your metabolic baseline.`} />
                  </div>
                )}

                {currentStep === 3 && result.adapted_meal_plan && (
                  <div className="agent-details fade-in">
                    <div className="glass-card primary-output" style={{ borderLeft: `4px solid ${STEPS[3].color}` }}>
                       <h4 style={{ color: STEPS[3].color }}>CUISINE SPECIALIZATION: {formData.cultural_preference.toUpperCase()}</h4>
                       <div className="grid" style={{ marginTop: '1.5rem' }}>
                          {result.adapted_meal_plan.meals.slice(1, 3).map((m, i) => (
                             <div key={i} className="sub-item">
                                <span className="si-label">{m.meal_type}</span>
                                <span className="si-val">{m.items[0].food_name}</span>
                             </div>
                          ))}
                       </div>
                    </div>
                    <HandoffCard color={STEPS[3].color} text={`CulturalAdapterAgent mapped regional staples from the Food Database to maintain culinary authenticity.`}/>
                  </div>
                )}

                {currentStep === 3 && !result.adapted_meal_plan && (
                  <div className="agent-details fade-in">
                    <div className="glass-card primary-output" style={{ borderLeft: `4px solid ${STEPS[3].color}` }}>
                       <h4 style={{ color: STEPS[3].color }}>CUISINE ADAPTATION IN PROGRESS</h4>
                       <p>The CulturalAdapterAgent is currently processing cultural adaptations...</p>
                    </div>
                    <HandoffCard color={STEPS[3].color} text={`CulturalAdapterAgent is adapting the meal plan to ${formData.cultural_preference} cuisine.`}/>
                  </div>
                )}

                {currentStep === 4 && result.final_report && result.calorie_analysis && (
                   <div className="agent-details fade-in">
                      <div className="glass-card" style={{ borderLeft: `8px solid ${STEPS[4].color}`, background: 'rgba(244, 63, 94, 0.05)' }}>
                         <h3 style={{ fontSize: '1.25rem', marginBottom: '1rem' }}>FINAL SYSTEM VERDICT</h3>
                         <p className="final-text">{result.final_report}</p>
                      </div>
                      <div className="grid" style={{ marginTop: '1.5rem' }}>
                         <div className="glass-card"><strong>PROTEIN</strong> {result.calorie_analysis.macronutrient_breakdown.protein_pct}%</div>
                         <div className="glass-card"><strong>FAT</strong> {result.calorie_analysis.macronutrient_breakdown.fat_pct}%</div>
                      </div>
                      <button onClick={() => {setResult(null); setCurrentStep(0)}} className="btn-restart">RESTART ORCHESTRATION</button>
                   </div>
                )}

                {currentStep === 4 && (!result.final_report || !result.calorie_analysis) && (
                   <div className="agent-details fade-in">
                      <div className="glass-card" style={{ borderLeft: `8px solid ${STEPS[4].color}`, background: 'rgba(244, 63, 94, 0.05)' }}>
                         <h3 style={{ fontSize: '1.25rem', marginBottom: '1rem' }}>ANALYSIS IN PROGRESS</h3>
                         <p>The CalorieAnalyzerAgent is performing final nutritional analysis...</p>
                      </div>
                      <HandoffCard color={STEPS[4].color} text={`CalorieAnalyzerAgent is validating the meal plan against nutritional targets.`} />
                   </div>
                )}

                <div className="nav-controls">
                  <button onClick={prevStep} className="btn-nav"><ChevronLeft /> PREVIOUS</button>
                  {currentStep < 4 && <button onClick={nextStep} className="btn-nav" style={{ borderColor: STEPS[currentStep+1].color }}>PROCEED TO {STEPS[currentStep+1].name.replace('Agent', '').toUpperCase()} <ChevronRight /></button>}
                </div>
              </div>

              <div className="agent-sidebar">
                <IntelligenceLog logs={result.analytical_logs} />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      <style dangerouslySetInnerHTML={{ __html: `
        :root { --p: #4ade80; --bg: #030712; --card: #111827; --text: #f9fafb; --dim: #94a3b8; }
        * { box-sizing: border-box; }
        body { background: var(--bg); color: var(--text); }
        .app-container { max-width: 1300px; margin: 0 auto; padding: 2rem 4rem; overflow: hidden; }
        .nav { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4rem; }
        .logo { font-size: 1.5rem; font-weight: 900; letter-spacing: -1px; background: linear-gradient(to right, #4ade80, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .dashboard-pill { background: rgba(255,255,255,0.05); padding: 0.5rem 1rem; border-radius: 99px; font-size: 0.7rem; font-weight: 800; color: var(--p); display: flex; gap: 0.5rem; align-items: center; border: 1px solid rgba(74, 222, 128, 0.2); }
        .glass-card { background: var(--card); border: 1px solid rgba(255,255,255,0.05); border-radius: 1.25rem; padding: 1.5rem; }
        
        .stepper-track { display: flex; justify-content: space-between; margin-bottom: 4rem; padding: 0 1rem; }
        .step-node { display: flex; align-items: center; gap: 0.75rem; opacity: 0.2; transform: scale(0.95); transition: all 0.4s ease; cursor: pointer; }
        .step-node.current { opacity: 1; transform: scale(1.05); }
        .step-node.done { opacity: 0.6; }
        .node-circle { width: 36px; height: 36px; border-radius: 50%; border: 2px solid; display: flex; align-items: center; justify-content: center; }
        .node-label { display: flex; flex-direction: column; }
        .node-name { font-size: 0.7rem; font-weight: 900; }
        .node-sub { font-size: 0.6rem; color: var(--dim); }

        .btn-launch { background: var(--p); color: #000; border: none; padding: 1rem; border-radius: 0.75rem; font-weight: 900; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 0.5rem; transition: transform 0.2s; }
        .btn-launch:hover { transform: translateY(-2px); box-shadow: 0 10px 30px rgba(74, 222, 128, 0.3); }
        .form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-top: 1.5rem; }
        .fg { display: flex; flex-direction: column; gap: 0.4rem; }
        .fg.full { grid-column: span 2; }
        label { font-size: 0.65rem; font-weight: 800; color: var(--dim); letter-spacing: 1px; }
        input, select { background: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.1); padding: 0.75rem; border-radius: 0.5rem; color: white; font-family: inherit; }

        .agent-page-grid { display: grid; grid-template-columns: 1fr 350px; gap: 2rem; }
        .agent-badge { font-size: 0.65rem; font-weight: 900; color: #000; padding: 0.3rem 0.6rem; border-radius: 0.4rem; margin-bottom: 1rem; width: fit-content; }
        .data-box { text-align: center; }
        .db-label { font-size: 0.65rem; font-weight: 800; color: var(--dim); }
        .db-value { font-size: 2.5rem; font-weight: 900; margin: 0.5rem 0; }
        .db-sub { font-size: 0.75rem; font-weight: 800; }

        .past-plan-item:hover { background: rgba(255,255,255,0.05); border-radius: 0.5rem; }
        .intel-sidebar { height: 100%; display: flex; flex-direction: column; background: #0b1120; border-color: rgba(139, 92, 246, 0.2); }
        .sidebar-header { display: flex; align-items: center; gap: 0.75rem; padding-bottom: 1rem; border-bottom: 1px solid rgba(255,255,255,0.05); }
        .log-container { flex: 1; padding: 1.5rem 0; overflow-y: auto; display: flex; flex-direction: column; gap: 1.25rem; }
        .log-item { font-size: 0.85rem; line-height: 1.6; color: #cbd5e1; position: relative; padding-left: 1.25rem; }
        .log-dot { position: absolute; left: 0; top: 8px; width: 6px; height: 6px; border-radius: 50%; background: #4ade80; }
        .sidebar-footer { font-size: 0.65rem; color: #64748b; padding-top: 1rem; border-top: 1px solid rgba(255,255,255,0.05); display: flex; align-items: center; gap: 0.4rem; }

        .nav-controls { display: flex; justify-content: space-between; margin-top: 3rem; }
        .btn-nav { background: transparent; border: 1px solid rgba(255,255,255,0.1); color: white; padding: 0.75rem 1.5rem; border-radius: 0.5rem; cursor: pointer; font-weight: 800; display: flex; align-items: center; gap: 0.5rem; }
        .btn-nav:hover { background: rgba(255,255,255,0.05); }
        
        .pulse-dot { width: 8px; height: 8px; background: var(--p); border-radius: 50%; animation: pulse 2s infinite; }
        @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(74, 222, 128, 0.7); } 70% { box-shadow: 0 0 0 8px rgba(74, 222, 128, 0); } 100% { box-shadow: 0 0 0 0 rgba(74, 222, 128, 0); } }
        .spinning { animation: spin 2s linear infinite; }
        @keyframes spin { 100% { transform: rotate(360deg); } }
        
        /* Workflow Diag */
        .workflow-diagram { display: flex; align-items: center; justify-content: space-between; margin-bottom: 2rem; }
        .diag-node { display: flex; flex-direction: column; align-items: center; gap: 0.5rem; font-size: 0.6rem; font-weight: 800; color: var(--dim); }
        .diag-node svg { background: rgba(255,255,255,0.05); padding: 0.75rem; border-radius: 50%; color: var(--p); }
        .diag-line { flex: 1; height: 1px; border-top: 1px dashed rgba(255,255,255,0.2); margin: 0 0.5rem; }
        .console-preview { background: #000; border-radius: 0.75rem; border: 1px solid rgba(255,255,255,0.1); flex: 1; overflow: hidden; display: flex; flex-direction: column; }
        .console-header { background: rgba(255,255,255,0.05); padding: 0.4rem 0.75rem; font-size: 0.6rem; font-weight: 900; color: var(--dim); }
        .console-body { padding: 1rem; overflow-y: auto; height: 180px; font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; }
        .text-green { color: #4ade80; }
        .text-dim { color: #475569; }
      `}} />
    </div>
  )
}

export default App
