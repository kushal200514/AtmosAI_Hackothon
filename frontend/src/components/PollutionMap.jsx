import React, { useState, useEffect } from 'react';
import { 
  MapContainer, 
  TileLayer, 
  CircleMarker, 
  Popup, 
  Polyline, 
  Rectangle, 
  Tooltip, 
  useMap,
  useMapEvents
} from 'react-leaflet';
import { 
  MapPin, 
  Navigation, 
  Car, 
  Bike, 
  Footprints, 
  ArrowLeftRight, 
  ShieldCheck, 
  AlertTriangle, 
  Database, 
  Layers, 
  Clock, 
  Info, 
  Wind, 
  Thermometer, 
  Activity,
  CheckCircle2,
  Compass,
  ArrowRight,
  Star,
  Home,
  Briefcase,
  GraduationCap,
  Plus
} from 'lucide-react';
import { 
  fetchMapGrid, 
  fetchMapStationMarkers, 
  fetchTravelRoutePollution 
} from '../services/api';

// Dynamic Map Bounds and View Controller
function MapViewController({ center, zoom, bounds }) {
  const map = useMap();
  useEffect(() => {
    if (bounds && bounds.length > 0) {
      try {
        map.fitBounds(bounds, { padding: [40, 40], maxZoom: 14 });
      } catch (err) {
        map.setView(center, zoom);
      }
    } else if (center) {
      map.setView(center, zoom);
    }
  }, [center, zoom, bounds, map]);
  return null;
}

function MapClickHandler({ onMapClick }) {
  useMapEvents({
    click: (e) => {
      if (onMapClick) onMapClick(e.latlng);
    }
  });
  return null;
}

export default function PollutionMap({ 
  stations = [], 
  locations = [], 
  savedLocations = [],
  selectedLocation = 'bengaluru_central', 
  onSelectLocation,
  onOpenAddLocationModal
}) {
  const defaultCenter = [12.9716, 77.5946]; // Central Bengaluru

  // Map display mode: 'route' (Travel Journey) or 'explore' (Metropolitan Stations & Grid)
  const [activeMode, setActiveMode] = useState('route');

  // Layer toggles
  const [showGridOverlay, setShowGridOverlay] = useState(true);
  const [showStations, setShowStations] = useState(true);
  const [showSavedPlaces, setShowSavedPlaces] = useState(true);
  const [mapClickPoint, setMapClickPoint] = useState(null);

  // Travel Routing State
  const [origin, setOrigin] = useState('yelahanka');
  const [destination, setDestination] = useState('silk_board');
  const [travelMode, setTravelMode] = useState('driving'); // 'driving', 'cycling', 'walking'
  const [routeData, setRouteData] = useState(null);
  const [routeLoading, setRouteLoading] = useState(false);
  const [routeError, setRouteError] = useState(null);

  // Atmospheric Grid & Station Markers State
  const [gridCells, setGridCells] = useState([]);
  const [stationMarkers, setStationMarkers] = useState([]);
  const [selectedSegmentId, setSelectedSegmentId] = useState(null);
  const [focusedStation, setFocusedStation] = useState(null);

  // Available locations for routing
  const availableLocations = locations.length > 0 
    ? locations 
    : [
        { name: 'yelahanka', display_name: 'Yelahanka (North Zone)' },
        { name: 'hebbal', display_name: 'Hebbal (Bellary Road)' },
        { name: 'bengaluru_central', display_name: 'Bengaluru Central (MG Road)' },
        { name: 'peenya', display_name: 'Peenya Industrial Area' },
        { name: 'whitefield', display_name: 'Whitefield (Tech Hub)' },
        { name: 'jayanagar', display_name: 'Jayanagar (South Zone)' },
        { name: 'silk_board', display_name: 'Central Silk Board (Hosur Road)' }
      ];

  // Initial load: Atmospheric Grid and Station Markers
  useEffect(() => {
    async function loadMapLayers() {
      try {
        const [grid, markers] = await Promise.all([
          fetchMapGrid().catch(() => []),
          fetchMapStationMarkers().catch(() => [])
        ]);
        if (grid && grid.length > 0) setGridCells(grid);
        if (markers && markers.length > 0) setStationMarkers(markers);
      } catch (err) {
        console.error('Failed to load initial map telemetry:', err);
      }
    }
    loadMapLayers();
  }, []);

  // Recalculate route whenever origin, destination, or mode changes
  useEffect(() => {
    let isCancelled = false;

    async function loadRoute() {
      if (!origin || !destination) return;
      setRouteLoading(true);
      setRouteError(null);
      setSelectedSegmentId(null);
      try {
        const data = await fetchTravelRoutePollution(origin, destination, travelMode);
        if (!isCancelled) {
          setRouteData(data);
        }
      } catch (err) {
        if (!isCancelled) {
          console.error('Failed to load travel route pollution:', err);
          setRouteError('Could not calculate corridor pollution route. Please try another corridor.');
        }
      } finally {
        if (!isCancelled) setRouteLoading(false);
      }
    }

    loadRoute();
    return () => { isCancelled = true; };
  }, [origin, destination, travelMode]);

  // Swap origin and destination
  const handleSwapCorridor = () => {
    const prevOrigin = origin;
    setOrigin(destination);
    setDestination(prevOrigin);
  };

  // Helper: CPCB NAQI Color
  const getMarkerColor = (aqi, pm25) => {
    if (aqi !== null && aqi !== undefined) {
      if (aqi <= 50) return '#10b981'; // Green (Good)
      if (aqi <= 100) return '#06b6d4'; // Cyan (Satisfactory)
      if (aqi <= 200) return '#f59e0b'; // Amber (Moderate)
      if (aqi <= 300) return '#f97316'; // Orange (Poor)
      if (aqi <= 400) return '#ef4444'; // Red (Very Poor)
      return '#7f1d1d'; // Maroon (Severe)
    }
    if (pm25 !== null && pm25 !== undefined) {
      if (pm25 <= 30) return '#10b981';
      if (pm25 <= 60) return '#06b6d4';
      if (pm25 <= 90) return '#f59e0b';
      if (pm25 <= 120) return '#f97316';
      return '#ef4444';
    }
    return '#64748b'; // Gray (Unavailable)
  };

  // Determine active map bounds
  const mapBounds = (activeMode === 'route' && routeData?.route_geometry?.length > 0)
    ? routeData.route_geometry
    : null;

  const currentStationList = stationMarkers.length > 0 ? stationMarkers : stations;

  return (
    <div className="space-y-6">
      {/* Top Header & Navigation Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-gradient-to-r from-[#F1F8ED] via-white to-[#F1F8ED] border border-[#C2EBBA] shadow-xs">
        <div>
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-lg bg-[#C2EBBA] flex items-center justify-center text-[#469A36]">
              <Compass className="w-5 h-5" />
            </div>
            <h1 className="text-xl font-extrabold text-[#263329] tracking-tight">
              Real-Time Travel Pollution Map
            </h1>
            <span className="text-[10px] uppercase font-bold px-2.5 py-0.5 rounded-full bg-[#F1F8ED] text-[#469A36] border border-[#C2EBBA]">
              Bengaluru Geospatial
            </span>
          </div>
          <p className="text-xs text-[#788278] mt-1 max-w-2xl">
            Live atmospheric environmental monitoring along Bengaluru travel corridors.
            Strictly distinguishes physical CPCB ground measurements from atmospheric dispersion forecasts.
          </p>
        </div>

        {/* View Mode Switcher */}
        <div className="flex items-center space-x-1.5 bg-white p-1.5 rounded-xl border border-[#E8ECE7] shadow-xs">
          <button
            onClick={() => setActiveMode('route')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
              activeMode === 'route'
                ? 'bg-[#64BC45] text-white shadow-sm'
                : 'text-[#788278] hover:text-[#263329]'
            }`}
          >
            <Navigation className="w-3.5 h-3.5" />
            <span>Route Pollution</span>
          </button>
          <button
            onClick={() => setActiveMode('explore')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
              activeMode === 'explore'
                ? 'bg-[#64BC45] text-white shadow-sm'
                : 'text-[#788278] hover:text-[#263329]'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Stations & Grid</span>
          </button>
        </div>
      </div>

      {/* Layer Toggles & Map Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-xl bg-white border border-[#E8ECE7] text-xs text-[#263329] shadow-xs">
        <div className="flex flex-wrap items-center gap-4">
          <label className="flex items-center space-x-2 cursor-pointer select-none">
            <input 
              type="checkbox" 
              checked={showGridOverlay} 
              onChange={(e) => setShowGridOverlay(e.target.checked)}
              className="rounded border-[#E8ECE7] text-[#64BC45] focus:ring-0 focus:ring-offset-0 cursor-pointer accent-[#64BC45]"
            />
            <span className="font-semibold text-[#263329] flex items-center space-x-1">
              <span className="w-3 h-2 border border-dashed border-[#469A36] bg-[#C2EBBA]/50 rounded-xs inline-block" />
              <span>CAMS Atmospheric Forecast Grid</span>
            </span>
          </label>

          <label className="flex items-center space-x-2 cursor-pointer select-none">
            <input 
              type="checkbox" 
              checked={showStations} 
              onChange={(e) => setShowStations(e.target.checked)}
              className="rounded border-[#E8ECE7] text-[#64BC45] focus:ring-0 focus:ring-offset-0 cursor-pointer accent-[#64BC45]"
            />
            <span className="font-semibold text-[#263329] flex items-center space-x-1">
              <span className="w-2.5 h-2.5 rounded-full bg-[#64BC45] inline-block" />
              <span>Physical Monitoring Stations</span>
            </span>
          </label>

          <label className="flex items-center space-x-2 cursor-pointer select-none">
            <input 
              type="checkbox" 
              checked={showSavedPlaces} 
              onChange={(e) => setShowSavedPlaces(e.target.checked)}
              className="rounded border-[#E8ECE7] text-[#64BC45] focus:ring-0 focus:ring-offset-0 cursor-pointer accent-[#64BC45]"
            />
            <span className="font-semibold text-[#263329] flex items-center space-x-1">
              <Star className="w-3 h-3 text-amber-500 fill-amber-500 inline-block" />
              <span>Saved Places ({savedLocations.length})</span>
            </span>
          </label>
        </div>

        {/* CPCB Scale Reference Pills */}
        <div className="flex items-center space-x-1 text-[10px] font-mono text-[#788278]">
          <span className="hidden sm:inline-block mr-1 text-[#788278]">CPCB AQI:</span>
          <span className="px-1.5 py-0.5 rounded bg-[#F1F8ED] text-[#469A36] border border-[#C2EBBA]">0-50</span>
          <span className="px-1.5 py-0.5 rounded bg-cyan-50 text-cyan-700 border border-cyan-200">51-100</span>
          <span className="px-1.5 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200">101-200</span>
          <span className="px-1.5 py-0.5 rounded bg-orange-50 text-orange-700 border border-orange-200">201-300</span>
          <span className="px-1.5 py-0.5 rounded bg-red-50 text-red-700 border border-red-200">301+</span>
        </div>
      </div>

      {/* Main Grid: Map (Left) + Information & Route Controls (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Map Canvas (7 cols on desktop) */}
        <div className="lg:col-span-7 h-[580px] rounded-2xl overflow-hidden border border-[#E8ECE7] shadow-md relative">
          <MapContainer
            center={defaultCenter}
            zoom={11}
            scrollWheelZoom={true}
            style={{ width: '100%', height: '100%' }}
          >
            <MapViewController 
              center={defaultCenter} 
              zoom={11} 
              bounds={mapBounds} 
            />

            {/* Dark Matter CartoDB Basemap */}
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
              url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            />

            {/* Layer 1: Atmospheric Forecast Grid Overlay (Copernicus CAMS Model) */}
            {showGridOverlay && gridCells.map((cell) => {
              return (
                <Rectangle
                  key={cell.cell_id}
                  bounds={cell.bounds}
                  pathOptions={{
                    color: cell.color,
                    weight: 1.2,
                    dashArray: '5, 5',
                    fillColor: cell.color,
                    fillOpacity: 0.12
                  }}
                >
                  <Tooltip direction="center" opacity={0.9} permanent={false}>
                    <div className="bg-white border border-[#E8ECE7] p-2 rounded-xl text-xs space-y-1 font-sans shadow-md">
                      <div className="flex items-center space-x-1.5 text-[#469A36] font-bold border-b border-[#E8ECE7] pb-1">
                        <Layers className="w-3 h-3" />
                        <span>CAMS Model Forecast Grid</span>
                      </div>
                      <p className="text-[11px] text-[#263329]">
                        Forecast PM2.5: <strong className="font-mono text-[#263329]">{cell.pm25} µg/m³</strong>
                      </p>
                      <p className="text-[10px] text-[#788278]">
                        Category: <span className="font-semibold" style={{ color: cell.color }}>{cell.aqi_category}</span>
                      </p>
                      <p className="text-[9px] text-[#788278] italic">
                        {cell.confidence_label}
                      </p>
                    </div>
                  </Tooltip>
                </Rectangle>
              );
            })}

            {/* Layer 2: Real-Time Travel Route Polyline with Segmented Risk Colors */}
            {activeMode === 'route' && routeData && routeData.segments && routeData.segments.map((seg) => {
              const isSelected = selectedSegmentId === seg.segment_id;
              return (
                <Polyline
                  key={`seg-${seg.segment_id}`}
                  positions={seg.coordinates}
                  pathOptions={{
                    color: seg.risk_color || '#64BC45',
                    weight: isSelected ? 8 : 5,
                    opacity: isSelected ? 1.0 : 0.85,
                    lineCap: 'round',
                    lineJoin: 'round'
                  }}
                  eventHandlers={{
                    click: () => setSelectedSegmentId(seg.segment_id)
                  }}
                >
                  <Popup>
                    <div className="p-1 space-y-2 text-[#263329] min-w-[220px]">
                      <div className="border-b border-[#E8ECE7] pb-1">
                        <span className="text-[10px] text-[#469A36] font-bold uppercase tracking-wider block">
                          Segment {seg.segment_id}
                        </span>
                        <h4 className="font-bold text-xs text-[#263329]">{seg.title}</h4>
                      </div>

                      <div className="flex items-baseline justify-between text-xs">
                        <span className="text-[#788278]">Estimated PM2.5:</span>
                        <span className="font-mono font-bold text-[#263329]">{seg.estimated_pm25} µg/m³</span>
                      </div>
                      <div className="flex items-baseline justify-between text-xs">
                        <span className="text-[#788278]">Corridor Category:</span>
                        <span className="font-bold font-sans" style={{ color: seg.risk_color }}>
                          {seg.aqi_category}
                        </span>
                      </div>
                      <div className="flex items-baseline justify-between text-[11px] text-[#788278]">
                        <span>Distance & Time:</span>
                        <span className="font-mono text-[#263329]">{seg.distance_km} km ({seg.duration_mins} min)</span>
                      </div>

                      <div className="pt-1.5 border-t border-[#E8ECE7] text-[10px] text-[#788278] space-y-0.5">
                        <div className="flex items-center space-x-1 text-[#469A36] font-semibold">
                          <MapPin className="w-3 h-3 flex-shrink-0" />
                          <span>Nearest Monitor: {seg.nearest_station_name}</span>
                        </div>
                        <p className="text-[9px] text-[#788278]">
                          {seg.nearest_station_distance_km} km away &bull; {seg.nearest_station_is_measured ? 'Measured Ground Monitor' : 'Regional Model'}
                        </p>
                        <p className="text-[9px] text-amber-800 italic pt-1">
                          {seg.data_provenance_note}
                        </p>
                      </div>
                    </div>
                  </Popup>
                </Polyline>
              );
            })}

            {/* Layer 3: Origin and Destination Pins */}
            {activeMode === 'route' && routeData && routeData.route_geometry?.length > 0 && (
              <>
                {/* Origin Marker */}
                <CircleMarker
                  center={routeData.route_geometry[0]}
                  radius={8}
                  pathOptions={{
                    color: '#64BC45',
                    fillColor: '#64BC45',
                    fillOpacity: 1,
                    weight: 2
                  }}
                >
                  <Tooltip permanent direction="top" offset={[0, -8]}>
                    <span className="text-[10px] font-bold text-[#263329] bg-white px-1.5 py-0.5 rounded shadow border border-[#E8ECE7]">
                      Start: {routeData.origin_display_name.split('(')[0].trim()}
                    </span>
                  </Tooltip>
                </CircleMarker>

                {/* Destination Marker */}
                <CircleMarker
                  center={routeData.route_geometry[routeData.route_geometry.length - 1]}
                  radius={8}
                  pathOptions={{
                    color: '#ef4444',
                    fillColor: '#ef4444',
                    fillOpacity: 1,
                    weight: 2
                  }}
                >
                  <Tooltip permanent direction="top" offset={[0, -8]}>
                    <span className="text-[10px] font-bold text-[#263329] bg-white px-1.5 py-0.5 rounded shadow border border-[#E8ECE7]">
                      End: {routeData.destination_display_name.split('(')[0].trim()}
                    </span>
                  </Tooltip>
                </CircleMarker>
              </>
            )}

            {/* Layer 4: Monitoring Station Markers */}
            {showStations && currentStationList.map((st) => {
              const color = getMarkerColor(st.aqi, st.pm25);
              const isSelected = (st.name === selectedLocation) || (focusedStation === st.name);
              const isMeasured = st.is_measured || (st.measurement_type === 'measured');

              return (
                <CircleMarker
                  key={st.station_id || st.name}
                  center={[st.latitude, st.longitude]}
                  radius={isSelected ? 14 : 10}
                  pathOptions={{
                    color: isMeasured ? '#ffffff' : color,
                    fillColor: color,
                    fillOpacity: 0.8,
                    weight: isMeasured ? 2.5 : 1.5,
                    dashArray: isMeasured ? undefined : '2, 3'
                  }}
                  eventHandlers={{
                    click: () => {
                      setFocusedStation(st.name);
                      if (onSelectLocation) onSelectLocation(st.name);
                    }
                  }}
                >
                  <Popup>
                    <div className="space-y-2 p-1 text-[#263329] min-w-[230px]">
                      <div className="border-b border-[#E8ECE7] pb-1.5">
                        <div className="flex items-center justify-between">
                          <h4 className="font-bold text-xs text-[#263329]">{st.display_name}</h4>
                          <span className={`text-[9px] uppercase font-bold px-1.5 py-0.5 rounded ${
                            isMeasured 
                              ? 'bg-[#F1F8ED] text-[#469A36] border border-[#C2EBBA]' 
                              : 'bg-cyan-50 text-cyan-700 border border-cyan-200'
                          }`}>
                            {isMeasured ? 'Measured' : 'Forecast'}
                          </span>
                        </div>
                        <p className="text-[10px] text-[#788278] font-mono mt-0.5">
                          {st.latitude.toFixed(4)}°N, {st.longitude.toFixed(4)}°E
                        </p>
                      </div>

                      {/* Pollution Values */}
                      <div className="grid grid-cols-2 gap-2 bg-[#F5F7F4] p-2 rounded-xl border border-[#E8ECE7]">
                        <div>
                          <p className="text-[9px] text-[#788278] uppercase">CPCB NAQI</p>
                          <p className="text-lg font-extrabold text-[#263329] font-mono">{st.aqi ?? '--'}</p>
                          <span className="text-[9px] font-semibold" style={{ color }}>{st.aqi_category ?? 'Moderate'}</span>
                        </div>
                        <div className="text-right">
                          <p className="text-[9px] text-[#788278] uppercase">PM2.5</p>
                          <p className="text-base font-extrabold text-[#469A36] font-mono">
                            {st.pm25 !== null ? `${st.pm25}` : '--'} <span className="text-[10px] text-[#788278] font-normal">µg/m³</span>
                          </p>
                          {st.pm10 && (
                            <p className="text-[9px] text-[#788278]">PM10: {st.pm10} µg/m³</p>
                          )}
                        </div>
                      </div>

                      {/* Station Metadata & Timestamps */}
                      <div className="text-[10px] text-[#788278] space-y-1 pt-1 border-t border-[#E8ECE7]">
                        <div className="flex justify-between">
                          <span>Data Source:</span>
                          <span className="text-[#263329] truncate max-w-[140px] text-right font-medium">
                            {st.data_source || 'CPCB / OpenAQ'}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>Observation Time:</span>
                          <span className="font-mono text-[#263329]">
                            {st.observation_time_iso ? new Date(st.observation_time_iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Live'}
                          </span>
                        </div>
                        {st.temperature_c && (
                          <div className="flex justify-between">
                            <span>Weather:</span>
                            <span className="text-[#263329]">{st.temperature_c}°C &bull; {st.wind_speed_kmh} km/h wind</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </Popup>
                </CircleMarker>
              );
            })}

            {/* Layer 5: Saved Locations Markers */}
            {showSavedPlaces && savedLocations && savedLocations.map((loc) => {
              const aq = loc.air_quality;
              const isSelected = selectedLocation === loc.location_name || selectedLocation === loc.location_id;
              
              return (
                <CircleMarker
                  key={`saved-${loc.location_id}`}
                  center={[loc.latitude, loc.longitude]}
                  radius={isSelected ? 15 : 11}
                  pathOptions={{
                    color: loc.is_primary ? '#469A36' : '#64BC45',
                    fillColor: loc.is_primary ? '#469A36' : '#7FC441',
                    fillOpacity: 0.9,
                    weight: isSelected ? 3 : 2
                  }}
                  eventHandlers={{
                    click: () => {
                      if (onSelectLocation) onSelectLocation(loc.location_name || loc.location_id);
                    }
                  }}
                >
                  <Tooltip direction="top" offset={[0, -10]}>
                    <div className="text-[11px] font-bold text-[#263329] bg-white px-2 py-1 rounded shadow border border-[#E8ECE7]">
                      <span className="text-[#469A36] font-mono uppercase text-[9px] block">
                        {loc.location_type?.replace('_', ' ')}
                      </span>
                      {loc.location_name} {aq?.pm25 ? `• PM2.5: ${aq.pm25}` : ''}
                    </div>
                  </Tooltip>
                  <Popup>
                    <div className="p-2 space-y-2 text-[#263329] min-w-[230px]">
                      <div className="border-b border-[#E8ECE7] pb-1.5">
                        <div className="flex items-center justify-between">
                          <span className="text-[9px] font-bold uppercase text-amber-600 font-mono">
                            {loc.location_type?.replace('_', ' ')} {loc.is_primary ? '(Primary)' : ''}
                          </span>
                          {aq?.freshness_status && (
                            <span className="text-[9px] px-1.5 py-0.5 rounded bg-[#F1F8ED] text-[#469A36] border border-[#C2EBBA] font-mono">
                              {aq.freshness_status}
                            </span>
                          )}
                        </div>
                        <h4 className="font-bold text-sm text-[#263329]">{loc.location_name}</h4>
                        {loc.address && <p className="text-[10px] text-[#788278]">{loc.address}</p>}
                      </div>

                      <div className="grid grid-cols-2 gap-2 bg-[#F5F7F4] p-2 rounded-xl border border-[#E8ECE7]">
                        <div>
                          <span className="text-[9px] text-[#788278] uppercase font-mono block">PM2.5 Ambient</span>
                          <span className="text-base font-extrabold text-[#469A36] font-mono">
                            {aq?.pm25 !== null && aq?.pm25 !== undefined ? `${aq.pm25} µg/m³` : 'Unavailable'}
                          </span>
                        </div>
                        {aq?.aqi !== null && aq?.aqi !== undefined && (
                          <div className="text-right">
                            <span className="text-[9px] text-[#788278] uppercase font-mono block">CPCB AQI</span>
                            <span className="text-sm font-bold text-[#263329] font-mono">
                              {aq.aqi} ({aq.aqi_category})
                            </span>
                          </div>
                        )}
                      </div>

                      {aq?.nearest_station && (
                        <div className="text-[10px] text-[#263329] space-y-0.5">
                          <p className="text-[#788278]">Nearest Station:</p>
                          <p className="font-semibold text-[#263329]">
                            {aq.nearest_station.station_name} ({aq.nearest_station.distance_km} km away)
                          </p>
                        </div>
                      )}

                      <button
                        onClick={() => {
                          if (onSelectLocation) onSelectLocation(loc.location_name || loc.location_id);
                        }}
                        className="w-full py-1.5 px-3 rounded-lg bg-[#64BC45] hover:bg-[#469A36] text-white font-bold text-xs transition cursor-pointer shadow"
                      >
                        Monitor on Dashboard
                      </button>
                    </div>
                  </Popup>
                </CircleMarker>
              );
            })}

            {/* Click to add location event handler & marker */}
            <MapClickHandler onMapClick={(latlng) => setMapClickPoint(latlng)} />

            {mapClickPoint && (
              <CircleMarker
                center={[mapClickPoint.lat, mapClickPoint.lng]}
                radius={9}
                pathOptions={{
                  color: '#64BC45',
                  fillColor: '#469A36',
                  fillOpacity: 0.9,
                  weight: 3
                }}
              >
                <Popup>
                  <div className="p-2 space-y-2 text-[#263329] min-w-[210px]">
                    <div className="border-b border-[#E8ECE7] pb-1">
                      <h4 className="font-bold text-xs text-[#263329]">Selected Map Point</h4>
                      <p className="text-[10px] text-[#469A36] font-mono">
                        {mapClickPoint.lat.toFixed(4)}°N, {mapClickPoint.lng.toFixed(4)}°E
                      </p>
                    </div>
                    <button
                      onClick={() => {
                        if (onOpenAddLocationModal) {
                          onOpenAddLocationModal({
                            latitude: mapClickPoint.lat,
                            longitude: mapClickPoint.lng
                          });
                        }
                        setMapClickPoint(null);
                      }}
                      className="w-full py-1.5 px-3 rounded-lg bg-[#64BC45] hover:bg-[#469A36] text-white font-bold text-xs cursor-pointer shadow flex items-center justify-center space-x-1"
                    >
                      <Plus className="w-3.5 h-3.5" />
                      <span>Save this Place</span>
                    </button>
                  </div>
                </Popup>
              </CircleMarker>
            )}
          </MapContainer>
        </div>

        {/* Right Column: Route Planner, Exposure Summary & Segment Inspector (5 cols on desktop) */}
        <div className="lg:col-span-5 space-y-4 flex flex-col justify-between">
          {/* Corridor Selection & Transit Mode */}
          <div className="bg-white p-5 border border-[#E8ECE7] rounded-2xl space-y-4 shadow-xs">
            <div className="flex items-center justify-between border-b border-[#E8ECE7] pb-3">
              <h3 className="font-bold text-[#263329] text-sm flex items-center space-x-2">
                <Navigation className="w-4 h-4 text-[#469A36]" />
                <span>Corridor Pollution Routing</span>
              </h3>
              <span className="text-[10px] font-mono text-[#788278]">OSRM Geometry</span>
            </div>

            {/* Origin & Destination Selectors */}
            <div className="space-y-3">
              <div className="space-y-1">
                <label className="text-[11px] font-semibold text-[#788278] flex items-center space-x-1">
                  <span className="w-2 h-2 rounded-full bg-[#64BC45]" />
                  <span>Starting Point</span>
                </label>
                <select
                  value={origin}
                  onChange={(e) => setOrigin(e.target.value)}
                  className="w-full p-2.5 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7] text-[#263329] text-xs font-semibold focus:border-[#64BC45] focus:bg-white outline-none transition"
                >
                  {availableLocations.map((loc) => (
                    <option key={loc.name} value={loc.name}>
                      {loc.display_name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Swap Button */}
              <div className="flex justify-center -my-1">
                <button
                  type="button"
                  onClick={handleSwapCorridor}
                  className="p-1.5 rounded-full bg-[#F5F7F4] hover:bg-[#E8ECE7] border border-[#E8ECE7] text-[#469A36] transition-colors cursor-pointer"
                  title="Swap Origin and Destination"
                >
                  <ArrowLeftRight className="w-3.5 h-3.5" />
                </button>
              </div>

              <div className="space-y-1">
                <label className="text-[11px] font-semibold text-[#788278] flex items-center space-x-1">
                  <span className="w-2 h-2 rounded-full bg-red-500" />
                  <span>Destination</span>
                </label>
                <select
                  value={destination}
                  onChange={(e) => setDestination(e.target.value)}
                  className="w-full p-2.5 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7] text-[#263329] text-xs font-semibold focus:border-[#64BC45] focus:bg-white outline-none transition"
                >
                  {availableLocations.map((loc) => (
                    <option key={loc.name} value={loc.name}>
                      {loc.display_name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Travel Mode Pills */}
            <div className="pt-2">
              <label className="text-[11px] font-semibold text-[#788278] block mb-1.5">
                Transit Mode & Respiration Profile
              </label>
              <div className="grid grid-cols-3 gap-2">
                <button
                  type="button"
                  onClick={() => setTravelMode('driving')}
                  className={`p-2 rounded-xl text-xs font-bold flex flex-col items-center justify-center space-y-1 transition-all cursor-pointer ${
                    travelMode === 'driving'
                      ? 'bg-[#64BC45] text-white shadow-sm'
                      : 'bg-[#F5F7F4] hover:bg-[#E8ECE7] text-[#788278] hover:text-[#263329] border border-[#E8ECE7]'
                  }`}
                >
                  <Car className="w-4 h-4" />
                  <span>Driving</span>
                </button>
                <button
                  type="button"
                  onClick={() => setTravelMode('cycling')}
                  className={`p-2 rounded-xl text-xs font-bold flex flex-col items-center justify-center space-y-1 transition-all cursor-pointer ${
                    travelMode === 'cycling'
                      ? 'bg-[#64BC45] text-white shadow-sm'
                      : 'bg-[#F5F7F4] hover:bg-[#E8ECE7] text-[#788278] hover:text-[#263329] border border-[#E8ECE7]'
                  }`}
                >
                  <Bike className="w-4 h-4" />
                  <span>Cycling</span>
                </button>
                <button
                  type="button"
                  onClick={() => setTravelMode('walking')}
                  className={`p-2 rounded-xl text-xs font-bold flex flex-col items-center justify-center space-y-1 transition-all cursor-pointer ${
                    travelMode === 'walking'
                      ? 'bg-[#64BC45] text-white shadow-sm'
                      : 'bg-[#F5F7F4] hover:bg-[#E8ECE7] text-[#788278] hover:text-[#263329] border border-[#E8ECE7]'
                  }`}
                >
                  <Footprints className="w-4 h-4" />
                  <span>Walking</span>
                </button>
              </div>
            </div>
          </div>

          {/* Loading or Error State */}
          {routeLoading && (
            <div className="bg-white border border-[#E8ECE7] rounded-2xl p-6 text-center text-[#788278] text-xs space-y-2 shadow-xs">
              <div className="w-6 h-6 border-2 border-[#64BC45] border-t-transparent rounded-full animate-spin mx-auto" />
              <p>Computing corridor road geometry and segment air quality...</p>
            </div>
          )}

          {routeError && (
            <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 text-red-500 flex-shrink-0" />
              <span>{routeError}</span>
            </div>
          )}

          {/* Route Pollution Summary & Time-Weighted Exposure */}
          {routeData && !routeLoading && (
            <div className="bg-white p-5 border border-[#E8ECE7] rounded-2xl space-y-4 shadow-xs">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-[10px] text-[#788278] uppercase font-semibold">Time-Weighted Exposure Index</span>
                  <div className="flex items-baseline space-x-2 mt-0.5">
                    <span className="text-3xl font-extrabold text-[#263329] font-mono">
                      {routeData.total_exposure_index}
                    </span>
                    <span className="text-xs text-[#788278]">µg/m³ PM2.5</span>
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-[10px] text-[#788278] block">Est. Duration</span>
                  <span className="text-lg font-bold font-mono text-[#469A36]">
                    {routeData.total_duration_minutes} min
                  </span>
                  <span className="text-[10px] text-[#788278] block font-mono">
                    {routeData.total_distance_km} km
                  </span>
                </div>
              </div>

              {/* Safety Advisory Banner */}
              <div className="p-3 rounded-xl bg-[#F1F8ED] border border-[#C2EBBA] text-xs text-[#263329] space-y-1">
                <div className="flex items-center space-x-1.5 font-bold text-[#469A36]">
                  <ShieldCheck className="w-4 h-4 text-[#469A36] flex-shrink-0" />
                  <span>{routeData.mode_label} Corridor Advisory</span>
                </div>
                <p className="text-[11px] text-[#788278] leading-relaxed">
                  {routeData.safety_advisory}
                </p>
              </div>

              {/* Corridor Segments List */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold text-[#263329] flex items-center space-x-1">
                  <span>Corridor Segments ({routeData.segments?.length || 0})</span>
                </h4>
                <div className="max-h-44 overflow-y-auto space-y-2 pr-1">
                  {routeData.segments?.map((seg) => {
                    const isSelected = selectedSegmentId === seg.segment_id;
                    return (
                      <div
                        key={seg.segment_id}
                        onClick={() => setSelectedSegmentId(seg.segment_id)}
                        className={`p-2.5 rounded-xl border text-xs transition-all cursor-pointer ${
                          isSelected
                            ? 'bg-[#F1F8ED] border-[#64BC45] shadow-xs'
                            : 'bg-[#F5F7F4] border-[#E8ECE7] hover:border-[#C2EBBA]'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-[#263329] truncate max-w-[180px]">
                            {seg.title}
                          </span>
                          <span 
                            className="px-2 py-0.5 rounded text-[10px] font-bold font-mono"
                            style={{ backgroundColor: `${seg.risk_color}20`, color: seg.risk_color }}
                          >
                            {seg.estimated_pm25} µg/m³
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-[10px] text-[#788278] mt-1">
                          <span>Near: <strong className="text-[#263329]">{seg.nearest_station_name}</strong> ({seg.nearest_station_distance_km} km)</span>
                          <span className="font-mono">{seg.duration_mins} min</span>
                        </div>
                        {isSelected && (
                          <p className="text-[9px] text-amber-800 italic mt-1.5 pt-1 border-t border-[#E8ECE7]">
                            {seg.data_provenance_note}
                          </p>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Destination Environmental Intelligence */}
              {routeData.destination_info && (
                <div className="p-3 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7] text-xs space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-[#263329] flex items-center space-x-1.5">
                      <MapPin className="w-3.5 h-3.5 text-red-500" />
                      <span>Destination: {routeData.destination_info.display_name}</span>
                    </span>
                    <span className="text-[10px] font-mono text-[#469A36] font-bold">
                      {routeData.destination_info.pm25 !== null ? `${routeData.destination_info.pm25} µg/m³` : '--'}
                    </span>
                  </div>
                  {/* Strict Non-Indoor Disclaimer Rule */}
                  <p className="text-[10px] text-[#788278] italic leading-relaxed border-t border-[#E8ECE7] pt-1.5">
                    {routeData.destination_info.indoor_disclaimer}
                  </p>
                </div>
              )}

              {/* Alternative Route Comparison (With Strict Comparable Data Guard) */}
              {routeData.alternative_comparison && (
                <div className="p-3 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7] text-xs space-y-1.5">
                  <div className="flex items-center justify-between text-[11px] font-bold text-[#263329]">
                    <span>Alternative Corridor Comparison</span>
                    <span className="text-[9px] uppercase font-mono px-1.5 py-0.5 rounded bg-[#F1F8ED] border border-[#C2EBBA] text-[#469A36]">
                      {routeData.alternative_comparison.has_sufficient_comparable_data ? 'Verified' : 'Notice'}
                    </span>
                  </div>
                  <p className="text-[11px] text-[#788278]">
                    {routeData.alternative_comparison.comparison_summary}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
