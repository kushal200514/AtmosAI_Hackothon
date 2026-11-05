import React, { useState, useEffect, useCallback } from 'react';
import { 
  ResponsiveContainer, 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  Tooltip, 
  Legend, 
  CartesianGrid 
} from 'recharts';
import { 
  ShieldCheck, 
  CheckCircle2, 
  AlertTriangle, 
  Clock, 
  Database, 
  RefreshCw, 
  BarChart3, 
  TrendingUp, 
  Info,
  Calendar,
  Layers
} from 'lucide-react';
import { fetchForecastAccuracy } from '../services/api';

export default function ForecastAccuracyDashboard({ selectedLocation = 'bengaluru_central' }) {
  const [dataMode, setDataMode] = useState('real'); // 'real' or 'demo'
  const [horizon, setHorizon] = useState(3);
  const [dateRange, setDateRange] = useState('all');
  const [loading, setLoading] = useState(true);
  const [accuracyData, setAccuracyData] = useState(null);
  const [error, setError] = useState(null);
  const [activeHistoryTab, setActiveHistoryTab] = useState('all'); // 'all', 'validated', 'pending'

  const loadAccuracyMetrics = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchForecastAccuracy(selectedLocation, horizon, dateRange, dataMode);
      setAccuracyData(data);
    } catch (err) {
      console.error('Failed to load forecast accuracy data:', err);
      setError('Unable to load forecast accuracy metrics. Please check network connection.');
    } finally {
      setLoading(false);
    }
  }, [selectedLocation, horizon, dateRange, dataMode]);

  useEffect(() => {
    loadAccuracyMetrics();
  }, [loadAccuracyMetrics]);

  const horizons = [
    { value: 1, label: '+1 Hour Ahead', short: '1h' },
    { value: 3, label: '+3 Hours Ahead', short: '3h' },
    { value: 6, label: '+6 Hours Ahead', short: '6h' }
  ];

  const dateRanges = [
    { value: 'last_24h', label: 'Last 24 Hours' },
    { value: 'last_7d', label: 'Last 7 Days' },
    { value: 'last_30d', label: 'Last 30 Days' },
    { value: 'all', label: 'All Validated Records' }
  ];

  const filteredHistory = accuracyData?.forecast_history?.filter(rec => {
    if (activeHistoryTab === 'validated') return rec.is_validated;
    if (activeHistoryTab === 'pending') return !rec.is_validated;
    return true;
  }) || [];

  return (
    <div className="space-y-6">
      {/* Header Banner with Mode Switch */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-2xl bg-gradient-to-r from-[#F1F8ED] via-white to-[#F1F8ED] border border-[#C2EBBA] shadow-xs">
        <div>
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-lg bg-[#C2EBBA] flex items-center justify-center text-[#469A36]">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h1 className="text-xl font-extrabold text-[#263329] tracking-tight">
              Forecast Accuracy & Trust Engine
            </h1>
            <span className={`text-[10px] uppercase font-bold px-2.5 py-0.5 rounded-full border ${
              dataMode === 'demo'
                ? 'bg-amber-100 text-amber-800 border-amber-300'
                : 'bg-[#F1F8ED] text-[#469A36] border-[#C2EBBA]'
            }`}>
              {dataMode === 'demo' ? 'Simulated Demo Data' : 'Verified Real Data'}
            </span>
          </div>
          <p className="text-xs text-[#788278] mt-1 max-w-2xl">
            {dataMode === 'demo'
              ? 'Demonstrating how AtmosAI matches prediction horizons against ground truth observations using synthetic environmental data.'
              : 'Demonstrating how well AtmosAI PM2.5 predictions match actual ground truth observations. Zero fabricated success rates.'}
          </p>
        </div>

        {/* Mode Switch & Refresh Controls */}
        <div className="flex items-center space-x-2.5 self-start sm:self-center">
          {/* Mode Switcher */}
          <div className="flex items-center space-x-1 bg-white p-1 rounded-xl border border-[#E8ECE7] shadow-xs">
            <button
              type="button"
              onClick={() => setDataMode('real')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                dataMode === 'real'
                  ? 'bg-[#64BC45] text-white shadow-sm'
                  : 'text-[#788278] hover:text-[#263329]'
              }`}
            >
              Real Data
            </button>
            <button
              type="button"
              onClick={() => setDataMode('demo')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                dataMode === 'demo'
                  ? 'bg-[#64BC45] text-white shadow-sm'
                  : 'text-[#788278] hover:text-[#263329]'
              }`}
            >
              Demo Data
            </button>
          </div>

          <button
            onClick={loadAccuracyMetrics}
            disabled={loading}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-white hover:bg-[#F5F7F4] border border-[#E8ECE7] text-xs font-semibold text-[#263329] transition-colors cursor-pointer disabled:opacity-50"
            title="Refresh Analytics"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-[#64BC45]' : 'text-[#788278]'}`} />
            <span className="hidden sm:inline">Refresh</span>
          </button>
        </div>
      </div>

      {/* Prominent Simulated Demo Mode Banner */}
      {dataMode === 'demo' && (
        <div className="p-4 rounded-2xl bg-[#F1F8ED] border-2 border-[#64BC45] text-[#263329] space-y-1.5 shadow-xs animate-fadeIn">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <span className="px-2.5 py-0.5 rounded-md bg-[#64BC45] text-white text-[10px] font-black uppercase tracking-wider">
              SIMULATED DATA — DEMONSTRATION ONLY
            </span>
            <span className="text-xs font-mono text-[#469A36] font-bold">
              Model: {accuracyData?.model_name || 'AtmosAI Demo Baseline (Moving Average & Diurnal Trend v1.0)'}
            </span>
          </div>
          <p className="text-xs text-[#263329] font-medium leading-relaxed">
            These results use synthetic environmental data and do not represent real-world forecast accuracy.
          </p>
          <p className="text-[11px] text-[#788278]">
            Generated deterministically over 7+ days (168 hourly samples) for Bengaluru Demo Location. Predictions and observations are strictly paired by target timestamp and horizon.
          </p>
        </div>
      )}

      {/* Selectors Bar: Horizon & Date Range */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Horizon Selector */}
        <div className="bg-white p-4 border border-[#E8ECE7] rounded-2xl space-y-2 shadow-xs">
          <label className="text-xs font-semibold text-[#263329] flex items-center space-x-1.5">
            <Clock className="w-4 h-4 text-[#469A36]" />
            <span>Select Forecast Horizon</span>
          </label>
          <div className="grid grid-cols-3 gap-2">
            {horizons.map(h => (
              <button
                key={h.value}
                onClick={() => setHorizon(h.value)}
                className={`py-2 px-3 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                  horizon === h.value
                    ? 'bg-[#64BC45] text-white shadow-sm border border-[#64BC45]'
                    : 'bg-[#F5F7F4] hover:bg-[#E8ECE7] text-[#788278] hover:text-[#263329] border border-[#E8ECE7]'
                }`}
              >
                {h.label}
              </button>
            ))}
          </div>
        </div>

        {/* Date Range Selector */}
        <div className="bg-white p-4 border border-[#E8ECE7] rounded-2xl space-y-2 shadow-xs">
          <label className="text-xs font-semibold text-[#263329] flex items-center space-x-1.5">
            <Calendar className="w-4 h-4 text-[#469A36]" />
            <span>Select Date Range</span>
          </label>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {dateRanges.map(dr => (
              <button
                key={dr.value}
                onClick={() => setDateRange(dr.value)}
                className={`py-2 px-2.5 rounded-xl text-xs font-semibold transition-all cursor-pointer text-center ${
                  dateRange === dr.value
                    ? 'bg-[#F1F8ED] text-[#469A36] border border-[#64BC45] font-bold shadow-xs'
                    : 'bg-[#F5F7F4] hover:bg-[#E8ECE7] text-[#788278] hover:text-[#263329] border border-[#E8ECE7]'
                }`}
              >
                {dr.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Loading & Error States */}
      {loading && !accuracyData && (
        <div className="bg-white border border-[#E8ECE7] rounded-2xl p-12 text-center text-[#788278] space-y-3">
          <div className="w-8 h-8 border-2 border-[#64BC45] border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-sm">Evaluating forecast accuracy against ground truth observations...</p>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-center space-x-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0 text-red-500" />
          <span>{error}</span>
        </div>
      )}

      {accuracyData && (
        <>
          {/* Insufficient Data Guard Alert (Preserved in Real Data Mode) */}
          {!accuracyData.has_sufficient_data && dataMode === 'real' && (
            <div className="p-5 rounded-2xl bg-amber-50 border border-amber-200 text-amber-900 space-y-3">
              <div className="flex items-center space-x-2">
                <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0" />
                <h3 className="font-bold text-sm text-amber-800">
                  {accuracyData.status_message}
                </h3>
              </div>
              <p className="text-xs text-amber-800/80 leading-relaxed">
                AtmosAI requires at least 3 validated prediction-observation pairs within the selected range before computing trusted statistical metrics.
                Live predictions have been registered and will be evaluated once corresponding ground monitoring telemetry is received.
              </p>
              <div>
                <button
                  type="button"
                  onClick={() => setDataMode('demo')}
                  className="px-4 py-2 rounded-xl bg-[#64BC45] hover:bg-[#469A36] text-white text-xs font-bold transition shadow-sm cursor-pointer"
                >
                  Switch to Demo Data Mode to Preview Dashboard
                </button>
              </div>
            </div>
          )}

          {/* Show metrics and charts whenever has_sufficient_data is true OR in demo mode */}
          {(accuracyData.has_sufficient_data || dataMode === 'demo') && (
            <>
              {/* Key Trust Metrics KPI Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* MAE Card */}
                <div className="bg-white p-5 border border-[#E8ECE7] rounded-2xl relative overflow-hidden flex flex-col justify-between shadow-xs">
                  <div>
                    <div className="flex items-center justify-between text-xs text-[#788278]">
                      <span className="font-semibold uppercase tracking-wider">Mean Absolute Error (MAE)</span>
                      <BarChart3 className="w-4 h-4 text-[#469A36]" />
                    </div>
                    <div className="mt-3 flex items-baseline space-x-2">
                      <span className="text-3xl font-extrabold text-[#263329] font-mono">
                        {accuracyData.mae !== null ? accuracyData.mae.toFixed(2) : '--'}
                      </span>
                      <span className="text-xs text-[#788278]">µg/m³</span>
                    </div>
                  </div>
                  <div className="mt-4 pt-3 border-t border-[#E8ECE7] text-[11px] text-[#788278] flex items-center justify-between">
                    <span>Persistence baseline:</span>
                    <span className="font-mono text-[#263329]">
                      {accuracyData.baseline_mae !== null ? `${accuracyData.baseline_mae.toFixed(2)} µg/m³` : '--'}
                    </span>
                  </div>
                </div>

                {/* RMSE Card */}
                <div className="bg-white p-5 border border-[#E8ECE7] rounded-2xl relative overflow-hidden flex flex-col justify-between shadow-xs">
                  <div>
                    <div className="flex items-center justify-between text-xs text-[#788278]">
                      <span className="font-semibold uppercase tracking-wider">Root Mean Squared Error (RMSE)</span>
                      <TrendingUp className="w-4 h-4 text-[#469A36]" />
                    </div>
                    <div className="mt-3 flex items-baseline space-x-2">
                      <span className="text-3xl font-extrabold text-[#263329] font-mono">
                        {accuracyData.rmse !== null ? accuracyData.rmse.toFixed(2) : '--'}
                      </span>
                      <span className="text-xs text-[#788278]">µg/m³</span>
                    </div>
                  </div>
                  <div className="mt-4 pt-3 border-t border-[#E8ECE7] text-[11px] text-[#788278] flex items-center justify-between">
                    <span>Penalizes peak variance:</span>
                    <span className="font-mono text-[#469A36] font-semibold">Lower is better</span>
                  </div>
                </div>

                {/* Sample Pairs Count */}
                <div className="bg-white p-5 border border-[#E8ECE7] rounded-2xl relative overflow-hidden flex flex-col justify-between shadow-xs">
                  <div>
                    <div className="flex items-center justify-between text-xs text-[#788278]">
                      <span className="font-semibold uppercase tracking-wider">Validated Observations</span>
                      <CheckCircle2 className="w-4 h-4 text-[#469A36]" />
                    </div>
                    <div className="mt-3 flex items-baseline space-x-2">
                      <span className="text-3xl font-extrabold text-[#469A36] font-mono">
                        {accuracyData.validated_sample_count}
                      </span>
                      <span className="text-xs text-[#788278]">matched pairs (N)</span>
                    </div>
                  </div>
                  <div className="mt-4 pt-3 border-t border-[#E8ECE7] text-[11px] text-[#788278] flex items-center justify-between">
                    <span>Validation Window:</span>
                    <span className="font-mono text-[#469A36] font-semibold">±45m tolerance</span>
                  </div>
                </div>

                {/* Baseline Advantage / Improvement */}
                <div className="bg-white p-5 border border-[#E8ECE7] rounded-2xl relative overflow-hidden flex flex-col justify-between shadow-xs">
                  <div>
                    <div className="flex items-center justify-between text-xs text-[#788278]">
                      <span className="font-semibold uppercase tracking-wider">Baseline Advantage</span>
                      <Layers className="w-4 h-4 text-[#469A36]" />
                    </div>
                    <div className="mt-3 flex items-baseline space-x-2">
                      <span className={`text-3xl font-extrabold font-mono ${
                        (accuracyData.mae_improvement_pct ?? 0) >= 0 ? 'text-[#469A36]' : 'text-[#263329]'
                      }`}>
                        {accuracyData.mae_improvement_pct !== null ? `${accuracyData.mae_improvement_pct > 0 ? '+' : ''}${accuracyData.mae_improvement_pct.toFixed(1)}%` : '--'}
                      </span>
                      <span className="text-xs text-[#788278]">vs Persistence</span>
                    </div>
                  </div>
                  <div className="mt-4 pt-3 border-t border-[#E8ECE7] text-[11px] text-[#788278] flex items-center justify-between">
                    <span>Horizon:</span>
                    <span className="font-mono text-[#469A36] font-semibold">+{accuracyData.horizon_hours}h ahead</span>
                  </div>
                </div>
              </div>

              {/* Actual vs Predicted PM2.5 Line Chart */}
              <div className="bg-white p-6 border border-[#E8ECE7] rounded-2xl space-y-4 shadow-xs">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#E8ECE7] pb-4">
                  <div>
                    <h3 className="text-base font-bold text-[#263329] flex items-center space-x-2">
                      <BarChart3 className="w-4 h-4 text-[#469A36]" />
                      <span>Actual vs Predicted PM2.5 Concentration ({accuracyData.horizon_hours}h Horizon)</span>
                    </h3>
                    <p className="text-xs text-[#788278] mt-0.5">
                      {dataMode === 'demo'
                        ? 'Simulated benchmark dataset. Predicted values generated with horizon-calibrated baseline model.'
                        : 'Chronological test observations matched to AtmosAI predictions. Hover over data points to inspect individual prediction errors.'}
                    </p>
                  </div>

                  {/* Data Source Badge */}
                  <div className="flex items-center space-x-2 text-[11px] font-mono text-[#788278] bg-[#F5F7F4] px-3 py-1.5 rounded-lg border border-[#E8ECE7]">
                    <Database className="w-3.5 h-3.5 text-[#469A36]" />
                    <span>Source: <span className="text-[#263329]">{accuracyData.observation_source}</span></span>
                  </div>
                </div>

                {/* Recharts Chart Canvas */}
                <div className="h-80 w-full pt-4">
                  {accuracyData.chart_data && accuracyData.chart_data.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={accuracyData.chart_data} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#E8ECE7" />
                        <XAxis 
                          dataKey="display_time" 
                          stroke="#788278" 
                          tick={{ fill: '#788278', fontSize: 10 }}
                          tickLine={false}
                        />
                        <YAxis 
                          stroke="#788278" 
                          tick={{ fill: '#788278', fontSize: 10 }}
                          tickLine={false}
                          domain={['auto', 'auto']}
                          unit=" µg/m³"
                        />
                        <Tooltip 
                          content={({ active, payload, label }) => {
                            if (active && payload && payload.length) {
                              const data = payload[0].payload;
                              return (
                                <div className="bg-white border border-[#E8ECE7] p-3 rounded-xl shadow-xl text-xs space-y-1.5">
                                  <p className="font-bold text-[#263329] border-b border-[#E8ECE7] pb-1 font-mono">
                                    Target Time: {label}
                                  </p>
                                  <div className="flex items-center justify-between space-x-4">
                                    <span className="text-[#469A36] font-semibold flex items-center space-x-1">
                                      <span className="w-2 h-2 rounded-full bg-[#469A36] inline-block" />
                                      <span>Actual Observed:</span>
                                    </span>
                                    <span className="font-mono text-[#263329] font-bold">
                                      {data.actual_pm25 !== null ? `${data.actual_pm25.toFixed(1)} µg/m³` : 'Pending'}
                                    </span>
                                  </div>
                                  <div className="flex items-center justify-between space-x-4">
                                    <span className="text-[#7FC441] font-semibold flex items-center space-x-1">
                                      <span className="w-2 h-2 rounded-full bg-[#7FC441] inline-block" />
                                      <span>Predicted:</span>
                                    </span>
                                    <span className="font-mono text-[#263329] font-bold">
                                      {data.predicted_pm25.toFixed(1)} µg/m³
                                    </span>
                                  </div>
                                  {data.absolute_error !== null && (
                                    <div className="flex items-center justify-between space-x-4 pt-1 border-t border-[#E8ECE7] text-[11px]">
                                      <span className="text-[#788278]">Absolute Error:</span>
                                      <span className="font-mono text-[#469A36] font-bold">
                                        {data.absolute_error.toFixed(1)} µg/m³
                                      </span>
                                    </div>
                                  )}
                                </div>
                              );
                            }
                            return null;
                          }}
                        />
                        <Legend 
                          wrapperStyle={{ paddingTop: '15px' }}
                          formatter={(value) => <span className="text-xs text-[#263329] font-semibold mr-4">{value}</span>}
                        />
                        <Line 
                          type="monotone" 
                          dataKey="actual_pm25" 
                          name="Actual PM2.5 (Ground Truth)" 
                          stroke="#469A36" 
                          strokeWidth={2}
                          dot={false}
                          activeDot={{ r: 5, fill: '#469A36', stroke: '#ffffff' }}
                        />
                        <Line 
                          type="monotone" 
                          dataKey="predicted_pm25" 
                          name="Predicted PM2.5 (Forecast Model)" 
                          stroke="#7FC441" 
                          strokeWidth={2}
                          strokeDasharray="4 2"
                          dot={false}
                          activeDot={{ r: 5, fill: '#7FC441', stroke: '#ffffff' }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-full flex items-center justify-center text-[#788278] text-xs">
                      No chart data available for the selected filters.
                    </div>
                  )}
                </div>
              </div>

              {/* Model Provenance & Verification Principles */}
              <div className="bg-white p-5 border border-[#E8ECE7] rounded-2xl space-y-3 shadow-xs">
                <h4 className="text-xs font-bold uppercase tracking-wider text-[#469A36] flex items-center space-x-1.5">
                  <Info className="w-4 h-4 text-[#469A36]" />
                  <span>Trust & Verification Methodology</span>
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-[#263329]">
                  <div className="space-y-1">
                    <span className="font-semibold text-[#263329] block">
                      {dataMode === 'demo' ? 'Controlled Synthetic Generation' : 'Strict Out-of-Sample Evaluation'}
                    </span>
                    <p className="text-[#788278] text-[11px] leading-relaxed">
                      {dataMode === 'demo'
                        ? 'Synthetic records generated with fixed deterministic seed (42) and diurnal dynamics. Prediction error scales with horizon.'
                        : 'Predictions are strictly evaluated against forward chronological observations. No random shuffling or future data leakage.'}
                    </p>
                  </div>
                  <div className="space-y-1">
                    <span className="font-semibold text-[#263329] block">Strict Timestamp Alignment</span>
                    <p className="text-[#788278] text-[11px] leading-relaxed">
                      Predictions and observations are strictly paired by target timestamp and horizon. Never compares mismatched dates or unrelated locations.
                    </p>
                  </div>
                  <div className="space-y-1">
                    <span className="font-semibold text-[#263329] block">Dynamic Mathematical Metrics</span>
                    <p className="text-[#788278] text-[11px] leading-relaxed">
                      MAE and RMSE are computed dynamically from matched validation pairs. Metrics are never hardcoded or simulated with fake success rates.
                    </p>
                  </div>
                </div>
              </div>

              {/* Historical Forecast Records Table */}
              <div className="bg-white p-6 border border-[#E8ECE7] rounded-2xl space-y-4 shadow-xs">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#E8ECE7] pb-4">
                  <div>
                    <h3 className="text-base font-bold text-[#263329] flex items-center space-x-2">
                      <Database className="w-4 h-4 text-[#469A36]" />
                      <span>Forecast Verification History Log</span>
                    </h3>
                    <p className="text-xs text-[#788278] mt-0.5">
                      Detailed inspection of individual forecast records, matching ground stations, and error residuals.
                    </p>
                  </div>

                  {/* Filter tabs: All, Validated, Pending */}
                  <div className="flex items-center space-x-1 bg-[#F5F7F4] p-1 rounded-xl border border-[#E8ECE7] text-xs">
                    <button
                      onClick={() => setActiveHistoryTab('all')}
                      className={`px-3 py-1 rounded-lg font-semibold transition-all cursor-pointer ${
                        activeHistoryTab === 'all'
                          ? 'bg-white text-[#469A36] border border-[#C2EBBA] font-bold shadow-xs'
                          : 'text-[#788278] hover:text-[#263329]'
                      }`}
                    >
                      All ({accuracyData.forecast_history?.length || 0})
                    </button>
                    <button
                      onClick={() => setActiveHistoryTab('validated')}
                      className={`px-3 py-1 rounded-lg font-semibold transition-all cursor-pointer ${
                        activeHistoryTab === 'validated'
                          ? 'bg-white text-[#469A36] border border-[#C2EBBA] font-bold shadow-xs'
                          : 'text-[#788278] hover:text-[#263329]'
                      }`}
                    >
                      Validated ({accuracyData.validated_sample_count})
                    </button>
                    <button
                      onClick={() => setActiveHistoryTab('pending')}
                      className={`px-3 py-1 rounded-lg font-semibold transition-all cursor-pointer ${
                        activeHistoryTab === 'pending'
                          ? 'bg-white text-[#469A36] border border-[#C2EBBA] font-bold shadow-xs'
                          : 'text-[#788278] hover:text-[#263329]'
                      }`}
                    >
                      Pending ({accuracyData.forecast_history?.filter(r => !r.is_validated).length || 0})
                    </button>
                  </div>
                </div>

                {/* Table */}
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-[#F1F8ED] text-[#263329] uppercase font-mono text-[10px]">
                      <tr>
                        <th className="p-3">Target Time</th>
                        <th className="p-3">Horizon</th>
                        <th className="p-3">Predicted</th>
                        <th className="p-3">Actual Observed</th>
                        <th className="p-3">Absolute Error</th>
                        <th className="p-3">Status</th>
                        <th className="p-3">Source Type</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#E8ECE7] font-mono text-[#263329]">
                      {filteredHistory.length > 0 ? (
                        filteredHistory.slice(0, 50).map((rec) => {
                          const targetDate = new Date(rec.target_timestamp);
                          const formattedTime = targetDate.toLocaleDateString([], {
                            month: 'short',
                            day: 'numeric'
                          }) + ' ' + targetDate.toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit'
                          });

                          return (
                            <tr key={rec.id} className="hover:bg-[#F5F7F4]/80 transition-colors">
                              <td className="p-3 text-[#788278]">{formattedTime}</td>
                              <td className="p-3">
                                <span className="px-2 py-0.5 rounded bg-[#F1F8ED] text-[#469A36] text-[10px] font-bold">
                                  +{rec.horizon_hours}h
                                </span>
                              </td>
                              <td className="p-3 font-bold text-[#469A36]">
                                {rec.predicted_pm25.toFixed(1)} µg/m³
                              </td>
                              <td className="p-3">
                                {rec.actual_pm25 !== null ? (
                                  <span className="font-bold text-[#263329]">
                                    {rec.actual_pm25.toFixed(1)} µg/m³
                                  </span>
                                ) : (
                                  <span className="text-[#788278] italic">Awaiting observation</span>
                                )}
                              </td>
                              <td className="p-3">
                                {rec.absolute_error !== null ? (
                                  <span className="font-bold text-[#469A36]">
                                    {rec.absolute_error.toFixed(1)} µg/m³
                                  </span>
                                ) : (
                                  <span className="text-[#788278]">--</span>
                                )}
                              </td>
                              <td className="p-3">
                                {rec.validation_status === 'validated' && (
                                  <span className="px-2 py-0.5 rounded-full bg-[#F1F8ED] text-[#469A36] border border-[#C2EBBA] text-[10px] font-bold inline-flex items-center space-x-1">
                                    <CheckCircle2 className="w-3 h-3" />
                                    <span>Validated</span>
                                  </span>
                                )}
                                {rec.validation_status === 'pending' && (
                                  <span className="px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200 text-[10px] font-bold inline-flex items-center space-x-1">
                                    <Clock className="w-3 h-3" />
                                    <span>Pending</span>
                                  </span>
                                )}
                                {rec.validation_status.startsWith('rejected') && (
                                  <span className="px-2 py-0.5 rounded-full bg-red-50 text-red-700 border border-red-200 text-[10px] font-bold">
                                    Rejected
                                  </span>
                                )}
                              </td>
                              <td className="p-3 text-[11px] text-[#788278] font-sans">
                                {rec.data_source === 'SIMULATED' ? (
                                  <span className="px-2 py-0.5 rounded bg-amber-100 text-amber-800 font-mono text-[10px] font-bold border border-amber-300">
                                    SIMULATED
                                  </span>
                                ) : (
                                  rec.observation_source || 'Ground Telemetry'
                                )}
                              </td>
                            </tr>
                          );
                        })
                      ) : (
                        <tr>
                          <td colSpan="7" className="p-6 text-center text-[#788278] font-sans">
                            No forecast records match the selected filter.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
                {filteredHistory.length > 50 && (
                  <p className="text-[11px] text-[#788278] text-center font-mono">
                    Showing most recent 50 of {filteredHistory.length} validation records.
                  </p>
                )}
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
}

