import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Wind, 
  ArrowRight, 
  ArrowLeft, 
  Check, 
  CheckCircle2, 
  GraduationCap, 
  Briefcase, 
  Footprints, 
  Bike, 
  Truck, 
  Users, 
  Baby, 
  Bell, 
  Compass, 
  Clock, 
  Sparkles,
  HeartPulse
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const LIFESTYLE_CATEGORIES = [
  {
    id: 'student',
    title: 'Student',
    subtitle: 'Campus air quality, walking & outdoor schedules',
    icon: GraduationCap,
    desc: 'Prioritizes campus air quality, walking between lectures, sports, and outdoor study windows.'
  },
  {
    id: 'office_commuter',
    title: 'Office Commuter',
    subtitle: 'Corridor transit, morning/evening rush alerts',
    icon: Briefcase,
    desc: 'Prioritizes corridor transit pollution, optimal commute departure windows, and saved office routes.'
  },
  {
    id: 'runner',
    title: 'Runner / Athlete',
    subtitle: 'Workout PM2.5 forecasts & training windows',
    icon: Footprints,
    desc: 'Prioritizes exercise suitability scores, multi-horizon PM2.5 trends, and early morning running conditions.'
  },
  {
    id: 'cyclist',
    title: 'Cyclist',
    subtitle: 'Route wind & road-level particulate exposure',
    icon: Bike,
    desc: 'Prioritizes on-road PM2.5 exposure, wind vectors, and safe cycling commute hours.'
  },
  {
    id: 'outdoor_worker',
    title: 'Outdoor / Delivery Worker',
    subtitle: 'Shift exposure, surge warnings & peak alerts',
    icon: Truck,
    desc: 'Prioritizes shift safety, street-level air deterioration, and sustained outdoor protective advisories.'
  },
  {
    id: 'parent',
    title: 'Parent / Guardian',
    subtitle: 'Pediatric care, school transit & playground safety',
    icon: Baby,
    desc: 'Prioritizes safe playground times, school run air quality, and sensitive lung protection for children.'
  },
  {
    id: 'general_public',
    title: 'General Public',
    subtitle: 'Standard AQI, daily weather & ventilation advice',
    icon: Users,
    desc: 'Prioritizes general CPCB NAQI, PM2.5 levels, home ventilation windows, and standard forecasts.'
  }
];

const DAILY_ACTIVITIES = [
  { id: 'walking', label: 'Walking / Strolling' },
  { id: 'running', label: 'Running / Jogging' },
  { id: 'cycling', label: 'Cycling' },
  { id: 'outdoor_sports', label: 'Outdoor Sports / Training' },
  { id: 'commuting', label: 'Daily Commuting' },
  { id: 'outdoor_work', label: 'Outdoor Work / Field Transit' },
  { id: 'family_outdoor', label: 'Family Outdoor Activities' }
];

const OUTDOOR_TIMES = [
  { id: 'less_than_1h', label: 'Less than 1 hour' },
  { id: '1_to_3h', label: '1–3 hours' },
  { id: '3_to_6h', label: '3–6 hours' },
  { id: 'more_than_6h', label: 'More than 6 hours' }
];

const PRIORITIES = [
  { id: 'pm25_focus', label: 'General Air Quality & PM2.5 Monitoring' },
  { id: 'exercise_focus', label: 'Outdoor Exercise & Training Recommendations' },
  { id: 'commute_focus', label: 'Commuting & Transit Corridor Conditions' },
  { id: 'family_focus', label: 'Family & Children Outdoor Safety' },
  { id: 'deterioration_alerts', label: 'Sudden Pollution Deterioration Alerts' }
];

const SENSITIVITY_OPTIONS = [
  { id: 'none', label: 'Standard Environmental Sensitivity (None)' },
  { id: 'asthma_respiratory', label: 'Mild to Moderate Respiratory Sensitivity' },
  { id: 'allergies', label: 'Seasonal Air Pollen & Particulate Allergies' },
  { id: 'elderly_child_care', label: 'Caring for Young Children or Elderly Family' },
  { id: 'cardiovascular', label: 'Elevated Sensitivity to Strenuous Air Exertion' }
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

export default function OnboardingPage() {
  const navigate = useNavigate();
  const { user, profile, updateProfileData, saveOnboarding } = useAuth();

  // Wizard Step State (1 through 5)
  const [currentStep, setCurrentStep] = useState(profile?.onboarding_step || 1);
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState(null);

  // Form State
  const [fullName, setFullName] = useState(profile?.full_name || user?.full_name || '');
  const [ageGroup, setAgeGroup] = useState(profile?.age_group || '26_45');
  const [city, setCity] = useState(profile?.city || 'Bengaluru');
  const [locality, setLocality] = useState(profile?.locality || 'Central');
  const [preferredLanguage, setPreferredLanguage] = useState(profile?.preferred_language || 'en');

  // Step 2
  const [userCategory, setUserCategory] = useState(profile?.user_category || 'general_public');

  // Step 3
  const [preferredActivities, setPreferredActivities] = useState(
    profile?.preferred_activities || ['walking', 'commuting']
  );
  const [outdoorTime, setOutdoorTime] = useState(
    profile?.outdoor_time_duration || '1_to_3h'
  );

  // Step 4
  const [environmentalPreferences, setEnvironmentalPreferences] = useState(
    profile?.environmental_info_preferences || ['pm25_focus', 'deterioration_alerts']
  );
  const [sensitivity, setSensitivity] = useState(
    profile?.sensitivity_preference || 'none'
  );

  // Step 5
  const [primaryLocation, setPrimaryLocation] = useState(
    profile?.primary_location || 'bengaluru_central'
  );
  const [manualLocation, setManualLocation] = useState('');
  const [gpsStatus, setGpsStatus] = useState(null);

  const [enableNotifications, setEnableNotifications] = useState(true);
  const [alertThreshold, setAlertThreshold] = useState(
    profile?.notifications?.high_pollution_threshold || 101
  );
  const [activeAlertTypes, setActiveAlertTypes] = useState({
    threshold_crossing_alerts: true,
    deterioration_alerts: true,
    surge_warnings: true,
    daily_morning_brief: true,
    commute_window_alerts: true,
    improving_air_alerts: true
  });

  // Sync if profile loads late
  useEffect(() => {
    if (profile) {
      if (profile.onboarding_step && !currentStep) {
        setCurrentStep(profile.onboarding_step);
      }
      if (profile.full_name && !fullName) setFullName(profile.full_name);
      if (profile.user_category) setUserCategory(profile.user_category);
    }
  }, [profile]);

  // Activity toggle helper
  const toggleActivity = (id) => {
    setPreferredActivities(prev => 
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  // Preference toggle helper
  const togglePreference = (id) => {
    setEnvironmentalPreferences(prev => 
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  // GPS Simulation / Browser Geolocation
  const handleGPSDetect = () => {
    setGpsStatus('Requesting coordinates...');
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setGpsStatus(`GPS detected: ${pos.coords.latitude.toFixed(4)}°N, ${pos.coords.longitude.toFixed(4)}°E (Assigned nearest: Bengaluru Central)`);
          setPrimaryLocation('bengaluru_central');
        },
        () => {
          // Fallback demo GPS simulation
          setGpsStatus('Demo GPS fallback assigned: Bengaluru Central (12.9716°N, 77.5946°E)');
          setPrimaryLocation('bengaluru_central');
        },
        { timeout: 4000 }
      );
    } else {
      setGpsStatus('Demo GPS assigned: Bengaluru Central');
      setPrimaryLocation('bengaluru_central');
    }
  };

  // Intermediate step save (preserves progress if user exits midway)
  const saveProgress = async (nextStep) => {
    setSaving(true);
    try {
      const payload = {
        full_name: fullName,
        age_group: ageGroup,
        city,
        locality,
        preferred_language: preferredLanguage,
        user_category: userCategory,
        preferred_activities: preferredActivities,
        outdoor_time_duration: outdoorTime,
        environmental_info_preferences: environmentalPreferences,
        sensitivity_preference: sensitivity,
        primary_location: manualLocation.trim() || primaryLocation,
        onboarding_step: nextStep,
        onboarding_completed: false
      };
      await updateProfileData(payload);
      setSaveMessage('Progress saved');
      setTimeout(() => setSaveMessage(null), 2000);
    } catch (err) {
      console.warn('Progress save notice:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleNext = async () => {
    if (currentStep < 5) {
      const next = currentStep + 1;
      await saveProgress(next);
      setCurrentStep(next);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } else {
      await handleCompleteOnboarding();
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(prev => prev - 1);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const handleCompleteOnboarding = async () => {
    setSaving(true);
    try {
      const payload = {
        full_name: fullName || 'Atmos Citizen',
        age_group: ageGroup,
        city: city || 'Bengaluru',
        locality: locality || 'Central',
        preferred_language: preferredLanguage,
        user_category: userCategory,
        preferred_activities: preferredActivities,
        outdoor_time_duration: outdoorTime,
        environmental_info_preferences: environmentalPreferences,
        sensitivity_preference: sensitivity,
        primary_location: manualLocation.trim() || primaryLocation,
        notifications: {
          high_pollution_threshold: alertThreshold,
          use_recommended_threshold: true,
          threshold_crossing_alerts: enableNotifications && activeAlertTypes.threshold_crossing_alerts,
          deterioration_alerts: enableNotifications && activeAlertTypes.deterioration_alerts,
          forecast_alerts: enableNotifications,
          surge_warnings: enableNotifications && activeAlertTypes.surge_warnings,
          daily_morning_brief: enableNotifications && activeAlertTypes.daily_morning_brief,
          commute_window_alerts: enableNotifications && activeAlertTypes.commute_window_alerts,
          improving_air_alerts: enableNotifications && activeAlertTypes.improving_air_alerts
        },
        onboarding_step: 5,
        onboarding_completed: true
      };

      if (saveOnboarding) {
        await saveOnboarding({
          full_name: fullName || 'Atmos Citizen',
          age_group: ageGroup,
          city: city || 'Bengaluru',
          locality: locality || 'Central',
          preferred_language: preferredLanguage,
          lifestyle_category: userCategory,
          activities: preferredActivities,
          outdoor_time: outdoorTime,
          environmental_preferences: environmentalPreferences,
          sensitivity_preference: sensitivity,
          notifications: {
            high_pollution_threshold: alertThreshold,
            use_recommended_threshold: true,
            threshold_crossing_alerts: enableNotifications && activeAlertTypes.threshold_crossing_alerts,
            deterioration_alerts: enableNotifications && activeAlertTypes.deterioration_alerts,
            forecast_alerts: enableNotifications,
            surge_warnings: enableNotifications && activeAlertTypes.surge_warnings,
            daily_morning_brief: enableNotifications && activeAlertTypes.daily_morning_brief,
            commute_window_alerts: enableNotifications && activeAlertTypes.commute_window_alerts,
            improving_air_alerts: enableNotifications && activeAlertTypes.improving_air_alerts
          },
          aqi_alert_threshold: alertThreshold,
          primary_location: manualLocation.trim() || primaryLocation,
          onboarding_completed: true,
          onboarding_step: 5
        });
      } else {
        await updateProfileData(payload);
      }
      // Seamlessly navigate to the personalized dashboard
      navigate('/dashboard', { replace: true });
    } catch (err) {
      console.error('Failed to complete onboarding:', err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F5F7F4] text-[#263329] font-sans selection:bg-[#64BC45] selection:text-white py-10 px-4 sm:px-6 lg:px-8 flex flex-col justify-between">
      <div className="max-w-2xl mx-auto w-full">
        {/* Brand Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center space-x-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-[#469A36] to-[#64BC45] flex items-center justify-center text-white shadow-xs">
              <Wind className="w-5 h-5 stroke-[2.2]" />
            </div>
            <div>
              <span className="text-xl font-black text-[#263329]">Atmos<span className="text-[#64BC45]">AI</span></span>
              <span className="hidden sm:inline-block ml-2 text-xs text-[#788278] font-medium">&bull; Personalization Wizard</span>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {saveMessage && (
              <span className="text-[11px] font-bold text-[#469A36] flex items-center space-x-1 animate-fade-in">
                <Check className="w-3.5 h-3.5" />
                <span>{saveMessage}</span>
              </span>
            )}
            <span className="text-xs font-bold font-mono px-3 py-1 rounded-full bg-[#F1F8ED] border border-[#C2EBBA] text-[#469A36]">
              Step {currentStep} of 5
            </span>
          </div>
        </div>

        {/* Step Progress Bar */}
        <div className="w-full bg-[#E8ECE7] h-2 rounded-full overflow-hidden mb-8">
          <div 
            className="bg-[#64BC45] h-full transition-all duration-300 ease-out rounded-full"
            style={{ width: `${(currentStep / 5) * 100}%` }}
          />
        </div>

        {/* Wizard Step Cards Container */}
        <div className="bg-white rounded-3xl border border-[#E8ECE7] p-6 sm:p-10 shadow-xs">
          
          {/* STEP 1: Basic Information */}
          {currentStep === 1 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-2xl font-black text-[#263329] tracking-tight">Basic Information</h2>
                <p className="mt-1 text-xs text-[#788278]">
                  Help AtmosAI personalize your local environmental context and display preferences.
                </p>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-[#263329] mb-1.5 uppercase tracking-wider">
                    Full Name
                  </label>
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Your Name"
                    className="w-full px-4 py-2.5 rounded-xl border border-[#E8ECE7] bg-[#F5F7F4]/50 focus:bg-white text-sm text-[#263329] focus:outline-none focus:border-[#64BC45]"
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold text-[#263329] mb-1.5 uppercase tracking-wider">
                      City
                    </label>
                    <input
                      type="text"
                      value={city}
                      onChange={(e) => setCity(e.target.value)}
                      placeholder="e.g. Bengaluru"
                      className="w-full px-4 py-2.5 rounded-xl border border-[#E8ECE7] bg-[#F5F7F4]/50 focus:bg-white text-sm text-[#263329] focus:outline-none focus:border-[#64BC45]"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-[#263329] mb-1.5 uppercase tracking-wider">
                      Locality / Neighborhood
                    </label>
                    <input
                      type="text"
                      value={locality}
                      onChange={(e) => setLocality(e.target.value)}
                      placeholder="e.g. Indiranagar, HSR, Whitefield"
                      className="w-full px-4 py-2.5 rounded-xl border border-[#E8ECE7] bg-[#F5F7F4]/50 focus:bg-white text-sm text-[#263329] focus:outline-none focus:border-[#64BC45]"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold text-[#263329] mb-1.5 uppercase tracking-wider">
                      Age Group (Optional)
                    </label>
                    <select
                      value={ageGroup}
                      onChange={(e) => setAgeGroup(e.target.value)}
                      className="w-full px-4 py-2.5 rounded-xl border border-[#E8ECE7] bg-[#F5F7F4]/50 focus:bg-white text-sm text-[#263329] focus:outline-none focus:border-[#64BC45]"
                    >
                      <option value="under_18">Under 18</option>
                      <option value="18_25">18–25 years</option>
                      <option value="26_45">26–45 years</option>
                      <option value="46_65">46–65 years</option>
                      <option value="65_plus">65+ years</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-[#263329] mb-1.5 uppercase tracking-wider">
                      Preferred Language
                    </label>
                    <select
                      value={preferredLanguage}
                      onChange={(e) => setPreferredLanguage(e.target.value)}
                      className="w-full px-4 py-2.5 rounded-xl border border-[#E8ECE7] bg-[#F5F7F4]/50 focus:bg-white text-sm text-[#263329] focus:outline-none focus:border-[#64BC45]"
                    >
                      <option value="en">English (Default)</option>
                      <option value="kn">Kannada (ಕನ್ನಡ)</option>
                      <option value="hi">Hindi (हिन्दी)</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* STEP 2: Lifestyle Category */}
          {currentStep === 2 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-2xl font-black text-[#263329] tracking-tight">Select Your Lifestyle</h2>
                <p className="mt-1 text-xs text-[#788278]">
                  Select the primary lens through which AtmosAI prioritizes your dashboard widgets and forecasts.
                </p>
              </div>

              <div className="grid grid-cols-1 gap-3">
                {LIFESTYLE_CATEGORIES.map(cat => {
                  const Icon = cat.icon;
                  const isSelected = userCategory === cat.id;
                  return (
                    <div
                      key={cat.id}
                      onClick={() => setUserCategory(cat.id)}
                      className={`p-4 rounded-2xl border transition-all cursor-pointer flex items-start space-x-3.5 ${
                        isSelected 
                          ? 'border-[#64BC45] bg-[#F1F8ED] shadow-xs' 
                          : 'border-[#E8ECE7] bg-white hover:border-[#C2EBBA] hover:bg-[#F5F7F4]/50'
                      }`}
                    >
                      <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${
                        isSelected 
                          ? 'bg-[#64BC45] text-white shadow-xs' 
                          : 'bg-[#F5F7F4] text-[#469A36]'
                      }`}>
                        <Icon className="w-5 h-5" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <h4 className="text-sm font-bold text-[#263329]">{cat.title}</h4>
                          {isSelected && <CheckCircle2 className="w-4 h-4 text-[#469A36]" />}
                        </div>
                        <p className="text-xs font-semibold text-[#469A36] mt-0.5">{cat.subtitle}</p>
                        <p className="text-[11px] text-[#788278] mt-1 leading-relaxed">{cat.desc}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* STEP 3: Daily Activities & Outdoor Duration */}
          {currentStep === 3 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-2xl font-black text-[#263329] tracking-tight">Daily Activities</h2>
                <p className="mt-1 text-xs text-[#788278]">
                  Tell us about your outdoor habits to calibrate hourly activity planning scores.
                </p>
              </div>

              {/* Multi-select Activities */}
              <div>
                <label className="block text-xs font-bold text-[#263329] mb-2 uppercase tracking-wider">
                  Select Outdoor Activities (Multiple)
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                  {DAILY_ACTIVITIES.map(act => {
                    const isSelected = preferredActivities.includes(act.id);
                    return (
                      <button
                        key={act.id}
                        type="button"
                        onClick={() => toggleActivity(act.id)}
                        className={`p-3 rounded-xl border text-xs font-bold text-left flex items-center justify-between transition cursor-pointer ${
                          isSelected
                            ? 'border-[#64BC45] bg-[#F1F8ED] text-[#263329]'
                            : 'border-[#E8ECE7] bg-white text-[#788278] hover:border-[#C2EBBA]'
                        }`}
                      >
                        <span>{act.label}</span>
                        {isSelected && <Check className="w-4 h-4 text-[#469A36]" />}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Outdoor Time Duration */}
              <div className="pt-2">
                <label className="block text-xs font-bold text-[#263329] mb-2 uppercase tracking-wider">
                  Approximately how much time do you spend outdoors daily?
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {OUTDOOR_TIMES.map(dur => {
                    const isSelected = outdoorTime === dur.id;
                    return (
                      <button
                        key={dur.id}
                        type="button"
                        onClick={() => setOutdoorTime(dur.id)}
                        className={`py-3 px-2 rounded-xl border text-xs font-bold text-center transition cursor-pointer ${
                          isSelected
                            ? 'border-[#64BC45] bg-[#64BC45] text-white shadow-xs'
                            : 'border-[#E8ECE7] bg-white text-[#263329] hover:bg-[#F5F7F4]'
                        }`}
                      >
                        {dur.label}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {/* STEP 4: Environmental Preferences & Sensitivities */}
          {currentStep === 4 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-2xl font-black text-[#263329] tracking-tight">Environmental Preferences</h2>
                <p className="mt-1 text-xs text-[#788278]">
                  Select the aspects you care about most and indicate optional sensitivities (non-medical).
                </p>
              </div>

              {/* Priority areas */}
              <div>
                <label className="block text-xs font-bold text-[#263329] mb-2 uppercase tracking-wider">
                  What should AtmosAI prioritize for you?
                </label>
                <div className="space-y-2">
                  {PRIORITIES.map(pri => {
                    const isSelected = environmentalPreferences.includes(pri.id);
                    return (
                      <div
                        key={pri.id}
                        onClick={() => togglePreference(pri.id)}
                        className={`p-3 rounded-xl border text-xs font-medium cursor-pointer flex items-center justify-between transition ${
                          isSelected
                            ? 'border-[#64BC45] bg-[#F1F8ED] text-[#263329]'
                            : 'border-[#E8ECE7] bg-white text-[#788278] hover:border-[#C2EBBA]'
                        }`}
                      >
                        <span>{pri.label}</span>
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => {}}
                          className="w-4 h-4 rounded text-[#64BC45] focus:ring-[#64BC45]"
                        />
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Sensitivity preferences */}
              <div className="pt-2">
                <div className="flex items-center space-x-2 mb-1.5">
                  <HeartPulse className="w-4 h-4 text-[#469A36]" />
                  <label className="block text-xs font-bold text-[#263329] uppercase tracking-wider">
                    Optional Environmental Sensitivity Preference
                  </label>
                </div>
                <p className="text-[11px] text-[#788278] mb-2.5">
                  We use cautious guidance parameters based on CPCB categories without asking for medical diagnoses.
                </p>
                <select
                  value={sensitivity}
                  onChange={(e) => setSensitivity(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-[#E8ECE7] bg-[#F5F7F4]/50 focus:bg-white text-sm text-[#263329] focus:outline-none focus:border-[#64BC45]"
                >
                  {SENSITIVITY_OPTIONS.map(opt => (
                    <option key={opt.id} value={opt.id}>{opt.label}</option>
                  ))}
                </select>
              </div>
            </div>
          )}

          {/* STEP 5: Location & Notifications */}
          {currentStep === 5 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-2xl font-black text-[#263329] tracking-tight">Location & Notifications</h2>
                <p className="mt-1 text-xs text-[#788278]">
                  Set your primary monitoring location and configure proactive pollution threshold warnings.
                </p>
              </div>

              {/* Primary Location Selection */}
              <div>
                <label className="block text-xs font-bold text-[#263329] mb-1.5 uppercase tracking-wider">
                  Primary Monitoring Location
                </label>
                <select
                  value={primaryLocation}
                  onChange={(e) => setPrimaryLocation(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-[#E8ECE7] bg-[#F5F7F4]/50 focus:bg-white text-sm text-[#263329] focus:outline-none focus:border-[#64BC45]"
                >
                  {BENGALURU_LOCATIONS.map(loc => (
                    <option key={loc.slug} value={loc.slug}>{loc.label}</option>
                  ))}
                </select>

                <div className="mt-2 flex items-center justify-between text-xs">
                  <button
                    type="button"
                    onClick={handleGPSDetect}
                    className="inline-flex items-center space-x-1 text-[#469A36] font-bold hover:underline cursor-pointer"
                  >
                    <Compass className="w-3.5 h-3.5" />
                    <span>Detect Nearest via GPS</span>
                  </button>
                  <span className="text-[#788278] text-[11px] font-mono">CPCB Bengaluru Network</span>
                </div>
                {gpsStatus && (
                  <p className="mt-1.5 text-[11px] text-[#469A36] font-mono bg-[#F1F8ED] p-2 rounded-lg border border-[#C2EBBA]">
                    {gpsStatus}
                  </p>
                )}
              </div>

              {/* Notification Toggles */}
              <div className="pt-2 border-t border-[#E8ECE7]">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    <Bell className="w-4 h-4 text-[#469A36]" />
                    <span className="text-xs font-bold text-[#263329] uppercase tracking-wider">
                      Proactive Air Alerts
                    </span>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={enableNotifications}
                      onChange={(e) => setEnableNotifications(e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-9 h-5 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-[#64BC45]" />
                  </label>
                </div>

                {enableNotifications && (
                  <div className="space-y-4 pt-1">
                    {/* AQI Alert Threshold */}
                    <div className="p-4 rounded-2xl bg-[#F1F8ED] border border-[#C2EBBA]">
                      <div className="flex items-center justify-between text-xs font-bold text-[#263329] mb-1">
                        <span>Alert Threshold (CPCB NAQI)</span>
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
                      <div className="flex justify-between text-[10px] text-[#788278] font-mono mt-1">
                        <span>Satisfactory (100)</span>
                        <span className="font-bold text-[#469A36]">Moderate (101) &bull; Recommended</span>
                        <span>Poor (201)</span>
                      </div>
                    </div>

                    {/* Specific alert categories */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                      {[
                        { key: 'threshold_crossing_alerts', label: 'Threshold Exceedance' },
                        { key: 'deterioration_alerts', label: 'Rapid Deterioration' },
                        { key: 'surge_warnings', label: 'Peak Hour Surges' },
                        { key: 'daily_morning_brief', label: 'Daily Morning Brief (7 AM)' },
                        { key: 'commute_window_alerts', label: 'Commute Window Guidance' },
                        { key: 'improving_air_alerts', label: 'Air Improvement Opportunity' }
                      ].map(item => (
                        <label key={item.key} className="flex items-center space-x-2 p-2 rounded-lg bg-[#F5F7F4] hover:bg-white border border-[#E8ECE7] cursor-pointer">
                          <input
                            type="checkbox"
                            checked={activeAlertTypes[item.key]}
                            onChange={(e) => setActiveAlertTypes({
                              ...activeAlertTypes,
                              [item.key]: e.target.checked
                            })}
                            className="w-4 h-4 rounded text-[#64BC45] focus:ring-[#64BC45]"
                          />
                          <span className="text-[11px] text-[#263329] font-medium">{item.label}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Navigation Controls (Back / Continue) */}
          <div className="mt-8 pt-5 border-t border-[#E8ECE7] flex items-center justify-between">
            {currentStep > 1 ? (
              <button
                type="button"
                onClick={handleBack}
                disabled={saving}
                className="px-5 py-2.5 rounded-xl border border-[#E8ECE7] bg-white hover:bg-[#F5F7F4] text-[#263329] text-xs font-bold transition flex items-center space-x-1.5 cursor-pointer disabled:opacity-50"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Back</span>
              </button>
            ) : (
              <div />
            )}

            <button
              type="button"
              onClick={handleNext}
              disabled={saving}
              className="px-6 py-2.5 rounded-xl bg-[#64BC45] hover:bg-[#469A36] text-white text-xs font-bold shadow-sm shadow-[#64BC45]/25 transition flex items-center space-x-2 cursor-pointer disabled:opacity-50"
            >
              {saving ? (
                <>
                  <Clock className="w-3.5 h-3.5 animate-spin" />
                  <span>Saving...</span>
                </>
              ) : currentStep === 5 ? (
                <>
                  <span>Complete Setup & Go to Dashboard</span>
                  <Check className="w-4 h-4" />
                </>
              ) : (
                <>
                  <span>Continue</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
