import React from 'react';
import { 
  X, 
  Navigation as NavIcon, 
  Watch, 
  Bell, 
  User, 
  Cpu, 
  ShieldCheck, 
  ChevronRight,
  Server
} from 'lucide-react';

export default function MoreMenuSheet({ 
  isOpen, 
  onClose, 
  onSelectTab, 
  onOpenProfile, 
  currentProfile,
  backendStatus 
}) {
  if (!isOpen) return null;

  const menuItems = [
    {
      id: 'accuracy',
      title: 'Trust & Forecast Accuracy',
      description: 'Real PM2.5 verification, MAE, RMSE and actuals chart',
      icon: ShieldCheck,
      color: 'text-emerald-400',
      bgColor: 'bg-emerald-500/10'
    },
    {
      id: 'travel',
      title: 'Travel Intelligence',
      description: 'Point-to-point corridor exposure & route calculator',
      icon: NavIcon,
      color: 'text-teal-400',
      bgColor: 'bg-teal-500/10'
    },
    {
      id: 'wear',
      title: 'AtmosAI Wear Prototype',
      description: 'Simulated smartwatch bio-environmental telemetry',
      icon: Watch,
      color: 'text-cyan-400',
      bgColor: 'bg-cyan-500/10'
    },
    {
      id: 'alerts',
      title: 'Alerts & Web Push',
      description: 'Surge alerts and customizable AQI thresholds',
      icon: Bell,
      color: 'text-amber-400',
      bgColor: 'bg-amber-500/10'
    }
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/50 backdrop-blur-xs p-0 sm:p-4">
      <div className="fixed inset-0" onClick={onClose} />

      <div className="relative w-full max-w-md atmos-card rounded-t-3xl sm:rounded-2xl p-6 border-t sm:border border-[#E8ECE7] shadow-xl animate-sheet-up max-h-[85vh] flex flex-col z-10 bg-white">
        <div className="w-12 h-1.5 rounded-full bg-[#E8ECE7] mx-auto -mt-2 mb-4 sm:hidden" />

        <div className="flex items-center justify-between border-b border-[#E8ECE7] pb-3">
          <h3 className="font-bold text-[#263329] text-base">AtmosAI Environmental Suite</h3>
          <button
            onClick={onClose}
            className="p-2 rounded-full bg-[#F5F7F4] text-[#788278] hover:text-[#263329] hover:bg-[#E8ECE7] transition cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* User Profile Card */}
        <div 
          onClick={() => {
            onClose();
            onOpenProfile();
          }}
          className="mt-4 p-4 rounded-2xl bg-gradient-to-r from-[#F1F8ED] via-[#F5F7F4] to-white border border-[#C2EBBA] flex items-center justify-between cursor-pointer atmos-card-interactive"
        >
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-[#C2EBBA] text-[#469A36] flex items-center justify-center">
              <User className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-[#788278] font-medium">Active Profile</p>
              <p className="text-sm font-bold text-[#263329] capitalize">{currentProfile.replace('_', ' ')}</p>
            </div>
          </div>
          <span className="text-xs font-semibold text-[#469A36] flex items-center space-x-1">
            <span>Change</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </span>
        </div>

        {/* Navigation Items */}
        <div className="space-y-2.5 py-4">
          {menuItems.map((item) => {
            const Icon = item.icon;
            return (
              <div
                key={item.id}
                onClick={() => {
                  onSelectTab(item.id);
                  onClose();
                }}
                className="p-3.5 rounded-xl bg-[#F5F7F4] hover:bg-[#F1F8ED] border border-[#E8ECE7] hover:border-[#C2EBBA] flex items-center justify-between cursor-pointer atmos-card-interactive"
              >
                <div className="flex items-center space-x-3">
                  <div className={`p-2.5 rounded-xl ${item.bgColor} ${item.color}`}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-[#263329]">{item.title}</p>
                    <p className="text-[11px] text-[#788278]">{item.description}</p>
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-[#788278]" />
              </div>
            );
          })}
        </div>

        {/* Backend Status Footer */}
        <div className="pt-3 border-t border-[#E8ECE7] text-[11px] text-[#788278] flex items-center justify-between">
          <span className="flex items-center space-x-1.5">
            <Server className="w-3.5 h-3.5 text-[#469A36]" />
            <span>FastAPI Backend</span>
          </span>
          <span className="text-[#469A36] font-mono font-semibold">Online &bull; LightGBM v1.0</span>
        </div>
      </div>
    </div>
  );
}

