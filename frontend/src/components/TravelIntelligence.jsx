import React, { useState, useEffect } from 'react';
import { 
  Navigation, 
  Car, 
  Bike, 
  Footprints, 
  Clock, 
  MapPin, 
  AlertCircle, 
  ShieldCheck, 
  ArrowRight,
  Calculator
} from 'lucide-react';
import { calculateTravelExposure } from '../services/api';

export default function TravelIntelligence({ locations }) {
  const [origin, setOrigin] = useState('yelahanka');
  const [destination, setDestination] = useState('silk_board');
  const [mode, setMode] = useState('commute');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const runCalculation = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await calculateTravelExposure(origin, destination, mode);
      setResult(data);
    } catch (err) {
      setError(err.message || 'Failed to calculate travel exposure');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runCalculation();
  }, [origin, destination, mode]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="p-4 rounded-2xl bg-white border border-[#E8ECE7] shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center space-x-2">
              <Navigation className="w-5 h-5 text-[#469A36]" />
              <h1 className="text-xl font-bold text-[#263329] tracking-tight">Travel Environmental Exposure Intelligence</h1>
            </div>
            <p className="text-xs text-[#788278] mt-0.5">
              Point-to-point atmospheric exposure model for Bengaluru commute corridors.
            </p>
          </div>

          <div className="text-xs text-[#788278] flex items-center space-x-1.5 font-mono">
            <Calculator className="w-3.5 h-3.5 text-[#469A36]" />
            <span>Formula: E = Σ(Ci &bull; Δti) / ΣΔti</span>
          </div>
        </div>
      </div>

      {/* Origin, Destination & Mode Selector Card */}
      <div className="bg-white p-6 border border-[#E8ECE7] rounded-2xl space-y-4 shadow-xs">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Origin */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-[#788278]">Starting Point</label>
            <select
              value={origin}
              onChange={(e) => setOrigin(e.target.value)}
              className="w-full p-2.5 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7] text-[#263329] text-xs font-medium outline-none focus:border-[#64BC45] focus:bg-white transition"
            >
              {locations.map((loc) => (
                <option key={loc.name} value={loc.name}>{loc.display_name}</option>
              ))}
            </select>
          </div>

          {/* Destination */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-[#788278]">Destination</label>
            <select
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
              className="w-full p-2.5 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7] text-[#263329] text-xs font-medium outline-none focus:border-[#64BC45] focus:bg-white transition"
            >
              {locations.map((loc) => (
                <option key={loc.name} value={loc.name}>{loc.display_name}</option>
              ))}
            </select>
          </div>

          {/* Mode */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-[#788278]">Transit Mode</label>
            <div className="grid grid-cols-3 gap-1.5">
              <button
                type="button"
                onClick={() => setMode('commute')}
                className={`py-2 px-2 rounded-xl text-xs font-medium border flex items-center justify-center space-x-1 transition cursor-pointer ${
                  mode === 'commute' ? 'bg-[#F1F8ED] border-[#64BC45] text-[#469A36] font-bold shadow-xs' : 'bg-[#F5F7F4] border-[#E8ECE7] text-[#788278] hover:border-[#C2EBBA] hover:text-[#263329]'
                }`}
              >
                <Car className="w-3.5 h-3.5" />
                <span>Car/Bus</span>
              </button>
              <button
                type="button"
                onClick={() => setMode('cycling')}
                className={`py-2 px-2 rounded-xl text-xs font-medium border flex items-center justify-center space-x-1 transition cursor-pointer ${
                  mode === 'cycling' ? 'bg-[#F1F8ED] border-[#64BC45] text-[#469A36] font-bold shadow-xs' : 'bg-[#F5F7F4] border-[#E8ECE7] text-[#788278] hover:border-[#C2EBBA] hover:text-[#263329]'
                }`}
              >
                <Bike className="w-3.5 h-3.5" />
                <span>Cycling</span>
              </button>
              <button
                type="button"
                onClick={() => setMode('walking')}
                className={`py-2 px-2 rounded-xl text-xs font-medium border flex items-center justify-center space-x-1 transition cursor-pointer ${
                  mode === 'walking' ? 'bg-[#F1F8ED] border-[#64BC45] text-[#469A36] font-bold shadow-xs' : 'bg-[#F5F7F4] border-[#E8ECE7] text-[#788278] hover:border-[#C2EBBA] hover:text-[#263329]'
                }`}
              >
                <Footprints className="w-3.5 h-3.5" />
                <span>Walking</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Results View */}
      {result && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Exposure Summary Card */}
          <div className="bg-white p-6 border border-[#E8ECE7] rounded-2xl flex flex-col justify-between shadow-xs">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase text-[#788278]">Estimated Exposure</span>
                <span className={`text-xs font-bold px-2 py-0.5 rounded-full border ${
                  result.risk_level === 'Low' ? 'bg-[#F1F8ED] text-[#469A36] border-[#C2EBBA]' :
                  result.risk_level === 'Moderate' ? 'bg-amber-50 text-amber-700 border-amber-200' :
                  'bg-red-50 text-red-700 border-red-200'
                }`}>
                  {result.risk_level} Exposure
                </span>
              </div>

              <div>
                <div className="flex items-baseline space-x-2">
                  <span className="text-5xl font-extrabold text-[#263329] font-mono">{result.total_exposure_index}</span>
                  <span className="text-sm font-medium text-[#788278]">µg/m³</span>
                </div>
                <p className="text-xs text-[#788278] mt-1">
                  Estimated duration: <strong className="text-[#469A36]">{result.estimated_duration_minutes} minutes</strong>
                </p>
              </div>

              <div className="p-3 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7] text-xs text-[#263329] leading-relaxed">
                {result.advisory}
              </div>
            </div>

            <div className="pt-4 border-t border-[#E8ECE7] text-[10px] text-[#788278] mt-4">
              <p>{result.disclaimer}</p>
            </div>
          </div>

          {/* Waypoint Corridor Breakdown Table */}
          <div className="lg:col-span-2 bg-white p-6 border border-[#E8ECE7] rounded-2xl space-y-4 shadow-xs">
            <h3 className="text-sm font-bold text-[#263329] flex items-center space-x-2">
              <MapPin className="w-4 h-4 text-[#469A36]" />
              <span>Route Waypoint Environmental Concentration Breakdown</span>
            </h3>

            <div className="space-y-3 pt-1">
              {result.waypoints.map((wp, idx) => (
                <div key={idx} className="p-3.5 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7] flex items-center justify-between">
                  <div className="space-y-1">
                    <p className="text-xs font-bold text-[#263329]">{wp.name}</p>
                    <p className="text-[11px] text-[#788278]">
                      Segment Duration: <span className="font-mono text-[#263329]">{wp.segment_duration_mins} mins</span> &bull; 
                      Coords: {wp.latitude.toFixed(3)}, {wp.longitude.toFixed(3)}
                    </p>
                  </div>

                  <div className="text-right">
                    <span className="text-sm font-extrabold text-[#469A36] font-mono">
                      {wp.estimated_pm25} µg/m³
                    </span>
                    <span className="text-[10px] text-[#788278] block">{wp.aqi_category}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

