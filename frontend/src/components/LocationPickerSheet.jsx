import React from 'react';
import { X, MapPin, Check, Navigation, Star, Plus, Home, Briefcase, GraduationCap } from 'lucide-react';

export default function LocationPickerSheet({ 
  isOpen, 
  onClose, 
  locations = [], 
  savedLocations = [],
  selectedLocation, 
  onSelectLocation,
  onOpenManagePlaces 
}) {
  if (!isOpen) return null;

  const getLocationIcon = (type) => {
    switch (type) {
      case 'home':
        return Home;
      case 'office':
        return Briefcase;
      case 'college_school':
        return GraduationCap;
      case 'favourite_place':
        return Star;
      default:
        return MapPin;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/50 backdrop-blur-xs p-0 sm:p-4">
      {/* Backdrop tap dismiss */}
      <div className="fixed inset-0" onClick={onClose} />

      <div className="relative w-full max-w-md atmos-card rounded-t-3xl sm:rounded-2xl p-6 border-t sm:border border-[#E8ECE7] shadow-xl animate-sheet-up max-h-[85vh] flex flex-col z-10 bg-white">
        {/* Grab handle for mobile touch */}
        <div className="w-12 h-1.5 rounded-full bg-[#E8ECE7] mx-auto -mt-2 mb-4 sm:hidden" />

        <div className="flex items-center justify-between border-b border-[#E8ECE7] pb-3">
          <div className="flex items-center space-x-2">
            <div className="p-2 rounded-xl bg-[#F1F8ED] text-[#469A36]">
              <MapPin className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-[#263329] text-base">Select Monitored Location</h3>
              <p className="text-xs text-[#788278]">Saved Places & Regional Stations</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-full bg-[#F5F7F4] text-[#788278] hover:text-[#263329] hover:bg-[#E8ECE7] transition cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto space-y-4 py-4 pr-1">
          {/* Saved Places Section */}
          {savedLocations && savedLocations.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center justify-between px-1">
                <span className="text-[11px] font-bold uppercase tracking-wider text-[#469A36]">
                  Your Saved Places
                </span>
                {onOpenManagePlaces && (
                  <button
                    onClick={() => {
                      onClose();
                      onOpenManagePlaces();
                    }}
                    className="text-[11px] font-semibold text-[#788278] hover:text-[#469A36] flex items-center space-x-1 cursor-pointer"
                  >
                    <Plus className="w-3 h-3" />
                    <span>Manage</span>
                  </button>
                )}
              </div>

              <div className="space-y-1.5">
                {savedLocations.map((loc) => {
                  const Icon = getLocationIcon(loc.location_type);
                  const isSelected = selectedLocation === loc.location_name || selectedLocation === loc.location_id;
                  const aq = loc.air_quality;

                  return (
                    <div
                      key={loc.location_id}
                      onClick={() => {
                        onSelectLocation(loc.location_name);
                        onClose();
                      }}
                      className={`p-3 rounded-xl border flex items-center justify-between transition cursor-pointer ${
                        isSelected
                          ? 'bg-[#F1F8ED] border-[#64BC45] shadow-xs'
                          : 'bg-white border-[#E8ECE7] hover:border-[#C2EBBA]'
                      }`}
                    >
                      <div className="flex items-center space-x-2.5 min-w-0">
                        <div className={`p-1.5 rounded-lg ${isSelected ? 'bg-[#C2EBBA] text-[#469A36]' : 'bg-[#F5F7F4] text-[#788278]'}`}>
                          <Icon className="w-4 h-4" />
                        </div>
                        <div className="space-y-0.5 min-w-0">
                          <div className="flex items-center space-x-1.5">
                            <p className={`text-xs font-bold truncate ${isSelected ? 'text-[#469A36]' : 'text-[#263329]'}`}>
                              {loc.location_name}
                            </p>
                            {loc.is_primary && (
                              <span className="text-[9px] font-extrabold uppercase px-1.5 py-0.2 rounded bg-[#F1F8ED] text-[#469A36] border border-[#C2EBBA]">
                                Primary
                              </span>
                            )}
                          </div>
                          <p className="text-[10px] text-[#788278] truncate">
                            {aq?.pm25 ? `PM2.5: ${aq.pm25} µg/m³ • ${aq.nearest_station?.distance_km} km to station` : loc.address}
                          </p>
                        </div>
                      </div>

                      {isSelected && (
                        <div className="w-5 h-5 rounded-full bg-[#64BC45] text-white flex items-center justify-center flex-shrink-0">
                          <Check className="w-3.5 h-3.5 stroke-[3]" />
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Regional Monitoring Stations Section */}
          <div className="space-y-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#788278] px-1 block">
              Bengaluru Monitoring Stations ({locations.length})
            </span>

            <div className="space-y-1.5">
              {locations.map((loc) => {
                const isSelected = loc.name === selectedLocation;

                return (
                  <div
                    key={loc.name}
                    onClick={() => {
                      onSelectLocation(loc.name);
                      onClose();
                    }}
                    className={`p-3 rounded-xl border flex items-center justify-between transition cursor-pointer ${
                      isSelected
                        ? 'bg-[#F1F8ED] border-[#64BC45] shadow-xs'
                        : 'bg-white border-[#E8ECE7] hover:border-[#C2EBBA]'
                    }`}
                  >
                    <div className="space-y-0.5 min-w-0">
                      <p className={`text-xs font-semibold truncate ${isSelected ? 'text-[#469A36]' : 'text-[#263329]'}`}>
                        {loc.display_name}
                      </p>
                      <p className="text-[10px] text-[#788278] font-mono">
                        Station Code: {loc.station_code || loc.name}
                      </p>
                    </div>

                    {isSelected && (
                      <div className="w-5 h-5 rounded-full bg-[#64BC45] text-white flex items-center justify-center flex-shrink-0">
                        <Check className="w-3.5 h-3.5 stroke-[3]" />
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        <div className="pt-3 border-t border-[#E8ECE7] text-center text-xs text-[#788278]">
          AtmosAI provides real-time atmospheric readings across all locations.
        </div>
      </div>
    </div>
  );
}
