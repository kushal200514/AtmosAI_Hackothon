import React, { useState } from 'react';
import { MapPin, Plus, Navigation, Sparkles, RefreshCw } from 'lucide-react';
import SavedLocationCard from './SavedLocationCard';

/**
 * Saved Places Widget for AtmosAI Dashboard
 * Displays Home, College/School, Office, and Custom Places with live air quality.
 */
export default function SavedPlacesWidget({
  savedLocations = [],
  selectedLocation,
  onSelectLocation,
  onOpenManageModal,
  onRefresh
}) {
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = async () => {
    if (!onRefresh) return;
    setIsRefreshing(true);
    try {
      await onRefresh();
    } finally {
      setIsRefreshing(false);
    }
  };

  return (
    <div className="atmos-card p-4 sm:p-6 border border-[#E8ECE7] bg-white space-y-4 shadow-xs">
      {/* Widget Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#E8ECE7] pb-3">
        <div className="space-y-0.5">
          <div className="flex items-center space-x-2">
            <div className="p-1.5 rounded-lg bg-[#F1F8ED] text-[#469A36]">
              <MapPin className="w-4 h-4" />
            </div>
            <h3 className="text-sm sm:text-base font-bold text-[#263329] tracking-tight">
              Saved Places Intelligence
            </h3>
            <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-full bg-[#F1F8ED] border border-[#C2EBBA] text-[#469A36] font-bold">
              {savedLocations.length} Monitored
            </span>
          </div>
          <p className="text-xs text-[#788278]">
            Monitor air quality, nearest station proximity, and freshness across your key places
          </p>
        </div>

        <div className="flex items-center space-x-2">
          {onRefresh && (
            <button
              onClick={handleRefresh}
              disabled={isRefreshing}
              className="p-1.5 rounded-lg bg-[#F5F7F4] border border-[#E8ECE7] text-[#263329] hover:bg-[#F1F8ED] transition cursor-pointer disabled:opacity-50"
              title="Refresh Telemetry"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-[#64BC45]' : 'text-[#788278]'}`} />
            </button>
          )}

          <button
            onClick={onOpenManageModal}
            className="text-xs font-bold text-white bg-[#64BC45] hover:bg-[#469A36] px-3 py-1.5 rounded-xl flex items-center space-x-1.5 transition cursor-pointer shadow-xs"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Manage Places</span>
          </button>
        </div>
      </div>

      {/* Places Cards Grid */}
      {savedLocations.length === 0 ? (
        <div className="text-center py-8 rounded-2xl bg-[#F5F7F4] border border-[#E8ECE7] p-6 space-y-3">
          <MapPin className="w-8 h-8 text-[#788278] mx-auto" />
          <div className="space-y-1">
            <h4 className="text-sm font-bold text-[#263329]">No Saved Locations Yet</h4>
            <p className="text-xs text-[#788278] max-w-sm mx-auto">
              Add your Home, College, Office, or Favourite places to monitor localized pollution and receive tailored alerts.
            </p>
          </div>
          <button
            onClick={onOpenManageModal}
            className="px-4 py-2 rounded-xl bg-[#64BC45] hover:bg-[#469A36] text-white font-bold text-xs shadow-sm cursor-pointer"
          >
            + Add Your First Place
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
          {savedLocations.map((loc) => {
            const isActive = selectedLocation === loc.location_name || selectedLocation === loc.location_id;
            return (
              <SavedLocationCard
                key={loc.location_id}
                location={loc}
                isActive={isActive}
                onSelect={() => onSelectLocation && onSelectLocation(loc)}
                onEdit={() => onOpenManageModal && onOpenManageModal(loc)}
              />
            );
          })}
        </div>
      )}

      {/* Transparency Note */}
      <div className="text-[11px] text-[#788278] italic pt-1 flex items-center justify-between">
        <span>* Nearest station distance is explicitly reported. Ground stations may differ from microclimates.</span>
        <span className="font-mono text-[10px] text-[#788278]">Zero Synthetic Fabrication</span>
      </div>
    </div>
  );
}

