import React from 'react';
import { 
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine 
} from 'recharts';
import { 
  Wind, 
  Droplets, 
  Thermometer, 
  Gauge, 
  AlertTriangle, 
  ShieldCheck, 
  Clock, 
  Database, 
  ArrowUpRight, 
  Sparkles, 
  Footprints,
  Map,
  MapPin
} from 'lucide-react';

import ActivityPlannerWidget from './ActivityPlannerWidget';
import EnvironmentalAlertsWidget from './EnvironmentalAlertsWidget';
import LocalStationsWidget from './LocalStationsWidget';
import DataReliabilityCard from './DataReliabilityCard';
import DataFreshnessBadge from './DataFreshnessBadge';
import SavedPlacesWidget from './SavedPlacesWidget';
import PersonalizedAdvisorCard from './PersonalizedAdvisorCard';

export default function Dashboard({ 
  liveData, 
  forecastData, 
  adviceData, 
  userProfile,
  personalizationConfig,
  stations,
  savedLocations = [],
  selectedLocation,
  onSelectLocation,
  onOpenSavedPlacesModal,
  onRefreshSavedPlaces,
  onNavigate 
}) {
  if (!liveData) {
    return (
      <div className="flex flex-col items-center justify-center p-12 atmos-card">
        <Clock className="w-8 h-8 text-[#64BC45] animate-spin mb-3" />
        <p className="text-sm text-[#788278]">Loading live environmental telemetry...</p>
      </div>
    );
  }

  const aqi = liveData.aqi !== null ? liveData.aqi : 25;
  const pm25 = liveData.pm25 !== null ? liveData.pm25 : '--';

  const getAQIColor = (val) => {
    if (val <= 50) return '#10b981'; // Good (Green)
    if (val <= 100) return '#06b6d4'; // Satisfactory (Cyan)
    if (val <= 200) return '#f59e0b'; // Moderate (Amber)
    if (val <= 300) return '#f97316'; // Poor (Orange)
    return '#ef4444'; // Very Poor / Severe (Red)
  };

  const aqiColor = getAQIColor(aqi);

  // Chart series
  const chartData = [];
  if (liveData.pm25 !== null) {
    chartData.push({
      time: 'Now',
      pm25: liveData.pm25
    });
  }

  if (forecastData && forecastData.forecast_points) {
    forecastData.forecast_points.forEach((pt) => {
      chartData.push({
        time: pt.target_time_label.split(' ')[0],
        pm25: pt.predicted_pm25,
        ci_lower: pt.confidence_lower,
        ci_upper: pt.confidence_upper
      });
    });
  }

  const activity = adviceData?.activity_guidance;
  const headline = personalizationConfig?.priority_headline || 'Atmospheric Intelligence & Multi-Horizon Trend';
  const defaultOrder = [
    'current_aqi',
    'data_reliability',
    'saved_places',
    'pm25_forecast',
    'weather',
    'ai_insight',
    'activity_planner',
    'pollution_map',
    'environmental_alerts',
    'local_stations'
  ];
  
  // Ensure data_reliability and saved_places are prominently positioned
  const rawOrder = personalizationConfig?.widget_order || defaultOrder;
  let order = [...rawOrder];
  if (!order.includes('data_reliability')) {
    order.splice(1, 0, 'data_reliability');
  }
  if (!order.includes('saved_places')) {
    order.splice(2, 0, 'saved_places');
  }

  const rawVisible = personalizationConfig?.visible_widgets || order;
  const visible = [...new Set([...rawVisible, 'data_reliability', 'saved_places'])];

  const relMeta = liveData?.reliability_metadata;

  // Reusable Widgets Dictionary
  const widgets = {
    // 1. Current Air Quality Widget
    current_aqi: (
      <div key="current_aqi" className="atmos-card p-5 sm:p-6 border border-[#E8ECE7] relative overflow-hidden bg-gradient-to-br from-white via-white to-[#F1F8ED] shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-xs font-bold uppercase text-[#788278] tracking-wider">
              Indian National AQI (CPCB)
            </span>
            <DataFreshnessBadge 
              freshnessStatus={relMeta?.freshness_status || (liveData.is_stale ? "STALE" : "FRESH")}
              sourceType={relMeta?.source_type || (liveData.measurement_type === "measured" ? "MEASURED" : "ESTIMATED")}
              ageMinutes={relMeta?.age_minutes}
            />
          </div>
          <span 
            className="text-xs font-extrabold px-3 py-1 rounded-full border shadow-2xs"
            style={{ backgroundColor: `${aqiColor}15`, borderColor: `${aqiColor}40`, color: aqiColor }}
          >
            {liveData.aqi_category || 'Satisfactory'}
          </span>
        </div>

        <div className="my-3 flex items-baseline justify-between">
          <div className="space-y-0.5">
            <div className="text-6xl sm:text-7xl font-black text-[#263329] font-mono tracking-tight leading-none">
              {liveData.aqi !== null ? liveData.aqi : '--'}
            </div>
            <p className="text-xs text-[#788278] pt-1">
              Health Risk: <strong className="text-[#263329] font-semibold">{liveData.risk_level || 'Low'}</strong>
            </p>
          </div>

          <div className="text-right space-y-0.5">
            <span className="text-[11px] text-[#788278] uppercase tracking-wider block">PM2.5 Ambient</span>
            <div className="text-3xl sm:text-4xl font-black text-[#469A36] font-mono">
              {pm25}
            </div>
            <span className="text-[11px] text-[#788278]">µg/m³ &bull; Fine Dust</span>
          </div>
        </div>

        {/* Quick Action Guidance Pills */}
        {activity && (
          <div className="grid grid-cols-2 gap-3 pt-3 border-t border-[#E8ECE7]">
            <div className="p-3 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7] space-y-1">
              <div className="flex items-center space-x-1.5 text-[#469A36]">
                <Footprints className="w-3.5 h-3.5" />
                <span className="text-[11px] font-bold">Exercise Window</span>
              </div>
              <p className="text-xs font-extrabold text-[#263329]">
                {activity.outdoor_exercise_allowed ? 'Permissible' : 'Limit Exertion'}
              </p>
              <p className="text-[10px] text-[#788278] truncate">{activity.best_time_window}</p>
            </div>

            <div className="p-3 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7] space-y-1">
              <div className="flex items-center space-x-1.5 text-[#64BC45]">
                <ShieldCheck className="w-3.5 h-3.5" />
                <span className="text-[11px] font-bold">Protection Mask</span>
              </div>
              <p className="text-xs font-extrabold text-[#263329] truncate">
                {activity.mask_recommendation.includes('N95') ? 'N95 Advised' : 'Optional'}
              </p>
              <p className="text-[10px] text-[#788278] truncate">{activity.mask_recommendation}</p>
            </div>
          </div>
        )}
      </div>
    ),

    // 1b. Data Freshness and Reliability Transparency Card
    data_reliability: (
      <DataReliabilityCard 
        key="data_reliability" 
        liveData={liveData} 
        metadata={liveData.reliability_metadata} 
      />
    ),

    // 1c. Saved Places Intelligence Widget
    saved_places: (
      <SavedPlacesWidget
        key="saved_places"
        savedLocations={savedLocations}
        selectedLocation={selectedLocation}
        onSelectLocation={(loc) => {
          if (onSelectLocation) {
            onSelectLocation(loc.location_name || loc.location_id);
          }
        }}
        onOpenManageModal={onOpenSavedPlacesModal}
        onRefresh={onRefreshSavedPlaces}
      />
    ),

    // 2. PM2.5 Forecast Widget
    pm25_forecast: (
      <div key="pm25_forecast" className="atmos-card p-4 sm:p-6 border border-[#E8ECE7] bg-white space-y-3 shadow-xs">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-[#263329] flex items-center space-x-1.5">
              <span>PM2.5 Trend (Next 3–6 Hours)</span>
            </h3>
            <p className="text-[11px] text-[#788278]">LightGBM Machine Learning Forecast</p>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => onNavigate('accuracy')}
              className="text-[10px] font-semibold text-[#469A36] bg-[#F1F8ED] hover:bg-[#C2EBBA] border border-[#C2EBBA] px-2.5 py-1 rounded-full flex items-center space-x-1 cursor-pointer transition-colors"
              title="View genuine out-of-sample accuracy metrics & actual vs predicted chart"
            >
              <span>Accuracy Stats</span>
              <ArrowUpRight className="w-2.5 h-2.5" />
            </button>
            <button
              onClick={() => onNavigate('forecast')}
              className="text-[11px] font-semibold text-[#469A36] flex items-center space-x-1 cursor-pointer hover:underline"
            >
              <span>Full Curve</span>
              <ArrowUpRight className="w-3 h-3" />
            </button>
          </div>
        </div>

        <div className="h-52 w-full pt-2">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="mobileForecastFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#64BC45" stopOpacity={0.35}/>
                  <stop offset="95%" stopColor="#64BC45" stopOpacity={0.0}/>
                </linearGradient>
              </defs>
              <XAxis dataKey="time" stroke="#788278" tick={{ fontSize: 10 }} />
              <YAxis stroke="#788278" tick={{ fontSize: 10 }} unit="µg" />
              <Tooltip 
                contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#E8ECE7', borderRadius: '0.75rem', color: '#263329', fontSize: '11px', boxShadow: '0 4px 12px rgba(38, 51, 41, 0.08)' }}
                formatter={(val) => [`${val} µg/m³`, 'PM2.5']}
              />
              <ReferenceLine y={30} stroke="#64BC45" strokeDasharray="3 3" />
              <Area type="monotone" dataKey="pm25" stroke="#469A36" strokeWidth={2.5} fillOpacity={1} fill="url(#mobileForecastFill)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    ),

    // 3. Weather Widget
    weather: (
      <div key="weather" className="atmos-card p-4 sm:p-5 border border-[#E8ECE7] bg-white space-y-3 shadow-xs">
        <h3 className="text-xs font-bold uppercase tracking-wider text-[#788278]">
          Surface Meteorological Conditions
        </h3>
        <div className="grid grid-cols-4 gap-2 text-center">
          <div className="p-2.5 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7]">
            <Thermometer className="w-4 h-4 text-[#469A36] mx-auto mb-1" />
            <p className="text-[10px] text-[#788278]">Temp</p>
            <p className="text-xs font-bold text-[#263329] font-mono">
              {liveData.weather?.temperature_c !== undefined ? `${liveData.weather.temperature_c}°C` : '--'}
            </p>
          </div>

          <div className="p-2.5 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7]">
            <Droplets className="w-4 h-4 text-[#64BC45] mx-auto mb-1" />
            <p className="text-[10px] text-[#788278]">Humidity</p>
            <p className="text-xs font-bold text-[#263329] font-mono">
              {liveData.weather?.relative_humidity_pct !== undefined ? `${liveData.weather.relative_humidity_pct}%` : '--'}
            </p>
          </div>

          <div className="p-2.5 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7]">
            <Wind className="w-4 h-4 text-[#469A36] mx-auto mb-1" />
            <p className="text-[10px] text-[#788278]">Wind</p>
            <p className="text-xs font-bold text-[#263329] font-mono">
              {liveData.weather?.wind_speed_kmh !== undefined ? `${liveData.weather.wind_speed_kmh} km/h` : '--'}
            </p>
          </div>

          <div className="p-2.5 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7]">
            <Gauge className="w-4 h-4 text-[#7FC441] mx-auto mb-1" />
            <p className="text-[10px] text-[#788278]">Pressure</p>
            <p className="text-xs font-bold text-[#263329] font-mono">
              {liveData.weather?.surface_pressure_hpa !== undefined ? `${Math.round(liveData.weather.surface_pressure_hpa)} hPa` : '--'}
            </p>
          </div>
        </div>
      </div>
    ),

    // 4. AI Insight Widget (Personalized Advisor Card)
    ai_insight: adviceData && (
      <PersonalizedAdvisorCard
        key="ai_insight"
        adviceData={adviceData}
        userProfile={userProfile}
        onNavigate={onNavigate}
      />
    ),

    // 5. Activity Planner Widget
    activity_planner: (
      <ActivityPlannerWidget
        key="activity_planner"
        location={selectedLocation}
        userProfile={userProfile}
        onNavigate={onNavigate}
      />
    ),

    // 6. Pollution Map Widget
    pollution_map: (
      <div 
        key="pollution_map"
        onClick={() => onNavigate('map')}
        className="atmos-card p-4 sm:p-5 border border-[#E8ECE7] bg-white space-y-3 cursor-pointer hover:border-[#64BC45] transition shadow-xs"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="p-1.5 rounded-lg bg-[#F1F8ED] text-[#469A36]">
              <Map className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-[#263329]">Z Pollution Map</h3>
              <p className="text-[10px] text-[#788278]">7 Connected Ground & Atmospheric Stations</p>
            </div>
          </div>
          <ArrowUpRight className="w-4 h-4 text-[#64BC45]" />
        </div>

        <div className="p-4 rounded-xl bg-[#F1F8ED] border border-[#C2EBBA] text-center flex items-center justify-center space-x-2 text-xs text-[#469A36] font-semibold">
          <MapPin className="w-4 h-4 text-[#64BC45]" />
          <span>Tap to explore interactive spatial heatmap across Bengaluru</span>
        </div>
      </div>
    ),

    // 7. Environmental Alerts Widget
    environmental_alerts: (
      <EnvironmentalAlertsWidget
        key="environmental_alerts"
        userProfile={userProfile}
        onNavigate={onNavigate}
      />
    ),

    // 8. Local Monitoring Stations Widget
    local_stations: (
      <LocalStationsWidget
        key="local_stations"
        stations={stations}
        selectedLocation={selectedLocation}
        onSelectLocation={onSelectLocation}
      />
    )
  };

  return (
    <div className="space-y-4 sm:space-y-6 pb-20 sm:pb-0">
      {/* Dynamic Subheader with Active Persona Headline */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 px-1">
        <div>
          <span className="text-[11px] text-[#469A36] font-bold tracking-wider uppercase block">
            {headline}
          </span>
          <h2 className="text-lg sm:text-2xl font-black text-[#263329] leading-tight">
            {liveData.display_name}
          </h2>
        </div>

        <div className="flex flex-wrap items-center gap-1.5 sm:space-x-2">
          <DataFreshnessBadge 
            freshnessStatus={relMeta?.freshness_status || (liveData.is_stale ? "STALE" : "FRESH")}
            sourceType={relMeta?.source_type || (liveData.measurement_type === 'measured' ? 'MEASURED' : 'ESTIMATED')}
            ageMinutes={relMeta?.age_minutes}
          />

          <span className="text-[10px] font-bold uppercase px-2.5 py-1 rounded-md border bg-[#F1F8ED] border-[#C2EBBA] text-[#469A36]">
            {userProfile?.user_category?.replace('_', ' ') || 'General Public'}
          </span>
        </div>
      </div>

      {/* Surge Warning Alert (if flagged by ML) */}
      {forecastData && forecastData.surge_detected && (
        <div className="p-3.5 rounded-2xl bg-amber-50 border border-amber-300 text-amber-900 flex items-start space-x-3 shadow-xs">
          <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5 animate-pulse" />
          <div className="space-y-0.5">
            <h4 className="font-bold text-xs text-amber-900">Pollution Surge Advisory (LightGBM)</h4>
            <p className="text-[11px] text-amber-800 leading-tight">
              Model projects PM2.5 rise over the next 3–6 hours. Conclude strenuous outdoor sessions early.
            </p>
          </div>
        </div>
      )}

      {/* Dynamic Widget Ordering Execution */}
      <div className="space-y-4 sm:space-y-6">
        {order
          .filter(widgetKey => visible.includes(widgetKey))
          .map(widgetKey => widgets[widgetKey])
          .filter(Boolean)}
      </div>
    </div>
  );
}
