import React from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Wind, 
  ShieldCheck, 
  Sparkles, 
  ArrowRight, 
  BarChart3,
  Users
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function WelcomePage() {
  const navigate = useNavigate();
  const { authDisclaimer } = useAuth();

  return (
    <div className="min-h-screen bg-[#F5F7F4] text-[#263329] flex flex-col font-sans selection:bg-[#64BC45] selection:text-white">
      {/* Top Banner if in Demo Auth Mode */}
      {authDisclaimer && (
        <div className="bg-amber-50 border-b border-amber-200 px-4 py-2 text-center text-xs text-amber-800 flex items-center justify-center space-x-2">
          <span className="font-bold uppercase tracking-wider text-[10px] px-2 py-0.5 rounded bg-amber-200/80 text-amber-900">
            Notice
          </span>
          <span>{authDisclaimer}</span>
        </div>
      )}

      {/* Header */}
      <header className="max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-5 flex items-center justify-between">
        <div className="flex items-center space-x-3 cursor-pointer" onClick={() => navigate('/welcome')}>
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-[#469A36] to-[#64BC45] flex items-center justify-center text-white shadow-sm shadow-[#64BC45]/20">
            <Wind className="w-6 h-6 stroke-[2.2]" />
          </div>
          <div>
            <span className="text-xl font-extrabold tracking-tight text-[#263329]">Atmos<span className="text-[#64BC45]">AI</span></span>
            <span className="block text-[10px] font-semibold tracking-wider uppercase text-[#788278]">Breathe Smarter</span>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <button
            type="button"
            onClick={() => navigate('/login')}
            className="px-4 py-2 text-xs font-bold text-[#263329] hover:text-[#469A36] rounded-xl hover:bg-[#F1F8ED] transition"
          >
            Log In
          </button>
          <button
            type="button"
            onClick={() => navigate('/signup')}
            className="px-5 py-2.5 text-xs font-bold text-white bg-[#64BC45] hover:bg-[#469A36] rounded-xl transition shadow-sm shadow-[#64BC45]/25 flex items-center space-x-1.5"
          >
            <span>Get Started</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1 flex flex-col justify-center max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12 text-center">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-[#F1F8ED] border border-[#C2EBBA] text-[#469A36] text-xs font-bold mx-auto mb-6">
          <Sparkles className="w-3.5 h-3.5 text-[#64BC45]" />
          <span>Hyperlocal Environmental Intelligence for Bengaluru</span>
        </div>

        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-[#263329] tracking-tight max-w-3xl mx-auto leading-tight sm:leading-none">
          Breathe Smarter, <br className="hidden sm:block" />
          <span className="text-[#469A36]">Live Safer.</span>
        </h1>

        <p className="mt-5 text-base sm:text-lg text-[#788278] max-w-2xl mx-auto leading-relaxed">
          AtmosAI pairs real ground sensor telemetry with reproducible ML forecasts and rule-based CPCB safety advisories. Tailored for students, runners, commuters, and families.
        </p>

        {/* CTA Buttons */}
        <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3">
          <button
            type="button"
            onClick={() => navigate('/signup')}
            className="w-full sm:w-auto px-8 py-3.5 rounded-2xl bg-[#64BC45] hover:bg-[#469A36] text-white text-sm font-bold shadow-md shadow-[#64BC45]/25 transition flex items-center justify-center space-x-2"
          >
            <span>Create Your Free Profile</span>
            <ArrowRight className="w-4 h-4" />
          </button>
          <button
            type="button"
            onClick={() => navigate('/login')}
            className="w-full sm:w-auto px-8 py-3.5 rounded-2xl bg-white hover:bg-[#F1F8ED] text-[#263329] border border-[#E8ECE7] text-sm font-bold shadow-xs transition"
          >
            Sign In with Existing Account
          </button>
        </div>

        {/* Key Feature Highlights Grid */}
        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-6 text-left">
          <div className="p-6 rounded-2xl bg-white border border-[#E8ECE7] shadow-xs hover:border-[#C2EBBA] transition">
            <div className="w-10 h-10 rounded-xl bg-[#F1F8ED] text-[#469A36] flex items-center justify-center mb-4">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-base text-[#263329]">CPCB Standard NAQI</h3>
            <p className="mt-2 text-xs text-[#788278] leading-relaxed">
              Official Indian National Air Quality Index categories with transparent multi-pollutant calculations and non-medical safety guidance.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-white border border-[#E8ECE7] shadow-xs hover:border-[#C2EBBA] transition">
            <div className="w-10 h-10 rounded-xl bg-[#F1F8ED] text-[#469A36] flex items-center justify-center mb-4">
              <BarChart3 className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-base text-[#263329]">Verified ML Forecasts</h3>
            <p className="mt-2 text-xs text-[#788278] leading-relaxed">
              1-hour, 3-hour, and 6-hour atmospheric predictions backed by dynamic MAE and RMSE accuracy evaluations against real ground sensors.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-white border border-[#E8ECE7] shadow-xs hover:border-[#C2EBBA] transition">
            <div className="w-10 h-10 rounded-xl bg-[#F1F8ED] text-[#469A36] flex items-center justify-center mb-4">
              <Users className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-base text-[#263329]">Persona Prioritization</h3>
            <p className="mt-2 text-xs text-[#788278] leading-relaxed">
              Dynamic widget reordering for students, runners, cyclists, outdoor workers, and parents. Environmental values remain 100% genuine.
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-[#E8ECE7] py-6 px-4 text-center text-xs text-[#788278]">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>AtmosAI &bull; Breathe Smarter, Live Safer</span>
          <span className="text-[11px] text-[#469A36] font-mono">
            Bengaluru Ground Network &bull; CPCB NAQI &bull; Open-Meteo &bull; Google Gemini
          </span>
        </div>
      </footer>
    </div>
  );
}
