import React from 'react';
import { 
  Wind, 
  Map, 
  TrendingUp, 
  BrainCircuit, 
  Navigation as NavIcon, 
  Watch, 
  Bell, 
  User, 
  MapPin,
  Activity,
  Layers,
  ChevronDown,
  ShieldCheck,
  LogOut
} from 'lucide-react';

export default function Navigation({ 
  currentTab, 
  setCurrentTab, 
  locations, 
  selectedLocation, 
  onOpenLocationPicker,
  currentProfile, 
  onOpenProfileModal,
  onOpenMoreMenu,
  onLogout,
  backendConnected
}) {
  const currentLocObj = locations.find(l => l.name === selectedLocation) || locations[0];
  const locDisplayName = currentLocObj ? currentLocObj.display_name.split('(')[0].trim() : 'Bengaluru Central';

  const mobilePrimaryTabs = [
    { id: 'dashboard', label: 'Home', icon: Activity },
    { id: 'map', label: 'Map', icon: Map },
    { id: 'forecast', label: 'Forecast', icon: TrendingUp },
    { id: 'ai', label: 'AI Guide', icon: BrainCircuit }
  ];

  const desktopAllTabs = [
    { id: 'dashboard', label: 'Dashboard', icon: Activity },
    { id: 'map', label: 'Pollution Map', icon: Map },
    { id: 'forecast', label: 'Forecast Details', icon: TrendingUp },
    { id: 'accuracy', label: 'Trust & Accuracy', icon: ShieldCheck },
    { id: 'ai', label: 'AI Intelligence', icon: BrainCircuit },
    { id: 'travel', label: 'Travel Intelligence', icon: NavIcon },
    { id: 'wear', label: 'AtmosAI Wear', icon: Watch },
    { id: 'alerts', label: 'Alerts', icon: Bell }
  ];

  return (
    <>
      {/* Top Mobile & Desktop App Bar */}
      <header className="border-b border-[#E8ECE7] bg-white/95 backdrop-blur-md sticky top-0 z-40 transition-all shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-14 sm:h-16">
            {/* Logo */}
            <div 
              className="flex items-center space-x-2.5 cursor-pointer" 
              onClick={() => setCurrentTab('dashboard')}
            >
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-[#64BC45] via-[#4AB746] to-[#469A36] p-[2px] shadow-sm">
                <div className="w-full h-full bg-white rounded-[9px] flex items-center justify-center">
                  <Wind className="w-4 h-4 text-[#64BC45]" />
                </div>
              </div>
              <div>
                <span className="font-extrabold text-lg tracking-tight text-[#263329]">
                  AtmosAI
                </span>
                <span className="hidden sm:inline-block ml-2 text-[10px] uppercase font-bold px-2 py-0.5 rounded-full bg-[#F1F8ED] text-[#469A36] border border-[#C2EBBA]">
                  Bengaluru
                </span>
              </div>
            </div>

            {/* Mobile Location Quick Switcher Pill & Profile Action */}
            <div className="flex items-center space-x-2 sm:space-x-3">
              {/* Location Selector Pill */}
              <button
                onClick={onOpenLocationPicker}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-full bg-white border border-[#E8ECE7] hover:border-[#64BC45] text-[#263329] text-xs font-semibold cursor-pointer atmos-card-interactive shadow-xs"
              >
                <MapPin className="w-3.5 h-3.5 text-[#64BC45] flex-shrink-0" />
                <span className="max-w-[120px] sm:max-w-none truncate">{locDisplayName}</span>
                <ChevronDown className="w-3 h-3 text-[#788278]" />
              </button>

              {/* Profile Pill */}
              <button
                onClick={onOpenProfileModal}
                className="flex items-center space-x-1.5 p-1.5 sm:px-3 sm:py-1.5 rounded-full bg-[#F1F8ED] border border-[#C2EBBA] hover:bg-[#C2EBBA]/30 text-[#469A36] text-xs font-medium cursor-pointer atmos-card-interactive"
                title="Change User Profile"
              >
                <User className="w-4 h-4 sm:w-3.5 sm:h-3.5" />
                <span className="capitalize hidden md:inline">{currentProfile.replace('_', ' ')}</span>
              </button>

              {/* Status Indicator */}
              <div 
                className={`w-2.5 h-2.5 rounded-full ${backendConnected ? 'bg-[#64BC45]' : 'bg-red-500 animate-pulse'}`} 
                title={backendConnected ? 'FastAPI Online' : 'Connecting to API...'}
              />

              {/* Logout Button */}
              {onLogout && (
                <button
                  type="button"
                  onClick={onLogout}
                  className="p-1.5 sm:px-2.5 sm:py-1.5 rounded-full text-[#788278] hover:text-red-600 hover:bg-red-50 border border-transparent hover:border-red-200 transition text-xs font-semibold cursor-pointer flex items-center space-x-1"
                  title="Sign Out"
                >
                  <LogOut className="w-4 h-4" />
                  <span className="hidden lg:inline text-[11px]">Sign Out</span>
                </button>
              )}
            </div>
          </div>

          {/* Desktop Sub-tabs (Hidden on Mobile) */}
          <div className="hidden sm:flex space-x-1 overflow-x-auto py-2 border-t border-[#E8ECE7] scrollbar-none">
            {desktopAllTabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = currentTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setCurrentTab(tab.id)}
                  className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition cursor-pointer ${
                    isActive
                      ? 'bg-[#F1F8ED] text-[#469A36] border border-[#C2EBBA] font-bold shadow-xs'
                      : 'text-[#788278] hover:text-[#263329] hover:bg-[#F5F7F4]'
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-[#469A36]' : 'text-[#788278]'}`} />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      </header>

      {/* Fixed Mobile Bottom Navigation Bar (Visible on Mobile only) */}
      <nav className="sm:hidden fixed bottom-0 left-0 right-0 z-40 mobile-bottom-nav">
        <div className="grid grid-cols-5 h-16 items-center px-1">
          {mobilePrimaryTabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = currentTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setCurrentTab(tab.id)}
                className={`flex flex-col items-center justify-center h-full space-y-1 transition-all cursor-pointer ${
                  isActive ? 'text-[#469A36] scale-105' : 'text-[#788278] hover:text-[#263329]'
                }`}
              >
                <div className={`p-1 rounded-xl transition ${isActive ? 'bg-[#F1F8ED]' : ''}`}>
                  <Icon className="w-5 h-5" />
                </div>
                <span className={`text-[10px] font-semibold tracking-tight ${isActive ? 'text-[#469A36]' : 'text-[#788278]'}`}>
                  {tab.label}
                </span>
              </button>
            );
          })}

          {/* 5th Button: More Suite Menu */}
          <button
            onClick={onOpenMoreMenu}
            className={`flex flex-col items-center justify-center h-full space-y-1 transition-all cursor-pointer ${
              ['travel', 'wear', 'alerts'].includes(currentTab) ? 'text-[#469A36] scale-105' : 'text-[#788278] hover:text-[#263329]'
            }`}
          >
            <div className={`p-1 rounded-xl transition ${['travel', 'wear', 'alerts'].includes(currentTab) ? 'bg-[#F1F8ED]' : ''}`}>
              <Layers className="w-5 h-5" />
            </div>
            <span className={`text-[10px] font-semibold tracking-tight ${['travel', 'wear', 'alerts'].includes(currentTab) ? 'text-[#469A36]' : 'text-[#788278]'}`}>
              More
            </span>
          </button>
        </div>
      </nav>
    </>
  );
}
