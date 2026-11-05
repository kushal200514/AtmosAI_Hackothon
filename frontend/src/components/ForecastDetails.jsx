import React, { useState } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  Minus, 
  Cpu, 
  CheckCircle2, 
  AlertTriangle, 
  Clock, 
  SlidersHorizontal,
  ShieldCheck,
  BarChart3
} from 'lucide-react';
import ForecastAccuracyDashboard from './ForecastAccuracyDashboard';

export default function ForecastDetails({ forecastData, selectedLocation = 'bengaluru_central', initialView = 'pipeline' }) {
  const [activeSubTab, setActiveSubTab] = useState(initialView);

  if (!forecastData) {
    return (
      <div className="bg-white border border-[#E8ECE7] rounded-2xl p-8 text-center text-[#788278]">
        Loading multi-horizon forecasting details...
      </div>
    );
  }

  const getTrendIcon = (trend) => {
    if (trend === 'rising') return <TrendingUp className="w-4 h-4 text-red-500" />;
    if (trend === 'falling') return <TrendingDown className="w-4 h-4 text-[#469A36]" />;
    return <Minus className="w-4 h-4 text-[#788278]" />;
  };

  return (
    <div className="space-y-6">
      {/* Top View Switcher */}
      <div className="flex items-center space-x-2 bg-white p-1.5 rounded-2xl border border-[#E8ECE7] w-fit shadow-xs">
        <button
          onClick={() => setActiveSubTab('pipeline')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
            activeSubTab === 'pipeline'
              ? 'bg-[#64BC45] text-white shadow-sm'
              : 'text-[#788278] hover:text-[#263329]'
          }`}
        >
          <TrendingUp className="w-4 h-4" />
          <span>Multi-Horizon Forecast</span>
        </button>

        <button
          onClick={() => setActiveSubTab('accuracy')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
            activeSubTab === 'accuracy'
              ? 'bg-[#64BC45] text-white shadow-sm'
              : 'text-[#788278] hover:text-[#263329]'
          }`}
        >
          <ShieldCheck className="w-4 h-4" />
          <span>Accuracy Verification</span>
        </button>
      </div>

      {activeSubTab === 'accuracy' ? (
        <ForecastAccuracyDashboard selectedLocation={selectedLocation} />
      ) : (
        <>
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-2xl bg-white border border-[#E8ECE7] shadow-xs">
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-xl font-bold text-[#263329] tracking-tight">Machine Learning Forecasting Pipeline</h1>
                <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded-full bg-[#F1F8ED] text-[#469A36] border border-[#C2EBBA]">
                  {forecastData.model_version}
                </span>
              </div>
              <p className="text-xs text-[#788278] mt-0.5">
                LightGBM Gradient Boosted Decision Trees trained with chronological split and no future leakage.
              </p>
            </div>

            <div className="text-xs text-[#788278]">
              Generated: <span className="font-mono text-[#263329]">{new Date(forecastData.generated_at).toLocaleTimeString()}</span>
            </div>
          </div>

          {/* 4 Horizons Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {forecastData.forecast_points.map((pt) => {
              return (
                <div key={pt.horizon_hours} className="bg-white p-5 border border-[#E8ECE7] rounded-2xl flex flex-col justify-between shadow-xs hover:border-[#64BC45] transition">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-[#469A36] uppercase tracking-wider">
                        {pt.target_time_label}
                      </span>
                      <div className="flex items-center space-x-1">
                        {getTrendIcon(pt.trend)}
                        <span className="text-xs capitalize font-medium text-[#263329]">{pt.trend}</span>
                      </div>
                    </div>

                    <div>
                      <div className="flex items-baseline space-x-2">
                        <span className="text-3xl font-extrabold text-[#263329] font-mono">{pt.predicted_pm25}</span>
                        <span className="text-xs text-[#788278]">µg/m³</span>
                      </div>
                      <p className="text-xs text-[#788278] mt-1">
                        90% CI: <span className="text-[#469A36] font-mono">[{pt.confidence_lower} – {pt.confidence_upper}]</span>
                      </p>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-[#E8ECE7] text-[11px] flex items-center justify-between mt-4">
                    <span className="text-[#788278]">Risk Bracket:</span>
                    <span className="font-semibold text-[#263329]">{pt.risk_level}</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Benchmark & Out-of-Sample Metrics Table */}
          <div className="bg-white p-6 border border-[#E8ECE7] rounded-2xl space-y-4 shadow-xs">
            <h3 className="text-sm font-bold text-[#263329] flex items-center space-x-2">
              <Cpu className="w-4 h-4 text-[#469A36]" />
              <span>Out-of-Sample Test Set Benchmark (LightGBM vs Persistence Baseline)</span>
            </h3>
            <p className="text-xs text-[#788278]">
              Evaluated strictly on forward chronological test observations (no future leakage). Shows performance comparison across horizons.
            </p>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-[#F1F8ED] text-[#263329] uppercase font-mono text-[10px]">
                  <tr>
                    <th className="p-3">Horizon</th>
                    <th className="p-3">LightGBM MAE</th>
                    <th className="p-3">LightGBM RMSE</th>
                    <th className="p-3">Persistence MAE</th>
                    <th className="p-3">Persistence RMSE</th>
                    <th className="p-3">MAE Advantage</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#E8ECE7] font-mono text-[#263329]">
                  <tr>
                    <td className="p-3 font-bold text-[#469A36]">+1 Hour</td>
                    <td className="p-3">5.01 µg/m³</td>
                    <td className="p-3">6.80</td>
                    <td className="p-3">4.62 µg/m³</td>
                    <td className="p-3">6.35</td>
                    <td className="p-3 text-[#788278]">Persistence competitive</td>
                  </tr>
                  <tr>
                    <td className="p-3 font-bold text-[#469A36]">+3 Hours</td>
                    <td className="p-3">7.38 µg/m³</td>
                    <td className="p-3">9.77</td>
                    <td className="p-3">6.96 µg/m³</td>
                    <td className="p-3">9.60</td>
                    <td className="p-3 text-[#788278]">Persistence competitive</td>
                  </tr>
                  <tr>
                    <td className="p-3 font-bold text-[#469A36]">+4 Hours</td>
                    <td className="p-3">8.02 µg/m³</td>
                    <td className="p-3">10.89</td>
                    <td className="p-3">8.47 µg/m³</td>
                    <td className="p-3">11.20</td>
                    <td className="p-3 text-[#469A36] font-bold">+5.3% improvement</td>
                  </tr>
                  <tr>
                    <td className="p-3 font-bold text-[#469A36]">+5 Hours</td>
                    <td className="p-3">8.86 µg/m³</td>
                    <td className="p-3">11.73</td>
                    <td className="p-3">9.61 µg/m³</td>
                    <td className="p-3">12.39</td>
                    <td className="p-3 text-[#469A36] font-bold">+7.7% improvement</td>
                  </tr>
                  <tr>
                    <td className="p-3 font-bold text-[#469A36]">+6 Hours</td>
                    <td className="p-3">9.33 µg/m³</td>
                    <td className="p-3">12.11</td>
                    <td className="p-3">10.27 µg/m³</td>
                    <td className="p-3">13.16</td>
                    <td className="p-3 text-[#469A36] font-bold">+9.2% improvement</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Primary Driving Factors */}
          <div className="bg-white p-6 border border-[#E8ECE7] rounded-2xl space-y-3 shadow-xs">
            <h3 className="text-sm font-bold text-[#263329] flex items-center space-x-2">
              <SlidersHorizontal className="w-4 h-4 text-[#469A36]" />
              <span>Active Environmental Drivers</span>
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
              {forecastData.primary_driving_factors.map((factor, i) => (
                <div key={i} className="p-3 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7] text-xs text-[#263329] flex items-center space-x-2.5">
                  <CheckCircle2 className="w-4 h-4 text-[#469A36] flex-shrink-0" />
                  <span>{factor}</span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

