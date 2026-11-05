import React from 'react';
import { MapPin, ArrowRight } from 'lucide-react';

export default function LocalStationsWidget({ stations, selectedLocation, onSelectLocation }) {
  const getAQIColor = (val) => {
    if (!val || val <= 50) return '#10b981';
    if (val <= 100) return '#06b6d4';
    if (val <= 200) return '#f59e0b';
    if (val <= 300) return '#f97316';
    return '#ef4444';
  };

  return (
    <div className="atmos-card p-4 sm:p-5 border border-[#E8ECE7] bg-white space-y-3 shadow-xs">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="p-1.5 rounded-lg bg-[#F1F8ED] text-[#469A36]">
            <MapPin className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-[#263329]">Local Monitoring Stations</h3>
            <p className="text-[10px] text-[#788278]">Bengaluru Ground Sensors & CAMS</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1">
        {stations && stations.length > 0 ? (
          stations.map((st) => {
            const isSelected = selectedLocation === st.name;
            const aqiVal = st.aqi || 35;
            const aqiCol = getAQIColor(aqiVal);

            return (
              <button
                key={st.name}
                onClick={() => onSelectLocation(st.name)}
                className={`p-2.5 rounded-xl border text-left transition cursor-pointer flex flex-col justify-between ${
                  isSelected 
                    ? 'bg-[#F1F8ED] border-[#64BC45] text-[#263329] shadow-xs'
                    : 'bg-[#F5F7F4] border-[#E8ECE7] hover:border-[#C2EBBA] text-[#263329]'
                }`}
              >
                <div className="flex items-center justify-between w-full">
                  <span className="text-[11px] font-bold truncate max-w-[80px]">
                    {st.display_name?.replace('Bengaluru ', '') || st.name}
                  </span>
                  <span 
                    className="w-2 h-2 rounded-full" 
                    style={{ backgroundColor: aqiCol }} 
                  />
                </div>
                
                <div className="mt-1 flex items-baseline justify-between w-full">
                  <span className="text-sm font-mono font-black" style={{ color: aqiCol }}>
                    {aqiVal}
                  </span>
                  <span className="text-[9px] text-[#788278]">AQI</span>
                </div>
              </button>
            );
          })
        ) : (
          <div className="col-span-full text-xs text-[#788278] text-center py-2">
            Loading monitoring stations...
          </div>
        )}
      </div>
    </div>
  );
}

