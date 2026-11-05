import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  Save, 
  Check, 
  LogOut
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const PERSONAS = [
  { id: 'student', title: 'Student', desc: 'Campus air quality & outdoor schedule focus' },
  { id: 'office_commuter', title: 'Office Commuter', desc: 'Corridor transit & rush hour guidance' },
  { id: 'runner', title: 'Runner / Athlete', desc: 'Workout windows & PM2.5 multi-horizon trends' },
  { id: 'cyclist', title: 'Cyclist', desc: 'On-road wind & particulate exposure' },
  { id: 'outdoor_worker', title: 'Outdoor / Delivery Worker', desc: 'Extended shift safety & deterioration warnings' },
  { id: 'parent', title: 'Parent / Guardian', desc: 'Pediatric air quality & playground safe hours' },
  { id: 'general_public', title: 'General Public', desc: 'Daily CPCB NAQI & standard ventilation advice' }
];

const BENGALURU_LOCATIONS = [
  { slug: 'bengaluru_central', label: 'Bengaluru Central (City Station)' },
  { slug: 'silk_board', label: 'Central Silk Board (Hosur Rd)' },
  { slug: 'electronic_city', label: 'Electronic City Phase 1' },
  { slug: 'hebbal', label: 'Hebbal Flyover (Outer Ring Rd)' },
  { slug: 'koramangala', label: 'Koramangala 4th Block' },
  { slug: 'peenya', label: 'Peenya Industrial Area' },
  { slug: 'yelahanka', label: 'Yelahanka Satellite Town' }
];

export default function ProfilePage() {
  const navigate = useNavigate();
  const { user, profile, updateProfileData, signOut } = useAuth();

  const [fullName, setFullName] = useState(profile?.full_name || '');
  const [email] = useState(user?.email || profile?.email || '');
  const [city, setCity] = useState(profile?.city || 'Bengaluru');
  const [locality, setLocality] = useState(profile?.locality || 'Central');
  const [language, setLanguage] = useState(profile?.preferred_language || 'en');
  const [userCategory, setUserCategory] = useState(profile?.user_category || 'general_public');
  const [primaryLocation, setPrimaryLocation] = useState(profile?.primary_location || 'bengaluru_central');
  const [sensitivity, setSensitivity] = useState(profile?.sensitivity_preference || 'none');
  const [alertThreshold, setAlertThreshold] = useState(profile?.notifications?.high_pollution_threshold || 101);

  const [saving, setSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState(null);

  useEffect(() => {
    if (profile) {
      setFullName(profile.full_name || '');
      setCity(profile.city || 'Bengaluru');
      setLocality(profile.locality || 'Central');
      setLanguage(profile.preferred_language || 'en');
      setUserCategory(profile.user_category || 'general_public');
      setPrimaryLocation(profile.primary_location || 'bengaluru_central');
      setSensitivity(profile.sensitivity_preference || 'none');
      if (profile.notifications?.high_pollution_threshold) {
        setAlertThreshold(profile.notifications.high_pollution_threshold);
      }
    }
  }, [profile]);

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setSuccessMsg(null);
    try {
      await updateProfileData({
        full_name: fullName,
        city,
        locality,
        preferred_language: language,
        user_category: userCategory,
        primary_location: primaryLocation,
        sensitivity_preference: sensitivity,
        notifications: {
          high_pollution_threshold: alertThreshold
        }
      });
      setSuccessMsg('Profile updated! Dashboard personalization refreshed.');
      setTimeout(() => setSuccessMsg(null), 3000);
    } catch (err) {
      console.error('Failed to update profile:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleLogout = async () => {
    await signOut();
    navigate('/welcome', { replace: true });
  };

  return (
    <div className="min-h-screen bg-[#F5F7F4] text-[#263329] font-sans selection:bg-[#64BC45] selection:text-white py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto space-y-6">
        {/* Top Header Bar */}
        <div className="flex items-center justify-between">
          <button
            type="button"
            onClick={() => navigate('/dashboard')}
            className="flex items-center space-x-1.5 text-xs font-bold text-[#469A36] hover:text-[#263329] p-2 rounded-xl hover:bg-white transition cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Dashboard</span>
          </button>

          <button
            type="button"
            onClick={handleLogout}
            className="flex items-center space-x-1.5 text-xs font-bold text-red-600 hover:text-red-700 p-2 rounded-xl hover:bg-red-50 border border-transparent hover:border-red-200 transition cursor-pointer"
          >
            <LogOut className="w-4 h-4" />
            <span>Sign Out</span>
          </button>
        </div>

        {/* Profile Card */}
        <div className="bg-white rounded-3xl border border-[#E8ECE7] p-6 sm:p-10 shadow-xs">
          <div className="flex items-center space-x-3 pb-6 border-b border-[#E8ECE7]">
            <div className="w-12 h-12 rounded-2xl bg-[#F1F8ED] border border-[#C2EBBA] text-[#469A36] flex items-center justify-center font-bold text-lg">
              {fullName ? fullName.charAt(0).toUpperCase() : 'A'}
            </div>
            <div>
              <h1 className="text-xl font-black text-[#263329]">Profile & Personalization Settings</h1>
              <p className="text-xs text-[#788278]">{email} &bull; AtmosAI Account</p>
            </div>
          </div>

          {successMsg && (
            <div className="mt-4 p-3.5 rounded-2xl bg-[#F1F8ED] border border-[#C2EBBA] text-[#469A36] text-xs font-bold flex items-center space-x-2">
              <Check className="w-4 h-4 flex-shrink-0" />
              <span>{successMsg}</span>
            </div>
          )}

          <form onSubmit={handleSave} className="mt-6 space-y-6">
            {/* Personal Details */}
            <div>
              <h3 className="text-xs font-bold text-[#263329] uppercase tracking-wider mb-3">
                1. Personal Information
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-[#788278] mb-1">Full Name</label>
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl border border-[#E8ECE7] bg-[#F5F7F4]/50 focus:bg-white text-sm text-[#263329] focus:outline-none focus:border-[#64BC45]"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-[#788278] mb-1">Language</label>
                  <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl border border-[#E8ECE7] bg-[#F5F7F4]/50 focus:bg-white text-sm text-[#263329] focus:outline-none focus:border-[#64BC45]"
                  >
                    <option value="en">English</option>
                    <option value="kn">Kannada (ಕನ್ನಡ)</option>
                    <option value="hi">Hindi (हिन्दी)</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Lifestyle Category */}
            <div>
              <h3 className="text-xs font-bold text-[#263329] uppercase tracking-wider mb-3">
                2. Lifestyle Category (Affects Dashboard Widget Priorities)
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                {PERSONAS.map(p => {
                  const isSelected = userCategory === p.id;
                  return (
                    <div
                      key={p.id}
                      onClick={() => setUserCategory(p.id)}
                      className={`p-3 rounded-2xl border text-xs cursor-pointer transition ${
                        isSelected 
                          ? 'border-[#64BC45] bg-[#F1F8ED] shadow-xs' 
                          : 'border-[#E8ECE7] bg-white hover:border-[#C2EBBA]'
                      }`}
                    >
                      <div className="flex items-center justify-between font-bold text-[#263329]">
                        <span>{p.title}</span>
                        {isSelected && <Check className="w-3.5 h-3.5 text-[#469A36]" />}
                      </div>
                      <p className="text-[11px] text-[#788278] mt-1">{p.desc}</p>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Primary Location */}
            <div>
              <h3 className="text-xs font-bold text-[#263329] uppercase tracking-wider mb-3">
                3. Primary Monitoring Location
              </h3>
              <select
                value={primaryLocation}
                onChange={(e) => setPrimaryLocation(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl border border-[#E8ECE7] bg-[#F5F7F4]/50 focus:bg-white text-sm text-[#263329] focus:outline-none focus:border-[#64BC45]"
              >
                {BENGALURU_LOCATIONS.map(loc => (
                  <option key={loc.slug} value={loc.slug}>{loc.label}</option>
                ))}
              </select>
            </div>

            {/* Notification Threshold */}
            <div>
              <h3 className="text-xs font-bold text-[#263329] uppercase tracking-wider mb-3">
                4. CPCB Alert Threshold (NAQI)
              </h3>
              <div className="p-4 rounded-2xl bg-[#F1F8ED] border border-[#C2EBBA]">
                <div className="flex items-center justify-between text-xs font-bold text-[#263329] mb-1">
                  <span>High Pollution Alert Trigger</span>
                  <span className="text-[#469A36] font-mono">{alertThreshold} AQI</span>
                </div>
                <input
                  type="range"
                  min="51"
                  max="300"
                  step="10"
                  value={alertThreshold}
                  onChange={(e) => setAlertThreshold(parseInt(e.target.value))}
                  className="w-full accent-[#64BC45]"
                />
              </div>
            </div>

            {/* Submit */}
            <div className="pt-4 border-t border-[#E8ECE7] flex justify-end">
              <button
                type="submit"
                disabled={saving}
                className="px-6 py-2.5 rounded-xl bg-[#64BC45] hover:bg-[#469A36] text-white text-xs font-bold shadow-sm shadow-[#64BC45]/25 transition flex items-center space-x-2 cursor-pointer disabled:opacity-50"
              >
                {saving ? (
                  <>
                    <Clock className="w-3.5 h-3.5 animate-spin" />
                    <span>Saving Changes...</span>
                  </>
                ) : (
                  <>
                    <Save className="w-3.5 h-3.5" />
                    <span>Save Preferences & Update Dashboard</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
