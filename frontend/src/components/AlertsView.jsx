import React, { useState, useEffect } from 'react';
import { 
  Bell, 
  AlertTriangle, 
  CheckCircle2, 
  ShieldAlert, 
  Sliders, 
  Smartphone,
  Info,
  Sparkles,
  Clock,
  MapPin,
  TrendingUp,
  Check,
  Save,
  RotateCcw,
  HelpCircle,
  HeartPulse,
  Calendar,
  Layers,
  ArrowRight
} from 'lucide-react';
import { 
  fetchAlerts, 
  fetchNotificationSettings, 
  updateNotificationSettings, 
  fetchCPCBRecommendations 
} from '../services/api';

const ALL_STATIONS = [
  { id: 'bengaluru_central', label: 'Bengaluru Central' },
  { id: 'silk_board', label: 'Silk Board' },
  { id: 'electronic_city', label: 'Electronic City' },
  { id: 'hebbal', label: 'Hebbal' },
  { id: 'peenya', label: 'Peenya' },
  { id: 'yelahanka', label: 'Yelahanka' },
  { id: 'koramangala', label: 'Koramangala' }
];

export default function AlertsView({ currentProfile, userProfile }) {
  const [activeSubTab, setActiveSubTab] = useState('alerts'); // 'alerts' | 'settings' | 'cpcb_guide'
  
  // Alerts Stream State
  const [alerts, setAlerts] = useState([]);
  const [loadingAlerts, setLoadingAlerts] = useState(true);

  // Settings State
  const [settings, setSettings] = useState(null);
  const [loadingSettings, setLoadingSettings] = useState(true);
  const [savingSettings, setSavingSettings] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // CPCB Safety Recommendations Table State
  const [cpcbData, setCpcbData] = useState(null);

  // Push notifications
  const [pushEnabled, setPushEnabled] = useState(false);
  const [notificationStatus, setNotificationStatus] = useState('default');

  const userId = userProfile?.id || 'default_user';

  // Load Alerts
  const loadAlertsData = async () => {
    setLoadingAlerts(true);
    try {
      const data = await fetchAlerts(currentProfile, userId);
      setAlerts(data);
    } catch (err) {
      console.error('Failed to load alerts:', err);
    } finally {
      setLoadingAlerts(false);
    }
  };

  // Load Settings
  const loadSettingsData = async () => {
    setLoadingSettings(true);
    try {
      const s = await fetchNotificationSettings(userId);
      setSettings(s);
    } catch (err) {
      console.error('Failed to load notification settings:', err);
    } finally {
      setLoadingSettings(false);
    }
  };

  // Load CPCB Guide
  const loadCPCBGuide = async () => {
    try {
      const guide = await fetchCPCBRecommendations(userId);
      setCpcbData(guide);
    } catch (err) {
      console.error('Failed to load CPCB recommendations:', err);
    }
  };

  useEffect(() => {
    loadAlertsData();
    loadSettingsData();
    loadCPCBGuide();
  }, [currentProfile, userProfile?.user_category, userProfile?.sensitivity_preference]);

  const requestNotificationPermission = async () => {
    if (!('Notification' in window)) {
      alert('This browser does not support desktop notifications.');
      return;
    }

    try {
      const permission = await Notification.requestPermission();
      setNotificationStatus(permission);
      if (permission === 'granted') {
        setPushEnabled(true);
        new Notification('AtmosAI Smart AQI Alerts Active', {
          body: `Smart CPCB notifications enabled for your profile with personalized safety recommendations.`,
          icon: '/favicon.svg'
        });
      }
    } catch (err) {
      console.error('Notification permission error:', err);
    }
  };

  const handleSaveSettings = async () => {
    if (!settings) return;
    setSavingSettings(true);
    try {
      const updated = await updateNotificationSettings({
        high_pollution_threshold: settings.current_threshold,
        custom_threshold: settings.current_threshold,
        use_recommended_threshold: settings.use_recommended_threshold,
        threshold_crossing_alerts: settings.threshold_crossing_alerts,
        deterioration_alerts: settings.deterioration_alerts,
        forecast_alerts: settings.forecast_alerts,
        surge_warnings: settings.surge_warnings,
        daily_morning_brief: settings.daily_morning_brief,
        commute_window_alerts: settings.commute_window_alerts,
        improving_air_alerts: settings.improving_air_alerts,
        monitored_locations: settings.monitored_locations
      }, userId);

      setSettings(updated);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2500);

      // Refresh alerts with updated rules
      loadAlertsData();
    } catch (err) {
      console.error('Failed to update notification settings:', err);
    } finally {
      setSavingSettings(false);
    }
  };

  const toggleLocation = (locId) => {
    if (!settings) return;
    const current = settings.monitored_locations || [];
    const exists = current.includes(locId);
    const updated = exists 
      ? (current.length > 1 ? current.filter(id => id !== locId) : current) // Keep at least one
      : [...current, locId];
    setSettings({ ...settings, monitored_locations: updated });
  };

  const getAlertIcon = (severity) => {
    if (severity === 'high' || severity === 'critical') {
      return <ShieldAlert className="w-5 h-5 text-rose-400 flex-shrink-0" />;
    }
    if (severity === 'medium') {
      return <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0" />;
    }
    return <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />;
  };

  const getAQIColor = (val) => {
    if (val <= 50) return '#10b981';
    if (val <= 100) return '#06b6d4';
    if (val <= 200) return '#f59e0b';
    if (val <= 300) return '#f97316';
    if (val <= 400) return '#ef4444';
    return '#991b1b';
  };

  return (
    <div className="space-y-6 pb-20 sm:pb-8">
      {/* Top Banner */}
      <div className="p-4 sm:p-5 rounded-2xl bg-gradient-to-r from-[#F1F8ED] via-white to-[#F1F8ED] border border-[#C2EBBA] shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <div className="p-2 rounded-xl bg-[#C2EBBA] text-[#469A36]">
                <Bell className="w-5 h-5" />
              </div>
              <div>
                <h1 className="text-lg sm:text-xl font-black text-[#263329] tracking-tight">
                  Smart AQI Alerts & Safety Recommendations
                </h1>
                <p className="text-xs text-[#788278]">
                  India CPCB NAQI Standards &bull; Multi-Horizon Forecast Warnings &bull; Personalized Safety Advisories
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={requestNotificationPermission}
              className={`px-3 py-1.5 rounded-xl border text-xs font-semibold flex items-center space-x-1.5 transition cursor-pointer ${
                pushEnabled
                  ? 'bg-[#F1F8ED] border-[#C2EBBA] text-[#469A36]'
                  : 'bg-white hover:bg-[#F5F7F4] border-[#E8ECE7] text-[#263329]'
              }`}
            >
              <Smartphone className="w-3.5 h-3.5" />
              <span>{pushEnabled ? 'Push Notifications Enabled' : 'Enable Web Push Alerts'}</span>
            </button>
          </div>
        </div>

        {/* Sub-navigation Tabs */}
        <div className="flex space-x-2 mt-4 pt-3 border-t border-[#E8ECE7]">
          <button
            onClick={() => setActiveSubTab('alerts')}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer flex items-center space-x-1.5 ${
              activeSubTab === 'alerts'
                ? 'bg-[#64BC45] text-white shadow-sm font-bold'
                : 'bg-white text-[#788278] hover:text-[#263329] border border-[#E8ECE7]'
            }`}
          >
            <Bell className="w-3.5 h-3.5" />
            <span>Active Alerts Stream ({alerts.length})</span>
          </button>

          <button
            onClick={() => setActiveSubTab('settings')}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer flex items-center space-x-1.5 ${
              activeSubTab === 'settings'
                ? 'bg-[#64BC45] text-white shadow-sm font-bold'
                : 'bg-white text-[#788278] hover:text-[#263329] border border-[#E8ECE7]'
            }`}
          >
            <Sliders className="w-3.5 h-3.5" />
            <span>Notification Settings</span>
          </button>

          <button
            onClick={() => setActiveSubTab('cpcb_guide')}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer flex items-center space-x-1.5 ${
              activeSubTab === 'cpcb_guide'
                ? 'bg-[#64BC45] text-white shadow-sm font-bold'
                : 'bg-white text-[#788278] hover:text-[#263329] border border-[#E8ECE7]'
            }`}
          >
            <HelpCircle className="w-3.5 h-3.5" />
            <span>CPCB Standards & Safety Guide</span>
          </button>
        </div>
      </div>

      {/* TAB 1: ACTIVE ALERTS STREAM */}
      {activeSubTab === 'alerts' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between px-1">
            <h2 className="text-sm font-bold text-[#263329] uppercase tracking-wider flex items-center space-x-2">
              <span>Live Alert Queue</span>
              <span className="text-xs font-normal text-[#788278]">
                (Filtered by your notification thresholds & monitored stations)
              </span>
            </h2>
            <button
              onClick={loadAlertsData}
              className="text-xs text-[#469A36] hover:underline flex items-center space-x-1 cursor-pointer"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Refresh</span>
            </button>
          </div>

          {loadingAlerts ? (
            <div className="p-12 text-center text-[#788278] text-xs bg-white border border-[#E8ECE7] rounded-2xl shadow-xs">
              Checking real-time sensor streams and forecast horizons...
            </div>
          ) : alerts.length === 0 ? (
            <div className="p-8 text-center text-[#788278] text-xs rounded-2xl bg-white border border-[#E8ECE7] space-y-2 shadow-xs">
              <CheckCircle2 className="w-8 h-8 text-[#469A36] mx-auto opacity-70" />
              <p className="font-semibold text-[#263329]">All air quality metrics are currently within your configured thresholds.</p>
              <p className="text-[11px] text-[#788278]">
                You will receive prompt alerts if ambient particulate concentrations rise or ML models forecast a surge.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {alerts.map((a) => {
                const isForecast = a.alert_source === 'forecast_prediction';
                const isSummary = a.alert_source === 'daily_summary';
                const isDeterioration = a.alert_type === 'deterioration';

                return (
                  <div
                    key={a.id}
                    className={`p-4 sm:p-5 rounded-2xl border transition shadow-xs space-y-3 ${
                      a.severity === 'high' || a.severity === 'critical'
                        ? 'bg-rose-50/70 border-rose-200'
                        : a.severity === 'medium'
                        ? 'bg-amber-50/70 border-amber-200'
                        : 'bg-[#F1F8ED]/70 border-[#C2EBBA]'
                    }`}
                  >
                    {/* Alert Top Bar */}
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-start space-x-2.5">
                        {getAlertIcon(a.severity)}
                        <div className="space-y-0.5">
                          <div className="flex items-center space-x-2 flex-wrap">
                            <h3 className="text-sm font-bold text-[#263329]">{a.title}</h3>
                            
                            {/* Explicit Source Badge: Current vs Forecast */}
                            <span className={`text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-md border ${
                              isForecast 
                                ? 'bg-[#F1F8ED] text-[#469A36] border-[#C2EBBA]' 
                                : isSummary
                                ? 'bg-purple-50 text-purple-700 border-purple-200'
                                : 'bg-amber-50 text-amber-800 border-amber-200'
                            }`}>
                              {isForecast ? '3–6H FORECAST ADVISORY' : isSummary ? 'DAILY BRIEF' : 'LIVE SENSOR ALERT'}
                            </span>

                            {a.cpcb_category && (
                              <span 
                                className="text-[10px] font-bold px-2 py-0.5 rounded-md border"
                                style={{ 
                                  backgroundColor: `${getAQIColor(a.current_aqi || 80)}15`,
                                  borderColor: `${getAQIColor(a.current_aqi || 80)}40`,
                                  color: getAQIColor(a.current_aqi || 80)
                                }}
                              >
                                {a.cpcb_category} (AQI {a.current_aqi || '--'})
                              </span>
                            )}
                          </div>

                          <p className="text-[11px] text-[#788278] flex items-center space-x-2 pt-0.5">
                            <span className="flex items-center space-x-1">
                              <MapPin className="w-3 h-3 text-[#469A36]" />
                              <span>{a.location_name}</span>
                            </span>
                            <span>&bull;</span>
                            <span className="flex items-center space-x-1">
                              <Clock className="w-3 h-3 text-[#788278]" />
                              <span>{new Date(a.timestamp).toLocaleTimeString()}</span>
                            </span>
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Main Message */}
                    <p className="text-xs sm:text-sm text-[#263329] leading-relaxed font-medium">
                      {a.message}
                    </p>

                    {/* Safety Recommendation Box */}
                    {a.safety_recommendation && (
                      <div className="p-3 rounded-xl bg-white border border-[#E8ECE7] text-xs text-[#263329] space-y-1">
                        <div className="flex items-center space-x-1.5 text-[#469A36] font-bold text-[11px] uppercase tracking-wider">
                          <Sparkles className="w-3.5 h-3.5" />
                          <span>CPCB Safety Guidance</span>
                        </div>
                        <p className="text-[#263329] font-medium">{a.safety_recommendation}</p>
                        
                        {a.sensitivity_note && (
                          <p className="text-[#469A36] text-[11px] pt-1 border-t border-[#E8ECE7]">
                            {a.sensitivity_note}
                          </p>
                        )}
                      </div>
                    )}

                    {/* Disclaimer */}
                    <p className="text-[10px] text-[#788278] italic">
                      {a.disclaimer}
                    </p>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: NOTIFICATION SETTINGS & THRESHOLDS */}
      {activeSubTab === 'settings' && settings && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Threshold Selector & Recommendation */}
          <div className="lg:col-span-1 space-y-5">
            {/* Recommended Threshold Card */}
            <div className="p-5 border border-[#C2EBBA] rounded-2xl bg-gradient-to-b from-[#F1F8ED] to-white space-y-3.5 shadow-xs">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold uppercase tracking-wider text-[#469A36] flex items-center space-x-1.5">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Smart Recommended Threshold</span>
                </span>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-black bg-[#F1F8ED] text-[#469A36] border border-[#C2EBBA]">
                  AQI {settings.recommended_threshold}
                </span>
              </div>

              <div className="space-y-1">
                <h4 className="text-xs font-bold text-[#263329] capitalize">
                  Personalized for {settings.user_category.replace('_', ' ')}
                  {settings.sensitivity_preference !== 'none' && ` & ${settings.sensitivity_preference.replace('_', ' ')}`}
                </h4>
                <p className="text-[11px] text-[#788278] leading-relaxed">
                  {settings.recommended_threshold_reason}
                </p>
              </div>

              {/* Recommendation Mode Choice */}
              <div className="pt-2 border-t border-[#E8ECE7] space-y-2 text-xs">
                <label className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="radio"
                    name="threshold_mode"
                    checked={settings.use_recommended_threshold}
                    onChange={() => setSettings({
                      ...settings,
                      use_recommended_threshold: true,
                      current_threshold: settings.recommended_threshold
                    })}
                    className="accent-[#64BC45]"
                  />
                  <span className="text-[#263329] font-medium">Use Recommended Threshold (AQI {settings.recommended_threshold})</span>
                </label>

                <label className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="radio"
                    name="threshold_mode"
                    checked={!settings.use_recommended_threshold}
                    onChange={() => setSettings({ ...settings, use_recommended_threshold: false })}
                    className="accent-[#64BC45]"
                  />
                  <span className="text-[#788278] font-medium">Use Custom AQI Threshold</span>
                </label>
              </div>
            </div>

            {/* Custom AQI Slider */}
            <div className={`bg-white p-5 border rounded-2xl space-y-3 shadow-xs ${
              settings.use_recommended_threshold ? 'opacity-60 border-[#E8ECE7]' : 'border-[#64BC45]'
            }`}>
              <div className="flex justify-between items-center text-xs">
                <span className="text-[#788278] font-semibold">Active Trigger Threshold:</span>
                <span className="font-mono font-black text-sm text-[#469A36]">
                  AQI {settings.current_threshold}
                </span>
              </div>

              <input
                type="range"
                min="40"
                max="300"
                step="5"
                disabled={settings.use_recommended_threshold}
                value={settings.current_threshold}
                onChange={(e) => setSettings({
                  ...settings,
                  current_threshold: Number(e.target.value)
                })}
                className="w-full accent-[#64BC45] cursor-pointer disabled:cursor-not-allowed"
              />

              <div className="grid grid-cols-5 text-[9px] text-center font-mono text-[#788278] gap-1">
                <span className="text-[#469A36]">50 (Good)</span>
                <span className="text-cyan-600">100 (Sat.)</span>
                <span className="text-amber-600">200 (Mod.)</span>
                <span className="text-orange-600">300 (Poor)</span>
                <span className="text-red-600">400 (V.Poor)</span>
              </div>
            </div>

            {/* Monitored Locations Multi-Selector */}
            <div className="bg-white p-5 border border-[#E8ECE7] rounded-2xl space-y-3 shadow-xs">
              <label className="text-xs font-bold uppercase tracking-wider text-[#469A36] block flex items-center space-x-1.5">
                <MapPin className="w-3.5 h-3.5" />
                <span>Monitored Stations (Location Alerts)</span>
              </label>
              <div className="flex flex-wrap gap-1.5">
                {ALL_STATIONS.map((st) => {
                  const isChecked = (settings.monitored_locations || []).includes(st.id);
                  return (
                    <button
                      key={st.id}
                      type="button"
                      onClick={() => toggleLocation(st.id)}
                      className={`px-2.5 py-1 rounded-xl text-xs font-semibold transition cursor-pointer flex items-center space-x-1 ${
                        isChecked
                          ? 'bg-[#F1F8ED] border border-[#64BC45] text-[#469A36]'
                          : 'bg-[#F5F7F4] border border-[#E8ECE7] text-[#788278] hover:border-[#C2EBBA]'
                      }`}
                    >
                      <span>{st.label}</span>
                      {isChecked && <Check className="w-3 h-3 text-[#469A36]" />}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Right Column: Individual Category Toggles & Save Action */}
          <div className="lg:col-span-2 space-y-5">
            <div className="bg-white p-6 border border-[#E8ECE7] rounded-2xl space-y-5 shadow-xs">
              <div className="flex items-center justify-between border-b border-[#E8ECE7] pb-3">
                <div>
                  <h3 className="text-sm font-bold text-[#263329]">Enable / Disable Notification Categories</h3>
                  <p className="text-xs text-[#788278]">Fine-tune which environmental events trigger alerts</p>
                </div>

                <button
                  onClick={handleSaveSettings}
                  disabled={savingSettings}
                  className={`px-4 py-2 rounded-xl text-xs font-bold flex items-center space-x-1.5 transition cursor-pointer shadow-sm ${
                    saveSuccess
                      ? 'bg-[#469A36] text-white font-black'
                      : 'bg-[#64BC45] hover:bg-[#469A36] text-white'
                  }`}
                >
                  {saveSuccess ? (
                    <>
                      <Check className="w-4 h-4 stroke-[3]" />
                      <span>Preferences Saved!</span>
                    </>
                  ) : savingSettings ? (
                    <span>Saving...</span>
                  ) : (
                    <>
                      <Save className="w-4 h-4" />
                      <span>Save Notification Preferences</span>
                    </>
                  )}
                </button>
              </div>

              {/* Toggles Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                {/* 1. Threshold Crossing */}
                <div className="p-3.5 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7] flex items-start justify-between space-x-3">
                  <div className="space-y-0.5">
                    <span className="text-xs font-bold text-[#263329] block">Threshold Crossing Alerts</span>
                    <p className="text-[11px] text-[#788278]">
                      Alerts when measured AQI crosses above your configured trigger threshold.
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={settings.threshold_crossing_alerts}
                    onChange={(e) => setSettings({ ...settings, threshold_crossing_alerts: e.target.checked })}
                    className="accent-[#64BC45] rounded mt-1"
                  />
                </div>

                {/* 2. Deterioration Alerts */}
                <div className="p-3.5 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7] flex items-start justify-between space-x-3">
                  <div className="space-y-0.5">
                    <span className="text-xs font-bold text-[#263329] block">Pollution Deterioration Alerts</span>
                    <p className="text-[11px] text-[#788278]">
                      Alerts on sudden particulate accumulation or category downgrade (&ge; 20 AQI spike).
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={settings.deterioration_alerts}
                    onChange={(e) => setSettings({ ...settings, deterioration_alerts: e.target.checked })}
                    className="accent-[#64BC45] rounded mt-1"
                  />
                </div>

                {/* 3. Forecast-Based Alerts */}
                <div className="p-3.5 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7] flex items-start justify-between space-x-3">
                  <div className="space-y-0.5">
                    <span className="text-xs font-bold text-[#263329] block">Forecast Surge Advisories</span>
                    <p className="text-[11px] text-[#788278]">
                      3–6 hour ML predictive warnings before particulate accumulation intensifies.
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={settings.forecast_alerts}
                    onChange={(e) => setSettings({ ...settings, forecast_alerts: e.target.checked })}
                    className="accent-[#64BC45] rounded mt-1"
                  />
                </div>

                {/* 4. Daily Morning Brief */}
                <div className="p-3.5 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7] flex items-start justify-between space-x-3">
                  <div className="space-y-0.5">
                    <span className="text-xs font-bold text-[#263329] block">Daily Morning Air Brief</span>
                    <p className="text-[11px] text-[#788278]">
                      Consolidated metro average AQI, cleanest stations, and optimal outdoor activity windows.
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={settings.daily_morning_brief}
                    onChange={(e) => setSettings({ ...settings, daily_morning_brief: e.target.checked })}
                    className="accent-[#64BC45] rounded mt-1"
                  />
                </div>

                {/* 5. Commute Corridor Advisories */}
                <div className="p-3.5 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7] flex items-start justify-between space-x-3">
                  <div className="space-y-0.5">
                    <span className="text-xs font-bold text-[#263329] block">Commute Corridor Notices</span>
                    <p className="text-[11px] text-[#788278]">
                      Transit route warnings (Outer Ring Road, Silk Board) prompting cabin air recirculation.
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={settings.commute_window_alerts}
                    onChange={(e) => setSettings({ ...settings, commute_window_alerts: e.target.checked })}
                    className="accent-[#64BC45] rounded mt-1"
                  />
                </div>

                {/* 6. Improving Air Notices */}
                <div className="p-3.5 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7] flex items-start justify-between space-x-3">
                  <div className="space-y-0.5">
                    <span className="text-xs font-bold text-[#263329] block">Clean Air & Dispersion Notices</span>
                    <p className="text-[11px] text-[#788278]">
                      Confirmatory alerts when atmospheric dispersion returns air quality to safe thresholds.
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={settings.improving_air_alerts}
                    onChange={(e) => setSettings({ ...settings, improving_air_alerts: e.target.checked })}
                    className="accent-[#64BC45] rounded mt-1"
                  />
                </div>
              </div>

              {/* Deduplication & Technical Rules Note */}
              <div className="p-3.5 rounded-xl bg-[#F1F8ED] border border-[#C2EBBA] text-[11px] text-[#263329] space-y-1">
                <span className="font-bold text-[#469A36] block">Smart Alert Engine Rules:</span>
                <p>&bull; <strong>Deduplication Guard:</strong> Steady-state sensor readings are capped to prevent duplicate notification spam within a 60-minute cooldown window.</p>
                <p>&bull; <strong>CPCB Multi-Pollutant Standard:</strong> Overall AQI is derived from multi-pollutant breakpoints (PM2.5, PM10, NO2, SO2, CO, O3) and never computed from PM2.5 alone.</p>
                <p>&bull; <strong>Forecast vs Measurement:</strong> Forecast alerts are explicitly distinguished from real-time ground sensor measurements.</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: CPCB STANDARDS & SAFETY RECOMMENDATIONS GUIDE */}
      {activeSubTab === 'cpcb_guide' && cpcbData && (
        <div className="bg-white p-6 border border-[#E8ECE7] rounded-2xl space-y-6 shadow-xs">
          <div>
            <h2 className="text-base sm:text-lg font-black text-[#263329]">
              CPCB National Air Quality Index (NAQI) Standard Categories
            </h2>
            <p className="text-xs text-[#788278]">
              Official Indian Central Pollution Control Board categories and actionable safety recommendations
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {cpcbData.categories.map((cat) => (
              <div
                key={cat.category}
                className="p-4 rounded-2xl border space-y-2.5 bg-[#F5F7F4] border-[#E8ECE7] shadow-xs relative overflow-hidden"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span 
                      className="w-3 h-3 rounded-full" 
                      style={{ backgroundColor: cat.color }} 
                    />
                    <h3 className="text-sm font-black text-[#263329]">{cat.category}</h3>
                  </div>
                  <span className="text-xs font-mono font-bold px-2.5 py-0.5 rounded-md bg-white text-[#263329] border border-[#E8ECE7]">
                    AQI {cat.aqi_range}
                  </span>
                </div>

                <div className="space-y-1 pt-1">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-[#469A36] block">
                    CPCB Safety Guidance
                  </span>
                  <p className="text-xs text-[#263329] font-medium leading-relaxed">
                    {cat.base_recommendation}
                  </p>
                </div>

                {cat.personalized_guidance && (
                  <div className="pt-2 border-t border-[#E8ECE7] text-[11px] text-[#469A36] leading-tight">
                    <strong>For {cpcbData.active_persona.replace('_', ' ')}:</strong> {cat.personalized_guidance}
                  </div>
                )}

                {cat.sensitivity_note && (
                  <div className="text-[10px] text-rose-600 leading-tight">
                    {cat.sensitivity_note}
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Regulatory Non-Medical Disclaimer */}
          <div className="p-4 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7] text-xs text-[#788278] space-y-1">
            <span className="font-bold text-[#469A36] block">Non-Medical Advisory Disclaimer:</span>
            <p className="leading-relaxed">
              {cpcbData.disclaimer}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
