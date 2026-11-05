import React, { useState, useEffect } from 'react';
import { 
  BrainCircuit, 
  Sparkles, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  ShieldCheck, 
  Wind, 
  Info,
  Activity,
  AlertTriangle,
  GraduationCap,
  Footprints,
  Briefcase,
  Bike,
  Baby,
  Users,
  Database,
  Calendar,
  Layers,
  ArrowRight
} from 'lucide-react';
import { fetchAIAdvice } from '../services/api';

const ALL_PERSONAS = [
  { id: 'student', label: 'Student', icon: GraduationCap, focus: 'Campus Conditions & Outdoor Walks' },
  { id: 'runner', label: 'Runner', icon: Footprints, focus: 'Workout Windows & Aerobic Respiration' },
  { id: 'office_commuter', label: 'Commuter', icon: Briefcase, focus: 'Arterial Traffic & Vehicle Recirculation' },
  { id: 'outdoor_worker', label: 'Outdoor Worker', icon: Bike, focus: 'Shift Exposure & Protective Masks' },
  { id: 'parent', label: 'Parent', icon: Baby, focus: 'Playground Outings & Pediatric Safety' },
  { id: 'general_public', label: 'General Public', icon: Users, focus: 'Daily Trends & Indoor Ventilation' }
];

export default function ExplainableAI({ 
  adviceData: initialAdvice, 
  selectedLocation = 'bengaluru_central', 
  onSelectProfile 
}) {
  const [activePersona, setActivePersona] = useState(
    initialAdvice?.user_category || initialAdvice?.profile_type || 'runner'
  );
  const [adviceData, setAdviceData] = useState(initialAdvice);
  const [loading, setLoading] = useState(false);

  // Sync if initialAdvice changes from parent
  useEffect(() => {
    if (initialAdvice) {
      setAdviceData(initialAdvice);
      const cat = initialAdvice.user_category || initialAdvice.profile_type;
      if (cat) setActivePersona(cat);
    }
  }, [initialAdvice]);

  // Handle switching personas to test the personalized risk advisor dynamically
  const handlePersonaSelect = async (personaId) => {
    setActivePersona(personaId);
    setLoading(true);
    try {
      const updated = await fetchAIAdvice(selectedLocation, personaId);
      setAdviceData(updated);
    } catch (err) {
      console.error('Failed to load persona-specific advice:', err);
    } finally {
      setLoading(false);
    }
  };

  if (!adviceData) {
    return (
      <div className="bg-white border border-[#E8ECE7] rounded-2xl p-12 text-center text-[#788278] space-y-3">
        <div className="w-8 h-8 border-2 border-[#64BC45] border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-sm">Generating personalized pollution risk assessment...</p>
      </div>
    );
  }

  const { activity_guidance } = adviceData;

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="p-5 rounded-2xl bg-gradient-to-r from-[#F1F8ED] via-white to-[#F1F8ED] border border-[#C2EBBA] shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded-lg bg-[#C2EBBA] flex items-center justify-center text-[#469A36]">
                <BrainCircuit className="w-5 h-5" />
              </div>
              <h1 className="text-xl font-extrabold text-[#263329] tracking-tight">
                Personalized Pollution Risk Advisor
              </h1>
              <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-full bg-[#F1F8ED] text-[#469A36] border border-[#C2EBBA]">
                Evidence-Based
              </span>
            </div>
            <p className="text-xs text-[#788278] mt-1 max-w-2xl">
              Integrates user lifestyle profile, live environmental telemetry, multi-horizon forecasts, and meteorological drivers
              to produce tailored risk reduction guidance without fabricated data.
            </p>
          </div>

          <div className="text-xs text-[#788278] font-mono">
            Provider: <span className="text-[#469A36] font-semibold">{adviceData.ai_provider}</span>
          </div>
        </div>
      </div>

      {/* Persona Testing Bar: Switch between all 6 Personas */}
      <div className="bg-white p-4 border border-[#E8ECE7] rounded-2xl space-y-2 shadow-xs">
        <div className="flex items-center justify-between">
          <label className="text-xs font-bold text-[#263329] flex items-center space-x-1.5">
            <Users className="w-4 h-4 text-[#469A36]" />
            <span>Select Persona to Evaluate Personalized Recommendations</span>
          </label>
          {loading && (
            <span className="text-[11px] text-[#469A36] font-mono animate-pulse">
              Re-evaluating persona risk...
            </span>
          )}
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 pt-1">
          {ALL_PERSONAS.map((p) => {
            const Icon = p.icon;
            const isSelected = activePersona.toLowerCase() === p.id.toLowerCase();
            return (
              <button
                key={p.id}
                onClick={() => handlePersonaSelect(p.id)}
                disabled={loading}
                className={`p-2.5 rounded-xl border text-left transition-all cursor-pointer flex flex-col justify-between space-y-1.5 ${
                  isSelected
                    ? 'bg-[#64BC45] text-white shadow-sm border-[#64BC45]'
                    : 'bg-[#F5F7F4] hover:bg-[#E8ECE7] text-[#263329] border-[#E8ECE7]'
                }`}
              >
                <div className="flex items-center justify-between">
                  <Icon className={`w-4 h-4 ${isSelected ? 'text-white' : 'text-[#469A36]'}`} />
                  {isSelected && <CheckCircle2 className="w-3.5 h-3.5 text-white" />}
                </div>
                <div>
                  <p className="text-xs font-bold leading-tight">{p.label}</p>
                  <p className={`text-[9px] truncate ${isSelected ? 'text-white/90' : 'text-[#788278]'}`}>
                    {p.focus}
                  </p>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* 2-Column Overview: Current Environmental Status & Forecast Deterioration */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Current Environmental Status Card */}
        <div className="bg-white p-5 border border-[#E8ECE7] rounded-2xl space-y-3 shadow-xs">
          <div className="flex items-center justify-between text-xs text-[#788278]">
            <span className="font-semibold uppercase tracking-wider flex items-center space-x-1.5 text-[#263329]">
              <Activity className="w-4 h-4 text-[#469A36]" />
              <span>Current Environmental Status</span>
            </span>
            <span className="font-mono text-[10px] text-[#788278]">
              {adviceData.timestamp_iso ? new Date(adviceData.timestamp_iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Live'}
            </span>
          </div>

          <div className="flex items-baseline space-x-3">
            <div>
              <span className="text-2xl font-extrabold text-[#263329]">
                {adviceData.aqi_category || 'Satisfactory'}
              </span>
              <p className="text-xs text-[#788278] mt-0.5">
                Indian NAQI: <strong className="text-[#263329] font-mono">{adviceData.current_aqi ?? '--'}</strong> &bull; PM2.5: <strong className="text-[#469A36] font-mono">{adviceData.current_pm25 ?? '--'} µg/m³</strong>
              </p>
            </div>
          </div>

          <p className="text-xs text-[#263329] border-t border-[#E8ECE7] pt-2 leading-relaxed">
            {adviceData.current_environmental_status}
          </p>
        </div>

        {/* Potential Forecast Deterioration Card */}
        <div className={`p-5 rounded-2xl border space-y-3 shadow-xs ${
          adviceData.potential_forecast_deterioration
            ? 'border-amber-200 bg-amber-50/50'
            : 'border-[#C2EBBA] bg-[#F1F8ED]/40'
        }`}>
          <div className="flex items-center justify-between text-xs">
            <span className={`font-semibold uppercase tracking-wider flex items-center space-x-1.5 ${
              adviceData.potential_forecast_deterioration ? 'text-amber-700' : 'text-[#469A36]'
            }`}>
              {adviceData.potential_forecast_deterioration ? (
                <AlertTriangle className="w-4 h-4 text-amber-600" />
              ) : (
                <CheckCircle2 className="w-4 h-4 text-[#469A36]" />
              )}
              <span>3–6 Hour Forecast Trend</span>
            </span>
            <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase font-mono ${
              adviceData.potential_forecast_deterioration 
                ? 'bg-amber-100 text-amber-800 border border-amber-300' 
                : 'bg-[#F1F8ED] text-[#469A36] border border-[#C2EBBA]'
            }`}>
              {adviceData.potential_forecast_deterioration ? 'Deterioration Warning' : 'Stable / Favorable'}
            </span>
          </div>

          <p className="text-xs text-[#263329] leading-relaxed font-medium">
            {adviceData.deterioration_details || (
              adviceData.potential_forecast_deterioration
                ? 'Atmospheric models predict particulate concentration increase over the next 3–6 hours.'
                : 'Particulate levels are expected to remain steady or improve.'
            )}
          </p>

          <div className="text-[11px] text-[#788278] border-t border-[#E8ECE7] pt-2 flex items-center justify-between">
            <span>Forecast Model:</span>
            <span className="font-mono text-[#469A36]">LightGBM Multi-Horizon Predictor</span>
          </div>
        </div>
      </div>

      {/* Hero Card: Primary Recommended Action */}
      <div className="p-6 rounded-2xl border border-[#C2EBBA] bg-gradient-to-r from-[#F1F8ED] via-white to-[#F1F8ED] space-y-3 shadow-xs">
        <div className="flex items-center space-x-2 text-[#469A36]">
          <ShieldCheck className="w-5 h-5 text-[#469A36]" />
          <span className="text-xs font-extrabold uppercase tracking-wider">
            Primary Recommended Action for {activePersona.replace('_', ' ').toUpperCase()}
          </span>
        </div>

        <p className="text-base sm:text-lg font-bold text-[#263329] leading-relaxed">
          {adviceData.recommended_action || adviceData.headline_summary}
        </p>

        {adviceData.sensitivity_preference && adviceData.sensitivity_preference !== 'none' && (
          <div className="text-xs text-amber-800 bg-amber-50 border border-amber-200 p-2.5 rounded-xl font-medium">
            <strong>Sensitivity Precaution ({adviceData.sensitivity_preference}):</strong> Keep prescribed respiratory or allergy relief medication readily accessible.
          </div>
        )}
      </div>

      {/* Main Evidence-Based Reasoning Card */}
      <div className="bg-white p-6 border border-[#E8ECE7] rounded-2xl space-y-4 shadow-xs">
        <div className="space-y-1">
          <span className="text-xs font-bold uppercase tracking-wider text-[#469A36]">Physical Atmospheric Explanation</span>
          <h2 className="text-base font-bold text-[#263329]">{adviceData.headline_summary}</h2>
        </div>

        <div className="p-4 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7] text-xs sm:text-sm text-[#263329] leading-relaxed font-sans">
          {adviceData.explanation || adviceData.evidence_based_explanation}
        </div>

        {/* Environmental Drivers Cited */}
        <div className="pt-2">
          <span className="text-xs font-semibold text-[#788278] block mb-2">Environmental Drivers Cited:</span>
          <div className="flex flex-wrap gap-2">
            {adviceData.environmental_drivers_cited?.map((d, i) => (
              <span key={i} className="text-xs px-3 py-1 rounded-lg bg-[#F1F8ED] border border-[#C2EBBA] text-[#469A36]">
                &bull; {d}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Activity Guidelines & Persona Directives */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Left Column: Practical Activity Guidelines */}
        <div className="bg-white p-6 border border-[#E8ECE7] rounded-2xl space-y-4 shadow-xs">
          <h3 className="text-sm font-bold text-[#263329] flex items-center space-x-2">
            <Activity className="w-4 h-4 text-[#469A36]" />
            <span>Activity Schedule & Environmental Protocol</span>
          </h3>

          <div className="space-y-3 text-xs">
            {/* Outdoor exercise */}
            <div className="flex items-center justify-between p-3 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7]">
              <span className="text-[#788278]">Outdoor Strenuous Exercise:</span>
              <span className={`font-semibold flex items-center space-x-1 ${
                activity_guidance.outdoor_exercise_allowed ? 'text-[#469A36]' : 'text-amber-600'
              }`}>
                {activity_guidance.outdoor_exercise_allowed ? (
                  <>
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Permissible</span>
                  </>
                ) : (
                  <>
                    <XCircle className="w-3.5 h-3.5" />
                    <span>Limit Exertion</span>
                  </>
                )}
              </span>
            </div>

            {/* Optimal window */}
            <div className="flex items-center justify-between p-3 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7]">
              <span className="text-[#788278]">Optimal Time Window:</span>
              <span className="font-semibold text-[#263329]">{activity_guidance.best_time_window}</span>
            </div>

            {/* Duration */}
            <div className="flex items-center justify-between p-3 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7]">
              <span className="text-[#788278]">Recommended Session Cap:</span>
              <span className="font-semibold text-[#469A36] font-mono">{activity_guidance.recommended_duration_minutes} minutes</span>
            </div>

            {/* Mask */}
            <div className="p-3 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7] space-y-1">
              <span className="text-[#788278]">Mask Recommendation:</span>
              <p className="font-medium text-[#263329]">{activity_guidance.mask_recommendation}</p>
            </div>

            {/* Indoor ventilation */}
            <div className="p-3 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7] space-y-1">
              <span className="text-[#788278]">Indoor Ventilation Timing:</span>
              <p className="font-medium text-[#263329]">{activity_guidance.indoor_ventilation_advice}</p>
            </div>
          </div>
        </div>

        {/* Right Column: Profile-Specific Directives */}
        <div className="bg-white p-6 border border-[#E8ECE7] rounded-2xl space-y-4 shadow-xs">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-[#263329] flex items-center space-x-2">
              <ShieldCheck className="w-4 h-4 text-[#469A36]" />
              <span className="capitalize">{activePersona.replace('_', ' ')} Directives</span>
            </h3>
            <span className="text-[11px] text-[#469A36] font-mono uppercase font-bold">
              {activePersona}
            </span>
          </div>

          <div className="space-y-3">
            {adviceData.profile_specific_recommendations?.map((rec, i) => (
              <div key={i} className="p-3.5 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7] text-xs text-[#263329] flex items-start space-x-3">
                <span className="w-5 h-5 rounded-full bg-[#F1F8ED] border border-[#C2EBBA] text-[#469A36] flex items-center justify-center font-bold text-[11px] flex-shrink-0 mt-0.5">
                  {i + 1}
                </span>
                <span className="leading-relaxed">{rec}</span>
              </div>
            ))}
          </div>

          {/* Data Provenance & Confidence Quality */}
          <div className="pt-3 border-t border-[#E8ECE7] text-[11px] text-[#788278] space-y-1.5 font-mono">
            <div className="flex items-center justify-between">
              <span className="flex items-center space-x-1 text-[#788278]">
                <Database className="w-3.5 h-3.5 text-[#469A36]" />
                <span>Data Source:</span>
              </span>
              <span className="text-[#263329] truncate max-w-[200px]">{adviceData.data_source}</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Confidence:</span>
              <span className="text-[#469A36] font-semibold">{adviceData.confidence_status}</span>
            </div>
          </div>

          {/* Conservative Non-Medical Disclaimer */}
          <div className="p-3 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7] text-[11px] text-[#788278] flex items-start space-x-2.5 mt-4">
            <Info className="w-4 h-4 text-[#788278] flex-shrink-0 mt-0.5" />
            <p className="leading-relaxed">{adviceData.disclaimer}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
