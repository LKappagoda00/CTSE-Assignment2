import React, { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import {
  User, Utensils, ChevronRight, ChevronLeft,
  Loader2, AlertCircle, Zap, Globe,
  BrainCircuit, Calculator, Scale, Terminal, Cpu,
  Lightbulb, ShieldCheck
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

const API_BASE = 'http://localhost:8000'

const STEPS = [
  { id: 0, name: 'Input Profile', icon: User, color: '#f8fafc' },
  { id: 1, name: 'UserProfileAgent', icon: Calculator, sub: 'Metabolic Logic', color: '#4ade80' },
  { id: 2, name: 'NutritionPlannerAgent', icon: Utensils, sub: 'Meal Architecture', color: '#8b5cf6' },
  { id: 3, name: 'CulturalAdapterAgent', icon: Globe, sub: 'Cuisine Adaptation', color: '#fbbf24' },
  { id: 4, name: 'CalorieAnalyzerAgent', icon: Scale, sub: 'Nutrition Audit', color: '#f43f5e' },
]

const DEFAULT_FORM = {
  name: 'Kasun Perera',
  age: 28,
  gender: 'male',
  weight_kg: 78,
  height_cm: 175,
  activity_level: 'moderately_active',
  dietary_goal: 'weight_loss',
  cultural_preference: 'sri_lankan',
  allergies: [],
}

function App() {
  const [currentStep, setCurrentStep] = useState(0)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [cultures, setCultures] = useState([])
  const [logIndex, setLogIndex] = useState(0)
  const [formData, setFormData] = useState(DEFAULT_FORM)
  const [allergyInput, setAllergyInput] = useState('')
  const logEndRef = useRef(null)

  useEffect(() => { fetchCultures() }, [])
  useEffect(() => {
    if (loading) logEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logIndex, loading])

  const fetchCultures = async () => {
    try {
      const resp = await axios.get(`${API_BASE}/cultures`)
      setCultures(resp.data.cultures)
    } catch (err) {
      console.error('Failed to fetch cultures', err)
    }
  }

  const validateForm = () => {
    if (!formData.name.trim()) return 'Name is required.'
    if (!formData.age || formData.age < 10 || formData.age > 120) return 'Age must be between 10 and 120.'
    if (!formData.weight_kg || formData.weight_kg < 20 || formData.weight_kg > 500) return 'Weight must be between 20 and 500 kg.'
    if (!formData.height_cm || formData.height_cm < 50 || formData.height_cm > 300) return 'Height must be between 50 and 300 cm.'
    return null
  }

  const runWorkflow = async () => {
    const validationError = validateForm()
    if (validationError) { setError(validationError); return }

    setLoading(true)
    setError(null)
    setLogIndex(0)
    setResult(null)

    try {
      const resp = await axios.post(`${API_BASE}/generate-plan`, formData)
      for (let i = 0; i < resp.data.messages.length; i++) {
        setLogIndex(i + 1)
        await new Promise(r => setTimeout(r, 400))
      }
      setResult(resp.data)
      setCurrentStep(1)
    } catch (err) {
      setError(err.response?.data?.detail || 'Is the backend active? (python api.py)')
    } finally {
      setLoading(false)
    }
  }

  const addAllergy = () => {
    const trimmed = allergyInput.trim().toLowerCase()
    if (trimmed && !formData.allergies.includes(trimmed)) {
      setFormData({ ...formData, allergies: [...formData.allergies, trimmed] })
    }
    setAllergyInput('')
  }

  const removeAllergy = (allergen) => {
    setFormData({ ...formData, allergies: formData.allergies.filter(a => a !== allergen) })
  }

  const handleFieldChange = (field, value) => setFormData({ ...formData, [field]: value })
  const nextStep = () => setCurrentStep(prev => Math.min(prev + 1, 4))
  const prevStep = () => setCurrentStep(prev => Math.max(prev - 1, 0))

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
          <motion.div
            key={i}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.1 }}
            className="log-item"
          >
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

  return (
    <div className="app-container">
      {/* Header */}
      <nav className="nav">
        <div className="logo" onClick={() => { setResult(null); setCurrentStep(0); setFormData(DEFAULT_FORM) }} style={{ cursor: 'pointer' }}>
          VITALITY MAS
        </div>
        <div className="dashboard-pill">
          <div className="pulse-dot" /> MULTI-AGENT ORCHESTRATOR
        </div>
      </nav>

      {/* Stepper */}
      <div className="stepper-track">
        {STEPS.map((step, idx) => (
          <div
            key={idx}
            className={`step-node ${currentStep === idx ? 'current' : ''} ${currentStep > idx ? 'done' : ''}`}
            onClick={() => result && setCurrentStep(idx)}
          >
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
          {currentStep === 0 ? (
            <motion.div key="st0" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="grid" style={{ gridTemplateColumns: '1.2fr 0.8fr', gap: '2rem' }}>

              {/* Left — Architecture + Console */}
              <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
                  <BrainCircuit size={28} color="var(--primary)" />
                  <h3 style={{ fontSize: '1.5rem' }}>System Architecture</h3>
                </div>
                <div className="workflow-diagram">
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
                    {loading
                      ? result?.messages?.slice(0, logIndex).map((m, i) => (
                        <div key={i} className="c-line text-green">{m}</div>
                      ))
                      : <div className="c-line text-dim">Click "Launch Intelligence System" to start.</div>
                    }
                    <div ref={logEndRef} />
                  </div>
                </div>
              </div>

              {/* Right — Form */}
              <div className="glass-card">
                <h3 style={{ marginBottom: '0.5rem' }}>Biometric Input</h3>
                <form onSubmit={e => { e.preventDefault(); runWorkflow() }} className="form-grid">

                  <div className="fg full">
                    <label>NAME</label>
                    <input type="text" value={formData.name} onChange={e => handleFieldChange('name', e.target.value)} />
                  </div>

                  <div className="fg">
                    <label>AGE</label>
                    <input type="number" min="10" max="120" value={formData.age} onChange={e => handleFieldChange('age', Number(e.target.value))} />
                  </div>

                  <div className="fg">
                    <label>GENDER</label>
                    <select value={formData.gender} onChange={e => handleFieldChange('gender', e.target.value)}>
                      <option value="male">Male</option>
                      <option value="female">Female</option>
                      <option value="other">Other</option>
                    </select>
                  </div>

                  <div className="fg">
                    <label>WEIGHT (KG)</label>
                    <input type="number" min="20" max="500" step="0.1" value={formData.weight_kg} onChange={e => handleFieldChange('weight_kg', Number(e.target.value))} />
                  </div>

                  <div className="fg">
                    <label>HEIGHT (CM)</label>
                    <input type="number" min="50" max="300" value={formData.height_cm} onChange={e => handleFieldChange('height_cm', Number(e.target.value))} />
                  </div>

                  <div className="fg full">
                    <label>ACTIVITY LEVEL</label>
                    <select value={formData.activity_level} onChange={e => handleFieldChange('activity_level', e.target.value)}>
                      <option value="sedentary">Sedentary (little or no exercise)</option>
                      <option value="lightly_active">Lightly Active (1–3 days/week)</option>
                      <option value="moderately_active">Moderately Active (3–5 days/week)</option>
                      <option value="very_active">Very Active (6–7 days/week)</option>
                      <option value="extra_active">Extra Active (athlete / physical job)</option>
                    </select>
                  </div>

                  <div className="fg full">
                    <label>DIETARY GOAL</label>
                    <select value={formData.dietary_goal} onChange={e => handleFieldChange('dietary_goal', e.target.value)}>
                      <option value="weight_loss">Weight Loss</option>
                      <option value="muscle_gain">Muscle Gain</option>
                      <option value="maintenance">Maintenance</option>
                      <option value="healthy_eating">Healthy Eating</option>
                    </select>
                  </div>

                  <div className="fg full">
                    <label>CULTURAL PREFERENCE</label>
                    <select value={formData.cultural_preference} onChange={e => handleFieldChange('cultural_preference', e.target.value)}>
                      {cultures.map(c => (
                        <option key={c} value={c}>{c.replace(/_/g, ' ').toUpperCase()}</option>
                      ))}
                    </select>
                  </div>

                  <div className="fg full">
                    <label>ALLERGIES (OPTIONAL)</label>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <input
                        type="text"
                        placeholder="e.g. nuts, gluten, dairy"
                        value={allergyInput}
                        onChange={e => setAllergyInput(e.target.value)}
                        onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), addAllergy())}
                        style={{ flex: 1 }}
                      />
                      <button type="button" onClick={addAllergy} className="btn-add-allergy">+ ADD</button>
                    </div>
                    {formData.allergies.length > 0 && (
                      <div className="allergy-tags">
                        {formData.allergies.map(a => (
                          <span key={a} className="allergy-tag">
                            {a}
                            <button type="button" onClick={() => removeAllergy(a)}>×</button>
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  <button type="submit" className="btn-launch full" disabled={loading}>
                    {loading ? <Loader2 className="spinning" size={18} /> : <Zap size={18} />}
                    LAUNCH INTELLIGENCE SYSTEM
                  </button>

                </form>
                {error && (
                  <div className="err-msg">
                    <AlertCircle size={14} /> {error}
                  </div>
                )}
              </div>
            </motion.div>

          ) : result && (
            <motion.div key={currentStep} className="agent-page-grid">
              <div className="agent-main">
                <div className="page-header">
                  <div className="agent-badge" style={{ background: STEPS[currentStep].color }}>AGENT 0{currentStep}</div>
                  <h2 style={{ fontSize: '2.5rem', fontWeight: '800' }}>{STEPS[currentStep].name}</h2>
                </div>

                {/* Step 1 */}
                {currentStep === 1 && (
                  <div className="agent-details">
                    <div className="grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
                      <div className="glass-card data-box">
                        <div className="db-label">COMPUTED BMI</div>
                        <div className="db-value">{result.bmi_result?.bmi_value ?? 'N/A'}</div>
                        <div className="db-sub" style={{ color: STEPS[1].color }}>{result.bmi_result?.category?.toUpperCase() ?? ''}</div>
                      </div>
                      <div className="glass-card data-box">
                        <div className="db-label">DAILY TARGET</div>
                        <div className="db-value">{result.target_calories}</div>
                        <div className="db-sub">KCAL / DAY</div>
                      </div>
                      <div className="glass-card data-box">
                        <div className="db-label">HYDRATION</div>
                        <div className="db-value">{result.hydration_target}L</div>
                        <div className="db-sub">H₂O / DAY</div>
                      </div>
                    </div>
                    <HandoffCard color={STEPS[1].color} text={`UserProfileAgent translated raw inputs into a Metabolic Baseline of ${result.target_calories} kcal/day for goal: ${formData.dietary_goal.replace(/_/g, ' ')}.`} />
                  </div>
                )}

                {/* Step 2 */}
                {currentStep === 2 && (
                  <div className="agent-details">
                    <div className="grid" style={{ gridTemplateColumns: 'repeat(2, 1fr)' }}>
                      {result.daily_meal_plan?.meals?.map((m, i) => (
                        <div key={i} className="glass-card meal-view">
                          <div className="mv-type">{m.meal_type.toUpperCase()}</div>
                          <div className="mv-name">{m.items?.[0]?.food_name ?? 'N/A'}</div>
                          <div className="mv-kcal">{m.total_calories} KCAL</div>
                        </div>
                      ))}
                    </div>
                    <HandoffCard color={STEPS[2].color} text={`NutritionPlannerAgent constructed a stable 4-meal architecture targeting ${result.target_calories} kcal/day.`} />
                  </div>
                )}

                {/* Step 3 */}
                {currentStep === 3 && (
                  <div className="agent-details">
                    <div className="glass-card primary-output" style={{ borderLeft: `4px solid ${STEPS[3].color}` }}>
                      <h4 style={{ color: STEPS[3].color }}>CUISINE: {formData.cultural_preference.replace(/_/g, ' ').toUpperCase()}</h4>
                      <div className="grid" style={{ marginTop: '1.5rem', gridTemplateColumns: '1fr 1fr' }}>
                        {result.adapted_meal_plan?.meals?.slice(1, 3).map((m, i) => (
                          <div key={i} className="sub-item">
                            <span className="si-label">{m.meal_type.toUpperCase()}</span>
                            <span className="si-val">{m.items?.[0]?.food_name ?? 'N/A'}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    <HandoffCard color={STEPS[3].color} text="CulturalAdapterAgent mapped regional staples from the Food Database to maintain culinary authenticity." />
                  </div>
                )}

                {/* Step 4 */}
                {currentStep === 4 && (
                  <div className="agent-details">
                    <div className="glass-card" style={{ borderLeft: `8px solid ${STEPS[4].color}`, background: 'rgba(244,63,94,0.05)' }}>
                      <h3 style={{ fontSize: '1.25rem', marginBottom: '1rem' }}>FINAL SYSTEM VERDICT</h3>
                      <p className="final-text">{result.final_report}</p>
                    </div>
                    <div className="grid" style={{ marginTop: '1.5rem', gridTemplateColumns: 'repeat(3,1fr)' }}>
                      <div className="glass-card data-box">
                        <div className="db-label">PROTEIN</div>
                        <div className="db-value" style={{ fontSize: '1.5rem' }}>{result.calorie_analysis?.macronutrient_breakdown?.protein_pct ?? 0}%</div>
                      </div>
                      <div className="glass-card data-box">
                        <div className="db-label">CARBS</div>
                        <div className="db-value" style={{ fontSize: '1.5rem' }}>{result.calorie_analysis?.macronutrient_breakdown?.carbs_pct ?? 0}%</div>
                      </div>
                      <div className="glass-card data-box">
                        <div className="db-label">FAT</div>
                        <div className="db-value" style={{ fontSize: '1.5rem' }}>{result.calorie_analysis?.macronutrient_breakdown?.fat_pct ?? 0}%</div>
                      </div>
                    </div>
                    <button onClick={() => { setResult(null); setCurrentStep(0); setFormData(DEFAULT_FORM) }} className="btn-restart">
                      RESTART ORCHESTRATION
                    </button>
                  </div>
                )}

                <div className="nav-controls">
                  <button onClick={prevStep} className="btn-nav"><ChevronLeft /> PREVIOUS</button>
                  {currentStep < 4 && (
                    <button onClick={nextStep} className="btn-nav" style={{ borderColor: STEPS[currentStep + 1].color }}>
                      PROCEED TO {STEPS[currentStep + 1].name.replace('Agent', '').toUpperCase()} <ChevronRight />
                    </button>
                  )}
                </div>
              </div>

              <div className="agent-sidebar">
                <IntelligenceLog logs={result.analytical_logs} />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      <style dangerouslySetInnerHTML={{
        __html: `
        :root { --primary: #4ade80; --bg: #030712; --card: #111827; --text: #f9fafb; --text-dim: #94a3b8; }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: var(--bg); color: var(--text); font-family: system-ui, sans-serif; }
        .app-container { max-width: 1300px; margin: 0 auto; padding: 2rem 4rem; }
        .nav { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4rem; }
        .logo { font-size: 1.5rem; font-weight: 900; letter-spacing: -1px; background: linear-gradient(to right, #4ade80, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .dashboard-pill { background: rgba(255,255,255,0.05); padding: 0.5rem 1rem; border-radius: 99px; font-size: 0.7rem; font-weight: 800; color: var(--primary); display: flex; gap: 0.5rem; align-items: center; border: 1px solid rgba(74,222,128,0.2); }
        .glass-card { background: var(--card); border: 1px solid rgba(255,255,255,0.05); border-radius: 1.25rem; padding: 1.5rem; }
        .grid { display: grid; gap: 1.5rem; }
        .stepper-track { display: flex; justify-content: space-between; margin-bottom: 4rem; padding: 0 1rem; }
        .step-node { display: flex; align-items: center; gap: 0.75rem; opacity: 0.2; transform: scale(0.95); transition: all 0.4s ease; cursor: pointer; }
        .step-node.current { opacity: 1; transform: scale(1.05); }
        .step-node.done { opacity: 0.6; }
        .node-circle { width: 36px; height: 36px; border-radius: 50%; border: 2px solid; display: flex; align-items: center; justify-content: center; }
        .node-label { display: flex; flex-direction: column; }
        .node-name { font-size: 0.7rem; font-weight: 900; }
        .node-sub { font-size: 0.6rem; color: var(--text-dim); }
        .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1.5rem; }
        .fg { display: flex; flex-direction: column; gap: 0.4rem; }
        .fg.full, .full { grid-column: span 2; }
        label { font-size: 0.65rem; font-weight: 800; color: var(--text-dim); letter-spacing: 1px; }
        input, select { background: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.1); padding: 0.75rem; border-radius: 0.5rem; color: white; font-family: inherit; width: 100%; }
        .allergy-tags { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 0.5rem; }
        .allergy-tag { background: rgba(244,63,94,0.15); border: 1px solid rgba(244,63,94,0.3); color: #f43f5e; padding: 0.2rem 0.6rem; border-radius: 99px; font-size: 0.7rem; display: flex; align-items: center; gap: 0.4rem; }
        .allergy-tag button { background: none; border: none; color: #f43f5e; cursor: pointer; font-size: 0.9rem; padding: 0; }
        .btn-add-allergy { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); color: white; padding: 0.75rem 1rem; border-radius: 0.5rem; cursor: pointer; font-size: 0.75rem; font-weight: 800; white-space: nowrap; }
        .btn-launch { background: var(--primary); color: #000; border: none; padding: 1rem; border-radius: 0.75rem; font-weight: 900; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 0.5rem; transition: transform 0.2s; width: 100%; margin-top: 0.5rem; }
        .btn-launch:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 10px 30px rgba(74,222,128,0.3); }
        .btn-launch:disabled { opacity: 0.5; cursor: not-allowed; }
        .err-msg { margin-top: 1rem; background: rgba(244,63,94,0.1); border: 1px solid rgba(244,63,94,0.3); color: #f43f5e; padding: 0.75rem 1rem; border-radius: 0.5rem; font-size: 0.8rem; display: flex; align-items: center; gap: 0.5rem; }
        .agent-page-grid { display: grid; grid-template-columns: 1fr 350px; gap: 2rem; }
        .agent-badge { font-size: 0.65rem; font-weight: 900; color: #000; padding: 0.3rem 0.6rem; border-radius: 0.4rem; margin-bottom: 1rem; width: fit-content; }
        .page-header { margin-bottom: 2rem; }
        .agent-details { display: flex; flex-direction: column; gap: 1.5rem; }
        .data-box { text-align: center; }
        .db-label { font-size: 0.65rem; font-weight: 800; color: var(--text-dim); }
        .db-value { font-size: 2.5rem; font-weight: 900; margin: 0.5rem 0; }
        .db-sub { font-size: 0.75rem; font-weight: 800; color: var(--text-dim); }
        .meal-view { display: flex; flex-direction: column; gap: 0.5rem; }
        .mv-type { font-size: 0.65rem; font-weight: 800; color: var(--text-dim); }
        .mv-name { font-size: 1rem; font-weight: 700; }
        .mv-kcal { font-size: 0.8rem; color: #8b5cf6; font-weight: 800; }
        .sub-item { display: flex; flex-direction: column; gap: 0.25rem; padding: 1rem; background: rgba(255,255,255,0.03); border-radius: 0.75rem; }
        .si-label { font-size: 0.65rem; font-weight: 800; color: var(--text-dim); }
        .si-val { font-size: 0.9rem; font-weight: 700; }
        .handoff-card { background: rgba(255,255,255,0.02); padding: 1rem; border-radius: 0.75rem; }
        .intel-sidebar { height: 100%; display: flex; flex-direction: column; background: #0b1120; border-color: rgba(139,92,246,0.2); }
        .sidebar-header { display: flex; align-items: center; gap: 0.75rem; padding-bottom: 1rem; border-bottom: 1px solid rgba(255,255,255,0.05); }
        .log-container { flex: 1; padding: 1.5rem 0; overflow-y: auto; display: flex; flex-direction: column; gap: 1.25rem; }
        .log-item { font-size: 0.85rem; line-height: 1.6; color: #cbd5e1; position: relative; padding-left: 1.25rem; }
        .log-dot { position: absolute; left: 0; top: 8px; width: 6px; height: 6px; border-radius: 50%; background: #4ade80; }
        .sidebar-footer { font-size: 0.65rem; color: #64748b; padding-top: 1rem; border-top: 1px solid rgba(255,255,255,0.05); display: flex; align-items: center; gap: 0.4rem; }
        .nav-controls { display: flex; justify-content: space-between; margin-top: 3rem; }
        .btn-nav { background: transparent; border: 1px solid rgba(255,255,255,0.1); color: white; padding: 0.75rem 1.5rem; border-radius: 0.5rem; cursor: pointer; font-weight: 800; display: flex; align-items: center; gap: 0.5rem; }
        .btn-nav:hover { background: rgba(255,255,255,0.05); }
        .btn-restart { margin-top: 1.5rem; background: rgba(244,63,94,0.1); border: 1px solid rgba(244,63,94,0.3); color: #f43f5e; padding: 0.75rem 1.5rem; border-radius: 0.5rem; cursor: pointer; font-weight: 800; width: 100%; }
        .workflow-diagram { display: flex; align-items: center; justify-content: space-between; margin-bottom: 2rem; }
        .diag-node { display: flex; flex-direction: column; align-items: center; gap: 0.5rem; font-size: 0.6rem; font-weight: 800; color: var(--text-dim); }
        .diag-node svg { background: rgba(255,255,255,0.05); padding: 0.75rem; border-radius: 50%; color: var(--primary); }
        .diag-line { flex: 1; height: 1px; border-top: 1px dashed rgba(255,255,255,0.2); margin: 0 0.5rem; }
        .console-preview { background: #000; border-radius: 0.75rem; border: 1px solid rgba(255,255,255,0.1); flex: 1; overflow: hidden; display: flex; flex-direction: column; }
        .console-header { background: rgba(255,255,255,0.05); padding: 0.4rem 0.75rem; font-size: 0.6rem; font-weight: 900; color: var(--text-dim); display: flex; align-items: center; gap: 0.4rem; }
        .console-body { padding: 1rem; overflow-y: auto; height: 180px; font-family: monospace; font-size: 0.7rem; }
        .c-line { margin-bottom: 0.3rem; }
        .text-green { color: #4ade80; }
        .text-dim { color: #475569; }
        .final-text { line-height: 1.8; color: #cbd5e1; }
        .pulse-dot { width: 8px; height: 8px; background: var(--primary); border-radius: 50%; animation: pulse 2s infinite; }
        @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(74,222,128,0.7); } 70% { box-shadow: 0 0 0 8px rgba(74,222,128,0); } 100% { box-shadow: 0 0 0 0 rgba(74,222,128,0); } }
        .spinning { animation: spin 1s linear infinite; }
        @keyframes spin { 100% { transform: rotate(360deg); } }
      `}} />
    </div>
  )
}

export default App