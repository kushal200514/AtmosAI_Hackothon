import React from 'react';
import { 
  Sparkles, 
  ShieldCheck, 
  AlertTriangle, 
  Clock, 
  Database, 
  Navigation, 
  CheckCircle2, 
  TrendingUp, 
  TrendingDown,
  Info,
  ArrowRight,
  UserCheck
} from 'lucide-react';

/**
 * Personalized Environmental Advisor Card
 * Displays:
 * 1. Current environmental category (CPCB Standard)
 * 2. Suggested action (Code-determined)
 * 3. Why AtmosAI recommends it (Evidence-based physical explanation)
 * 4. Forecast context (Multi-horizon ML trajectory)
 * 5. Data source (Ground station / CAMS)
 * 6. Measurement timestamp
 * 7. Data quality status (Freshness, validator check)
 */
export default function PersonalizedAdvisorCard({ 
  adviceData, 
  userProfile, 
  onNavigate = null,
  className = "" 
}) {
  if (!adviceData) return null;

  const getCategoryColor = (cat) => {
    switch ((cat || '').toLowerCase()) {
      case 'good':
        return { text: 'text-emerald-400', bg: 'bg-emerald-500/15', border: 'border-emerald-500/40' };
      case 'satisfactory':
        return { text: 'text-cyan-400', bg: 'bg-cyan-500/15', border: 'border-cyan-500/40' };
      case 'moderate':
        return { text: 'text-amber-400', bg: 'bg-amber-500/15', border: 'border-amber-500/40' };
      case 'poor':
        return { text: 'text-orange-400', bg: 'bg-orange-500/15', border: 'border-orange-500/40' };
      case 'very poor':
        return { text: 'text-red-400', bg: 'bg-red-500/20', border: 'border-red-500/50' };
      case 'severe':
        return { text: 'text-red-500', bg: 'bg-red-950/60', border: 'border-red-600' };
      default:
        return { text: 'text-[#788278]', bg: 'bg-[#F5F7F4]', border: 'border-[#E8ECE7]' };
    }
  };

  const catColors = getCategoryColor(adviceData.aqi_category);
  const formatTime = (ts) => {
    if (!ts) return 'Current Telemetry';
    try {
      const dt = new Date(ts);
      return dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return String(ts);
    }
  };

  return (
    <div className={`atmos-card p-5 sm:p-6 border border-[#E8ECE7] bg-white shadow-sm space-y-4 ${className}`}>
      {/* 1. Header with Persona & Category Pill */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#E8ECE7] pb-3">
        <div className="flex items-center space-x-2">
          <div className="p-1.5 rounded-lg bg-[#F1F8ED] text-[#469A36]">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm sm:text-base font-bold text-[#263329] tracking-tight flex items-center space-x-1.5">
              <span>Personalized Environmental Advisor</span>
            </h3>
            <p className="text-[11px] text-[#788278]">
              Deterministic Rule Engine &bull; Gemini Explainable Intelligence
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {adviceData.user_category && (
            <span className="text-[10px] font-bold uppercase px-2.5 py-1 rounded-md bg-[#F1F8ED] text-[#469A36] border border-[#C2EBBA] flex items-center space-x-1">
              <UserCheck className="w-3 h-3" />
              <span>{adviceData.user_category.replace('_', ' ')}</span>
            </span>
          )}

          {/* Current Environmental Category */}
          <span className={`text-[10px] font-extrabold uppercase px-2.5 py-1 rounded-md border ${catColors.bg} ${catColors.text} ${catColors.border}`}>
            {adviceData.aqi_category || 'Satisfactory'}
          </span>

          {onNavigate && (
            <button
              onClick={() => onNavigate('ai')}
              className="text-[11px] font-semibold text-[#469A36] hover:text-white px-2.5 py-1 rounded-md bg-[#F1F8ED] hover:bg-[#64BC45] border border-[#C2EBBA] flex items-center space-x-1 transition-all cursor-pointer ml-1"
              title="Open Explainable AI"
            >
              <span>Explain</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          )}
        </div>
      </div>

      {/* 2. Suggested Action (Core Directive) */}
      <div className="p-3.5 sm:p-4 rounded-2xl bg-gradient-to-r from-[#F1F8ED] via-white to-[#F1F8ED] border border-[#C2EBBA] space-y-1.5 shadow-xs">
        <div className="flex items-center space-x-1.5 text-[#469A36]">
          <ShieldCheck className="w-4 h-4 text-[#469A36] flex-shrink-0" />
          <span className="text-xs font-black uppercase tracking-wider">Suggested Action</span>
        </div>
        <p className="text-sm font-bold text-[#263329] leading-relaxed">
          {adviceData.recommended_action}
        </p>
      </div>

      {/* 3. Why AtmosAI Recommends It (Evidence-based explanation) */}
      <div className="space-y-1.5">
        <h4 className="text-xs font-bold uppercase tracking-wider text-[#788278] flex items-center space-x-1.5">
          <Info className="w-3.5 h-3.5 text-[#64BC45]" />
          <span>Why AtmosAI Recommends This</span>
        </h4>
        <p className="text-xs text-[#263329] leading-relaxed bg-[#F5F7F4] p-3 rounded-xl border border-[#E8ECE7]">
          {adviceData.evidence_based_explanation || adviceData.explanation}
        </p>
      </div>

      {/* 4. Forecast Context */}
      <div className="p-3 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7] flex items-start space-x-2.5 text-xs">
        {adviceData.potential_forecast_deterioration ? (
          <TrendingUp className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
        ) : (
          <TrendingDown className="w-4 h-4 text-[#64BC45] flex-shrink-0 mt-0.5" />
        )}
        <div className="space-y-0.5 min-w-0">
          <span className="text-[10px] font-bold uppercase text-[#788278] block font-mono">
            Forecast Context (Next 3–6 Hours)
          </span>
          <p className="text-[#263329] text-xs">
            {adviceData.deterioration_details || 'Atmospheric conditions projected to remain steady.'}
          </p>
        </div>
      </div>

      {/* 5, 6, 7. Provenance & Metadata Footer */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-2 border-t border-[#E8ECE7] text-[11px]">
        {/* Data Source */}
        <div className="p-2 rounded-lg bg-[#F5F7F4] border border-[#E8ECE7]">
          <span className="text-[10px] text-[#788278] block uppercase font-mono">Data Source</span>
          <span className="font-semibold text-[#263329] truncate block" title={adviceData.data_source}>
            {adviceData.data_source || 'CPCB Ground Station'}
          </span>
        </div>

        {/* Measurement Timestamp */}
        <div className="p-2 rounded-lg bg-[#F5F7F4] border border-[#E8ECE7]">
          <span className="text-[10px] text-[#788278] block uppercase font-mono">Telemetry Time</span>
          <span className="font-mono text-[#263329] block">
            {formatTime(adviceData.timestamp_iso)}
          </span>
        </div>

        {/* Data Quality Status */}
        <div className="p-2 rounded-lg bg-[#F5F7F4] border border-[#E8ECE7]">
          <span className="text-[10px] text-[#788278] block uppercase font-mono">Data Quality Status</span>
          <span className="font-semibold text-[#469A36] truncate block">
            {adviceData.confidence_status || 'Verified Telemetry'}
          </span>
        </div>
      </div>

      {/* Non-medical Disclaimer */}
      <p className="text-[10.5px] text-[#788278] italic pt-1 border-t border-[#E8ECE7] leading-tight">
        * {adviceData.disclaimer || "AtmosAI guidance is for environmental intelligence and risk reduction only. It does not constitute medical advice or disease diagnosis."}
      </p>
    </div>
  );
}
