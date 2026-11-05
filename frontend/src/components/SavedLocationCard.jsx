import React from 'react';
import { 
  Home, 
  GraduationCap, 
  Briefcase, 
  Star, 
  MapPin, 
  Radio, 
  Clock, 
  Trash2, 
  Edit3, 
  CheckCircle, 
  Navigation,
  AlertCircle,
  TrendingUp,
  ShieldCheck,
  MoreVertical
} from 'lucide-react';

/**
 * Reusable Saved Location Card
 * Displays environmental telemetry, nearest station distance, freshness, and switch action.
 */
export default function SavedLocationCard({ 
  location, 
  isActive = false, 
  onSelect, 
  onEdit, 
  onDelete,
  onSetPrimary
}) {
  const aq = location.air_quality;
  const isPrimary = location.is_primary;

  const getLocationIcon = (type) => {
    switch (type) {
      case 'home':
        return Home;
      case 'college_school':
        return GraduationCap;
      case 'office':
        return Briefcase;
      case 'favourite_place':
        return Star;
      case 'custom':
      default:
        return MapPin;
    }
  };

  const getTypeLabel = (type) => {
    switch (type) {
      case 'home':
        return 'HOME';
      case 'college_school':
        return 'COLLEGE / SCHOOL';
      case 'office':
        return 'OFFICE';
      case 'favourite_place':
        return 'FAVOURITE PLACE';
      case 'custom':
      default:
        return 'SAVED PLACE';
    }
  };

  const getAQIColor = (val) => {
    if (val === null || val === undefined) return '#94a3b8';
    if (val <= 50) return '#10b981';
    if (val <= 100) return '#06b6d4';
    if (val <= 200) return '#f59e0b';
    if (val <= 300) return '#f97316';
    return '#ef4444';
  };

  const getFreshnessBadge = (status) => {
    const s = (status || 'UNAVAILABLE').toUpperCase();
    switch (s) {
      case 'FRESH':
        return { label: 'Fresh', bg: 'bg-[#F1F8ED] text-[#469A36] border-[#C2EBBA]' };
      case 'AGING':
        return { label: 'Aging', bg: 'bg-amber-50 text-amber-700 border-amber-200' };
      case 'STALE':
        return { label: 'STALE', bg: 'bg-red-50 text-red-700 border-red-200 animate-pulse' };
      case 'UNAVAILABLE':
      default:
        return { label: 'Unavailable', bg: 'bg-[#F5F7F4] text-[#788278] border-[#E8ECE7]' };
    }
  };

  const Icon = getLocationIcon(location.location_type);
  const typeLabel = getTypeLabel(location.location_type);
  const freshness = getFreshnessBadge(aq?.freshness_status);
  const aqiColor = getAQIColor(aq?.aqi);

  const formatTime = (ts) => {
    if (!ts) return 'Awaiting telemetry';
    try {
      const dt = new Date(ts);
      return dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return String(ts);
    }
  };

  const hasData = aq && aq.pm25 !== null && aq.pm25 !== undefined;

  return (
    <div 
      className={`atmos-card p-4 sm:p-5 border transition-all relative flex flex-col justify-between ${
        isActive 
          ? 'border-[#64BC45] bg-[#F1F8ED]/70 shadow-sm' 
          : 'border-[#E8ECE7] hover:border-[#C2EBBA] bg-white'
      }`}
    >
      {/* Header */}
      <div>
        <div className="flex items-center justify-between gap-2 pb-2">
          <div className="flex items-center space-x-2">
            <div className={`p-1.5 rounded-lg ${isActive ? 'bg-[#C2EBBA] text-[#469A36]' : 'bg-[#F5F7F4] text-[#788278]'}`}>
              <Icon className="w-4 h-4" />
            </div>
            <div>
              <span className="text-[10px] font-black uppercase tracking-wider text-[#469A36] block font-mono">
                {typeLabel}
              </span>
              <h4 className="text-sm font-bold text-[#263329] leading-tight line-clamp-1">
                {location.location_name}
              </h4>
            </div>
          </div>

          <div className="flex items-center space-x-1">
            {isPrimary && (
              <span className="text-[9px] font-extrabold uppercase px-2 py-0.5 rounded-full bg-[#F1F8ED] text-[#469A36] border border-[#C2EBBA]">
                Primary
              </span>
            )}

            <button
              onClick={() => onEdit && onEdit(location)}
              className="p-1.5 rounded-lg text-[#788278] hover:text-[#263329] hover:bg-[#F5F7F4] transition cursor-pointer"
              title="Edit Place Details"
            >
              <Edit3 className="w-3.5 h-3.5" />
            </button>

            <button
              onClick={() => onDelete && onDelete(location.location_id)}
              className="p-1.5 rounded-lg text-[#788278] hover:text-red-500 hover:bg-[#F5F7F4] transition cursor-pointer"
              title="Delete Place"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {location.address && (
          <p className="text-[11px] text-[#788278] line-clamp-1 pt-0.5 flex items-center space-x-1">
            <MapPin className="w-3 h-3 flex-shrink-0 text-[#788278]" />
            <span>{location.address}</span>
          </p>
        )}

        {/* Environmental Telemetry Display */}
        {hasData ? (
          <div className="my-3 p-3 rounded-xl bg-white border border-[#E8ECE7] space-y-2 shadow-2xs">
            <div className="flex items-baseline justify-between">
              <div>
                <span className="text-[10px] text-[#788278] uppercase font-mono block">PM2.5 Ambient</span>
                <div className="flex items-baseline space-x-1">
                  <span className="text-2xl font-black font-mono text-[#263329]">
                    {aq.pm25}
                  </span>
                  <span className="text-xs text-[#788278]">µg/m³</span>
                </div>
              </div>

              {aq.aqi !== null && aq.aqi !== undefined && (
                <div className="text-right">
                  <span className="text-[10px] text-[#788278] uppercase font-mono block">CPCB AQI</span>
                  <span 
                    className="text-xs font-extrabold px-2 py-0.5 rounded-md border"
                    style={{ backgroundColor: `${aqiColor}15`, borderColor: `${aqiColor}40`, color: aqiColor }}
                  >
                    {aq.aqi} &bull; {aq.aqi_category || 'Moderate'}
                  </span>
                </div>
              )}
            </div>

            {/* Nearest Monitoring Station & Distance */}
            <div className="pt-2 border-t border-[#E8ECE7] space-y-1 text-[11px]">
              <div className="flex items-center justify-between text-[#263329]">
                <span className="text-[#788278] flex items-center space-x-1">
                  <Radio className="w-3 h-3 text-[#469A36] flex-shrink-0" />
                  <span>Station:</span>
                </span>
                <span className="font-semibold text-right truncate max-w-[170px]" title={aq.nearest_station?.station_name}>
                  {aq.nearest_station?.station_name?.split('(')[0] || 'Regional Station'}
                </span>
              </div>

              <div className="flex items-center justify-between text-[#263329]">
                <span className="text-[#788278]">Distance:</span>
                <span className="font-mono text-[#469A36] font-bold">
                  {aq.nearest_station?.distance_km} km away
                </span>
              </div>

              <div className="flex items-center justify-between text-[#263329]">
                <span className="text-[#788278]">Updated:</span>
                <span className="font-mono text-[#788278] flex items-center space-x-1">
                  <Clock className="w-2.5 h-2.5 text-[#788278]" />
                  <span>{formatTime(aq.observed_at)}</span>
                  {aq.age_minutes && <span className="text-[10px] text-[#788278]">({Math.round(aq.age_minutes)}m ago)</span>}
                </span>
              </div>

              <div className="flex items-center justify-between pt-1">
                <span className="text-[#788278]">Status:</span>
                <span className={`text-[9px] font-extrabold uppercase px-2 py-0.5 rounded border ${freshness.bg}`}>
                  {freshness.label}
                </span>
              </div>
            </div>

            {/* Forecast Trend Preview */}
            {aq.predicted_pm25_3h && (
              <div className="pt-1 text-[10px] text-[#788278] flex items-center space-x-1">
                <TrendingUp className="w-3 h-3 text-[#469A36] flex-shrink-0" />
                <span className="truncate">{aq.forecast_summary}</span>
              </div>
            )}
          </div>
        ) : (
          <div className="my-3 p-3 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7] space-y-2 text-xs">
            <div className="flex items-start space-x-2 text-[#263329]">
              <AlertCircle className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-bold text-[#263329]">PM2.5: Unavailable</p>
                <p className="text-[11px] text-[#788278]">Status: No nearby measurement available</p>
              </div>
            </div>
            <p className="text-[10px] text-[#788278] italic">
              External ground stations could not report telemetry. Zero synthetic values fabricated.
            </p>
          </div>
        )}
      </div>

      {/* Card Footer Actions */}
      <div className="flex items-center justify-between gap-2 pt-2 border-t border-[#E8ECE7]">
        <button
          onClick={() => onSelect && onSelect(location)}
          className={`flex-1 py-1.5 px-3 rounded-xl text-xs font-bold transition flex items-center justify-center space-x-1.5 cursor-pointer ${
            isActive
              ? 'bg-[#64BC45] text-white shadow-xs'
              : 'bg-[#F1F8ED] hover:bg-[#C2EBBA] text-[#469A36] border border-[#C2EBBA]'
          }`}
        >
          <Navigation className="w-3.5 h-3.5" />
          <span>{isActive ? 'Active on Dashboard' : 'Monitor Here'}</span>
        </button>

        {!isPrimary && onSetPrimary && (
          <button
            onClick={() => onSetPrimary(location.location_id)}
            className="p-1.5 rounded-xl border border-[#E8ECE7] bg-[#F5F7F4] hover:bg-[#F1F8ED] text-[#788278] hover:text-[#469A36] text-xs transition cursor-pointer"
            title="Make this your default primary location"
          >
            <Star className="w-3.5 h-3.5" />
          </button>
        )}
      </div>
    </div>
  );
}

