import React, { useState } from 'react';
import { 
  Watch, 
  Heart, 
  Footprints, 
  Flame, 
  Wind, 
  AlertTriangle, 
  ShieldCheck, 
  RefreshCw,
  Info
} from 'lucide-react';
import { postTelemetry } from '../services/api';

export default function WearablePrototype({ liveData }) {
  const [heartRate, setHeartRate] = useState(78);
  const [steps, setSteps] = useState(5420);
  const [activity, setActivity] = useState('walking');
  const [isSyncing, setIsSyncing] = useState(false);
  const [advisory, setAdvisory] = useState(null);

  const simulateStepIncrease = async (deltaSteps, targetHeartRate, newActivity) => {
    const nextSteps = steps + deltaSteps;
    const nextHR = targetHeartRate;
    setSteps(nextSteps);
    setHeartRate(nextHR);
    setActivity(newActivity);

    setIsSyncing(true);
    try {
      const res = await postTelemetry({
        device_id: 'atmos_wear_proto_01',
        timestamp: new Date().toISOString(),
        heart_rate: nextHR,
        step_count: nextSteps,
        activity_type: newActivity,
        ambient_pm25: liveData?.pm25 || 25.0,
        source: 'simulated_wearable_prototype'
      });
      if (res && res.contextual_advisory) {
        setAdvisory(res.contextual_advisory);
      } else {
        setAdvisory(null);
      }
    } catch (err) {
      console.error('Failed to sync wearable telemetry:', err);
    } finally {
      setIsSyncing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="p-4 rounded-2xl bg-white border border-[#E8ECE7] shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center space-x-2">
              <Watch className="w-5 h-5 text-[#469A36]" />
              <h1 className="text-xl font-bold text-[#263329] tracking-tight">AtmosAI PulseWear &bull; Wearable Prototype</h1>
              <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-[#F1F8ED] text-[#469A36] border border-[#C2EBBA]">
                Simulated Prototype
              </span>
            </div>
            <p className="text-xs text-[#788278] mt-0.5">
              Contextual bio-environmental fusion linking ambient atmospheric sensors with wearable activity metrics.
            </p>
          </div>

          <div className="text-xs text-[#788278] font-mono">
            Device: <strong className="text-[#469A36]">PulseWear-v1-Proto</strong>
          </div>
        </div>
      </div>

      {/* Main Prototype Simulation Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
        {/* Left: Interactive Simulated Smartwatch Screen */}
        <div className="flex justify-center">
          <div className="w-80 h-96 rounded-[2.5rem] bg-gradient-to-b from-[#1b2b20] via-[#101b13] to-[#0a120c] p-4 shadow-2xl border-4 border-[#263329] relative flex flex-col justify-between">
            {/* Watch Top Bezel */}
            <div className="flex items-center justify-between text-[11px] text-slate-400 px-2 pt-1 border-b border-white/10">
              <span className="font-mono text-[#64BC45] font-bold">AtmosOS</span>
              <span className="font-mono text-slate-300">12:30 PM</span>
            </div>

            {/* Watch Face Center Metrics */}
            <div className="text-center space-y-3 py-2">
              {/* Heart Rate Display */}
              <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-red-500/10 border border-red-500/30 text-red-300">
                <Heart className="w-4 h-4 text-red-400 animate-bounce" />
                <span className="text-lg font-extrabold font-mono">{heartRate}</span>
                <span className="text-[10px] text-slate-400">BPM</span>
              </div>

              {/* Step Count */}
              <div>
                <p className="text-3xl font-extrabold text-white font-mono tracking-tight">{steps.toLocaleString()}</p>
                <p className="text-[11px] text-slate-400">Daily Steps &bull; <span className="capitalize text-[#7FC441]">{activity}</span></p>
              </div>

              {/* Ambient PM2.5 Live Environmental Tile */}
              <div className="p-3 rounded-xl bg-black/40 border border-[#64BC45]/30 text-left space-y-1 mx-2">
                <div className="flex items-center justify-between text-[10px] text-slate-400">
                  <span className="flex items-center space-x-1">
                    <Wind className="w-3 h-3 text-[#64BC45]" />
                    <span>Ambient PM2.5</span>
                  </span>
                  <span className="text-[#7FC441] font-bold">{liveData?.aqi_category || 'Good'}</span>
                </div>
                <div className="flex items-baseline space-x-2">
                  <span className="text-xl font-extrabold text-[#64BC45] font-mono">
                    {liveData?.pm25 !== null && liveData?.pm25 !== undefined ? `${liveData.pm25} µg/m³` : '20.0 µg/m³'}
                  </span>
                </div>
              </div>
            </div>

            {/* Watch Bottom Context Alert Bar */}
            <div className="p-2 rounded-xl bg-black/60 border border-white/10 text-[10px] text-slate-400 text-center">
              {advisory ? (
                <span className="text-amber-300 font-medium">{advisory}</span>
              ) : (
                <span>Vitals & ambient exposure synchronized</span>
              )}
            </div>
          </div>
        </div>

        {/* Right: Simulation Controls & Verification */}
        <div className="bg-white p-6 border border-[#E8ECE7] rounded-2xl space-y-5 shadow-xs">
          <div className="space-y-1">
            <h3 className="text-base font-bold text-[#263329]">Prototype Activity Simulation Controls</h3>
            <p className="text-xs text-[#788278]">
              Test bio-environmental response by simulating exertion levels in ambient air.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
            <button
              onClick={() => simulateStepIncrease(300, 82, 'resting')}
              className="p-3 rounded-xl bg-[#F5F7F4] hover:bg-[#E8ECE7] border border-[#E8ECE7] text-left transition cursor-pointer"
            >
              <p className="text-xs font-semibold text-[#263329]">Simulate Resting</p>
              <p className="text-[11px] text-[#788278] mt-0.5">HR ~82 BPM &bull; Baseline indoor</p>
            </button>

            <button
              onClick={() => simulateStepIncrease(850, 115, 'walking')}
              className="p-3 rounded-xl bg-[#F5F7F4] hover:bg-[#E8ECE7] border border-[#E8ECE7] text-left transition cursor-pointer"
            >
              <p className="text-xs font-semibold text-[#263329]">Simulate Moderate Walk</p>
              <p className="text-[11px] text-[#788278] mt-0.5">HR ~115 BPM &bull; Street commute</p>
            </button>

            <button
              onClick={() => simulateStepIncrease(1800, 155, 'running')}
              className="p-3 rounded-xl bg-[#F5F7F4] hover:bg-[#E8ECE7] border border-[#E8ECE7] text-left transition cursor-pointer"
            >
              <p className="text-xs font-semibold text-[#263329]">Simulate High Aerobic Run</p>
              <p className="text-[11px] text-[#788278] mt-0.5">HR ~155 BPM &bull; Outdoor exertion</p>
            </button>

            <button
              onClick={() => simulateStepIncrease(200, 75, 'resting')}
              className="p-3 rounded-xl bg-[#F5F7F4] hover:bg-[#E8ECE7] border border-[#E8ECE7] text-left transition cursor-pointer"
            >
              <p className="text-xs font-semibold text-[#263329]">Cool-Down / Rest</p>
              <p className="text-[11px] text-[#788278] mt-0.5">HR ~75 BPM &bull; Recovery</p>
            </button>
          </div>

          {/* Context Advisory Response Alert */}
          {advisory && (
            <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-200 flex items-start space-x-3 text-amber-900 text-xs">
              <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-amber-900">Contextual Exertion Alert</p>
                <p className="text-[11px] text-amber-800 mt-0.5">{advisory}</p>
              </div>
            </div>
          )}

          {/* Non-medical Disclaimer */}
          <div className="p-3.5 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7] text-[11px] text-[#788278] flex items-start space-x-2.5">
            <Info className="w-4 h-4 text-[#788278] flex-shrink-0 mt-0.5" />
            <p className="leading-relaxed">
              AtmosAI Wear is an exploratory prototype. Telemetry is treated strictly as contextual information.
              It does not claim direct Fastrack hardware integration or clinical diagnostic capability.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

