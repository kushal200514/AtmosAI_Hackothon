import React, { useState, useEffect } from 'react';
import { 
  X, 
  Check, 
  Save, 
  GraduationCap, 
  Footprints, 
  Briefcase, 
  Bike, 
  Baby, 
  Users, 
  ShieldAlert, 
  Sliders, 
  Languages, 
  MapPin, 
  Bell, 
  HeartPulse 
} from 'lucide-react';
import { updateUserProfile } from '../services/api';

const PERSONAS = [
  {
    id: 'student',
    title: 'Student',
    desc: 'Campus air quality, outdoor recreation, and pollution surge alerts.',
    icon: GraduationCap,
    defaultActivities: ['campus_walks', 'outdoor_sports', 'cycling', 'walking']
  },
  {
    id: 'runner',
    title: 'Runner / Athlete',
    desc: 'Workout-time forecasts, multi-horizon PM2.5 trends, and weather.',
    icon: Footprints,
    defaultActivities: ['running', 'cycling', 'walking']
  },
  {
    id: 'office_commuter',
    title: 'Office Commuter',
    desc: 'Morning/evening forecasts, corridor pollution, and transit alerts.',
    icon: Briefcase,
    defaultActivities: ['morning_transit', 'evening_transit', 'walking']
  },
  {
    id: 'outdoor_worker',
    title: 'Outdoor Worker',
    desc: 'Current pollution, hourly forecast, shift safety, and warnings.',
    icon: Bike,
    defaultActivities: ['street_deliveries', 'outdoor_shifts', 'walking']
  },
  {
    id: 'parent',
    title: 'Parent / Guardian',
    desc: 'Family outdoor conditions, cautious pediatric guidance, and safe hours.',
    icon: Baby,
    defaultActivities: ['playground_trips', 'stroller_walks', 'walking']
  },
  {
    id: 'general_public',
    title: 'General Public',
    desc: 'Current AQI, PM2.5, spatial maps, and general environmental insights.',
    icon: Users,
    defaultActivities: ['walking', 'cycling']
  }
];

const ALL_ACTIVITIES = [
  { id: 'running', label: 'Running / Jogging' },
  { id: 'cycling', label: 'Cycling' },
  { id: 'walking', label: 'Walking' },
  { id: 'campus_walks', label: 'Campus Transit' },
  { id: 'outdoor_sports', label: 'Outdoor Sports' },
  { id: 'playground_trips', label: 'Playground Visits' },
  { id: 'stroller_walks', label: 'Stroller Outings' },
  { id: 'morning_transit', label: 'Morning Commute' },
  { id: 'evening_transit', label: 'Evening Commute' },
  { id: 'street_deliveries', label: 'Street Deliveries' },
  { id: 'outdoor_shifts', label: 'Outdoor Work Shifts' }
];

export default function ProfileSettingsModal({ 
  isOpen, 
  onClose, 
  userProfile, 
  onProfileUpdated 
}) {
  if (!isOpen) return null;

  // Active form state initialized from profile
  const [formData, setFormData] = useState({
    full_name: userProfile?.full_name || 'Atmos Citizen',
    age_group: userProfile?.age_group || '26_45',
    city: userProfile?.city || 'Bengaluru',
    locality: userProfile?.locality || 'Central',
    preferred_language: userProfile?.preferred_language || 'en',
    user_category: userProfile?.user_category || 'general_public',
    outdoor_time_duration: userProfile?.outdoor_time_duration || '1_to_3h',
    preferred_activities: userProfile?.preferred_activities || ['walking', 'running'],
    sensitivity_preference: userProfile?.sensitivity_preference || 'none',
    notifications: {
      surge_warnings: userProfile?.notifications?.surge_warnings ?? true,
      daily_morning_brief: userProfile?.notifications?.daily_morning_brief ?? true,
      commute_window_alerts: userProfile?.notifications?.commute_window_alerts ?? true,
      high_pollution_threshold: userProfile?.notifications?.high_pollution_threshold || 100,
      improving_air_alerts: userProfile?.notifications?.improving_air_alerts ?? true
    }
  });

  const [saving, setSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  // Quick preset switcher
  const handleSelectPersona = (personaId) => {
    const found = PERSONAS.find(p => p.id === personaId);
    setFormData(prev => ({
      ...prev,
      user_category: personaId,
      preferred_activities: found ? found.defaultActivities : prev.preferred_activities
    }));
  };

  const toggleActivity = (actId) => {
    setFormData(prev => {
      const exists = prev.preferred_activities.includes(actId);
      const updated = exists 
        ? prev.preferred_activities.filter(a => a !== actId)
        : [...prev.preferred_activities, actId];
      return { ...prev, preferred_activities: updated };
    });
  };

  const handleSave = async (e) => {
    e?.preventDefault();
    setSaving(true);
    try {
      const res = await updateUserProfile(formData, userProfile?.id || 'default_user');
      setSavedSuccess(true);
      if (onProfileUpdated) {
        onProfileUpdated(res.profile, res.personalization);
      }
      setTimeout(() => {
        setSavedSuccess(false);
        onClose();
      }, 700);
    } catch (err) {
      console.error('Failed to save profile:', err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/40 backdrop-blur-md animate-fadeIn">
      <div className="w-full max-w-3xl max-h-[92vh] flex flex-col bg-white border border-[#E8ECE7] rounded-3xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 sm:p-5 border-b border-[#E8ECE7] bg-white">
          <div>
            <h2 className="text-base sm:text-lg font-extrabold text-[#263329] tracking-tight flex items-center space-x-2">
              <span>Personalization Profile Settings</span>
            </h2>
            <p className="text-xs text-[#788278]">
              Dynamically configures dashboard widgets, planner activities, alerts & AI assistant.
            </p>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-full bg-[#F5F7F4] hover:bg-[#E8ECE7] text-[#788278] hover:text-[#263329] transition cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Scrollable Form Body */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
          {/* 1. Core Persona Category */}
          <div className="space-y-2.5">
            <label className="text-xs font-bold uppercase tracking-wider text-[#469A36] flex items-center space-x-1.5">
              <Users className="w-3.5 h-3.5" />
              <span>Select Persona Archetype (Reorders Dashboard)</span>
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
              {PERSONAS.map(p => {
                const Icon = p.icon;
                const isSelected = formData.user_category === p.id;
                return (
                  <div
                    key={p.id}
                    onClick={() => handleSelectPersona(p.id)}
                    className={`p-3 rounded-xl border transition cursor-pointer flex flex-col justify-between space-y-1.5 ${
                      isSelected
                        ? 'bg-[#F1F8ED] border-[#64BC45] text-[#263329] shadow-sm ring-1 ring-[#64BC45]'
                        : 'bg-[#F5F7F4] border-[#E8ECE7] hover:border-[#C2EBBA] hover:bg-[#F1F8ED]/40 text-[#263329]'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <Icon className={`w-4 h-4 ${isSelected ? 'text-[#469A36]' : 'text-[#788278]'}`} />
                        <span className="text-xs font-bold text-[#263329]">{p.title}</span>
                      </div>
                      {isSelected && <Check className="w-3.5 h-3.5 text-[#469A36]" />}
                    </div>
                    <p className="text-[10px] text-[#788278] leading-tight line-clamp-2">
                      {p.desc}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* 2. Personal Lifestyle & Location */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2 border-t border-[#E8ECE7]">
            <div>
              <label className="text-[11px] font-semibold text-[#263329] block mb-1">
                Full Name
              </label>
              <input
                type="text"
                value={formData.full_name}
                onChange={e => setFormData({ ...formData, full_name: e.target.value })}
                className="w-full px-3 py-2 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7] text-xs text-[#263329] focus:outline-none focus:border-[#64BC45] focus:bg-white transition"
              />
            </div>

            <div>
              <label className="text-[11px] font-semibold text-[#263329] block mb-1">
                City / Locality
              </label>
              <div className="flex space-x-1.5">
                <input
                  type="text"
                  value={formData.city}
                  onChange={e => setFormData({ ...formData, city: e.target.value })}
                  className="w-1/2 px-2.5 py-2 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7] text-xs text-[#263329] focus:outline-none focus:border-[#64BC45] focus:bg-white transition"
                  placeholder="City"
                />
                <input
                  type="text"
                  value={formData.locality}
                  onChange={e => setFormData({ ...formData, locality: e.target.value })}
                  className="w-1/2 px-2.5 py-2 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7] text-xs text-[#263329] focus:outline-none focus:border-[#64BC45] focus:bg-white transition"
                  placeholder="Locality"
                />
              </div>
            </div>

            <div>
              <label className="text-[11px] font-semibold text-[#263329] block mb-1 flex items-center space-x-1">
                <Languages className="w-3 h-3 text-[#469A36]" />
                <span>Preferred Language</span>
              </label>
              <select
                value={formData.preferred_language}
                onChange={e => setFormData({ ...formData, preferred_language: e.target.value })}
                className="w-full px-3 py-2 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7] text-xs text-[#263329] focus:outline-none focus:border-[#64BC45] focus:bg-white transition"
              >
                <option value="en">English (Default)</option>
                <option value="hi">हिन्दी (Hindi)</option>
                <option value="kn">ಕನ್ನಡ (Kannada)</option>
              </select>
            </div>
          </div>

          {/* 3. Outdoor Duration & Health Sensitivity */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-[11px] font-semibold text-[#263329] block mb-1">
                Outdoor Exposure Duration
              </label>
              <select
                value={formData.outdoor_time_duration}
                onChange={e => setFormData({ ...formData, outdoor_time_duration: e.target.value })}
                className="w-full px-3 py-2 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7] text-xs text-[#263329] focus:outline-none focus:border-[#64BC45] focus:bg-white transition"
              >
                <option value="less_than_1h">Less than 1 Hour</option>
                <option value="1_to_3h">1 to 3 Hours</option>
                <option value="3_to_6h">3 to 6 Hours (High Exposure)</option>
                <option value="more_than_6h">More than 6 Hours (Continuous Shift)</option>
              </select>
            </div>

            <div>
              <label className="text-[11px] font-semibold text-[#263329] block mb-1 flex items-center space-x-1">
                <HeartPulse className="w-3 h-3 text-rose-500" />
                <span>Health Sensitivity Profile</span>
              </label>
              <select
                value={formData.sensitivity_preference}
                onChange={e => setFormData({ ...formData, sensitivity_preference: e.target.value })}
                className="w-full px-3 py-2 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7] text-xs text-[#263329] focus:outline-none focus:border-[#64BC45] focus:bg-white transition"
              >
                <option value="none">Standard / None</option>
                <option value="asthma_respiratory">Asthma / Respiratory Sensitivity</option>
                <option value="allergies">Airborne Pollen & Dust Allergies</option>
                <option value="elderly_child_care">Pediatric / Elderly Household</option>
                <option value="cardiovascular">Cardiovascular Caution</option>
              </select>
            </div>
          </div>

          {/* 4. Preferred Activities Selection */}
          <div className="space-y-2 pt-2 border-t border-[#E8ECE7]">
            <label className="text-xs font-bold uppercase tracking-wider text-[#469A36] block">
              Preferred Activities (Prioritizes Smart Planner)
            </label>
            <div className="flex flex-wrap gap-2">
              {ALL_ACTIVITIES.map(act => {
                const checked = formData.preferred_activities.includes(act.id);
                return (
                  <button
                    key={act.id}
                    type="button"
                    onClick={() => toggleActivity(act.id)}
                    className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition cursor-pointer flex items-center space-x-1.5 ${
                      checked
                        ? 'bg-[#F1F8ED] border border-[#64BC45] text-[#469A36]'
                        : 'bg-[#F5F7F4] border border-[#E8ECE7] text-[#788278] hover:border-[#C2EBBA] hover:text-[#263329]'
                    }`}
                  >
                    <span>{act.label}</span>
                    {checked && <Check className="w-3 h-3 text-[#469A36]" />}
                  </button>
                );
              })}
            </div>
          </div>

          {/* 5. Notification & Alert Customization */}
          <div className="space-y-3 pt-2 border-t border-[#E8ECE7]">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold uppercase tracking-wider text-[#469A36] flex items-center space-x-1.5">
                <Bell className="w-3.5 h-3.5" />
                <span>Alert Notification Matrix</span>
              </label>
              <span className="text-[11px] text-[#469A36] font-mono font-bold">
                Threshold: AQI &ge; {formData.notifications.high_pollution_threshold}
              </span>
            </div>

            <div className="space-y-2">
              <input
                type="range"
                min="40"
                max="250"
                step="5"
                value={formData.notifications.high_pollution_threshold}
                onChange={e => setFormData({
                  ...formData,
                  notifications: {
                    ...formData.notifications,
                    high_pollution_threshold: parseInt(e.target.value)
                  }
                })}
                className="w-full accent-[#64BC45] cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-[#788278] font-mono">
                <span>Strict (AQI 40)</span>
                <span>Moderate (AQI 100)</span>
                <span>Severe Only (AQI 200+)</span>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 pt-1">
              <label className="p-2.5 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7] flex items-center justify-between cursor-pointer">
                <span className="text-xs text-[#263329]">Surge Warnings</span>
                <input
                  type="checkbox"
                  checked={formData.notifications.surge_warnings}
                  onChange={e => setFormData({
                    ...formData,
                    notifications: { ...formData.notifications, surge_warnings: e.target.checked }
                  })}
                  className="rounded accent-[#64BC45]"
                />
              </label>

              <label className="p-2.5 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7] flex items-center justify-between cursor-pointer">
                <span className="text-xs text-[#263329]">Commute Corridor Alerts</span>
                <input
                  type="checkbox"
                  checked={formData.notifications.commute_window_alerts}
                  onChange={e => setFormData({
                    ...formData,
                    notifications: { ...formData.notifications, commute_window_alerts: e.target.checked }
                  })}
                  className="rounded accent-[#64BC45]"
                />
              </label>

              <label className="p-2.5 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7] flex items-center justify-between cursor-pointer">
                <span className="text-xs text-[#263329]">Clean Air Advisories</span>
                <input
                  type="checkbox"
                  checked={formData.notifications.improving_air_alerts}
                  onChange={e => setFormData({
                    ...formData,
                    notifications: { ...formData.notifications, improving_air_alerts: e.target.checked }
                  })}
                  className="rounded accent-[#64BC45]"
                />
              </label>
            </div>
          </div>
        </div>

        {/* Action Footer */}
        <div className="p-4 sm:p-5 border-t border-[#E8ECE7] bg-white flex items-center justify-between">
          <p className="text-[11px] text-[#788278] hidden sm:block">
            Updates dashboard layout & AI recommendations dynamically.
          </p>

          <div className="flex items-center space-x-3 w-full sm:w-auto justify-end">
            <button
              onClick={onClose}
              type="button"
              className="px-4 py-2 rounded-xl bg-[#F5F7F4] hover:bg-[#E8ECE7] text-[#788278] hover:text-[#263329] text-xs font-bold transition cursor-pointer"
            >
              Cancel
            </button>

            <button
              onClick={handleSave}
              disabled={saving}
              type="button"
              className={`px-5 py-2 rounded-xl text-xs font-bold flex items-center space-x-1.5 transition cursor-pointer shadow-sm ${
                savedSuccess
                  ? 'bg-[#469A36] text-white font-black'
                  : 'bg-[#64BC45] hover:bg-[#469A36] text-white'
              }`}
            >
              {savedSuccess ? (
                <>
                  <Check className="w-4 h-4 stroke-[3]" />
                  <span>Applied Live!</span>
                </>
              ) : saving ? (
                <span>Updating Engine...</span>
              ) : (
                <>
                  <Save className="w-4 h-4" />
                  <span>Save & Apply Personalization</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

