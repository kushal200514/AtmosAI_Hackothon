import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navigation from '../components/Navigation';
import Dashboard from '../components/Dashboard';
import PollutionMap from '../components/PollutionMap';
import ForecastDetails from '../components/ForecastDetails';
import ForecastAccuracyDashboard from '../components/ForecastAccuracyDashboard';
import ExplainableAI from '../components/ExplainableAI';
import TravelIntelligence from '../components/TravelIntelligence';
import WearablePrototype from '../components/WearablePrototype';
import AlertsView from '../components/AlertsView';
import ProfileSettingsModal from '../components/ProfileSettingsModal';
import LocationPickerSheet from '../components/LocationPickerSheet';
import MoreMenuSheet from '../components/MoreMenuSheet';
import SavedLocationsModal from '../components/SavedLocationsModal';
import { useAuth } from '../context/AuthContext';

import { 
  fetchLocations, 
  fetchSavedLocations,
  createSavedLocation,
  updateSavedLocation,
  deleteSavedLocation,
  fetchLiveForecast, 
  fetchMLPrediction, 
  fetchAIAdvice, 
  fetchMapData,
  fetchUserProfile
} from '../services/api';

export default function DashboardPage() {
  const navigate = useNavigate();
  const { user, profile, personalization, signOut, updateProfileData, authDisclaimer } = useAuth();

  const [currentTab, setCurrentTab] = useState('dashboard');
  const [locations, setLocations] = useState([]);
  const [selectedLocation, setSelectedLocation] = useState(
    profile?.primary_location || 'bengaluru_central'
  );
  const [currentProfile, setCurrentProfile] = useState(
    profile?.user_category || 'general_public'
  );
  
  // Centralized Profile & Personalization State
  const [userProfile, setUserProfile] = useState(profile);
  const [personalizationConfig, setPersonalizationConfig] = useState(personalization);

  const [liveData, setLiveData] = useState(null);
  const [forecastData, setForecastData] = useState(null);
  const [adviceData, setAdviceData] = useState(null);
  const [mapStations, setMapStations] = useState([]);

  const [isLoading, setIsLoading] = useState(true);
  const [backendConnected, setBackendConnected] = useState(false);
  
  // Mobile Sheets / Modals state
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);
  const [isLocationSheetOpen, setIsLocationSheetOpen] = useState(false);
  const [isMoreMenuOpen, setIsMoreMenuOpen] = useState(false);

  // Saved Location Intelligence State
  const [savedLocations, setSavedLocations] = useState([]);
  const [isSavedLocationsModalOpen, setIsSavedLocationsModalOpen] = useState(false);
  const [editingSavedLocation, setEditingSavedLocation] = useState(null);
  const [initialMapCoords, setInitialMapCoords] = useState(null);

  // Sync profile from context whenever it changes
  useEffect(() => {
    if (profile) {
      setUserProfile(profile);
      if (profile.user_category) {
        setCurrentProfile(profile.user_category);
      }
      if (profile.primary_location && !selectedLocation) {
        setSelectedLocation(profile.primary_location);
      }
    }
    if (personalization) {
      setPersonalizationConfig(personalization);
    }
  }, [profile, personalization]);

  // Initial load
  useEffect(() => {
    async function initPlatform() {
      try {
        const userId = user?.id || 'default_user';
        const [locs, mapRes, profRes, savedRes] = await Promise.all([
          fetchLocations(),
          fetchMapData(),
          fetchUserProfile(userId).catch(() => null),
          fetchSavedLocations(userId, true).catch(() => [])
        ]);

        setLocations(locs || []);
        if (mapRes && mapRes.stations) {
          setMapStations(mapRes.stations);
        }
        if (profRes && profRes.profile) {
          setUserProfile(profRes.profile);
          setPersonalizationConfig(profRes.personalization);
          setCurrentProfile(profRes.profile.user_category || 'general_public');
          if (profRes.profile.primary_location) {
            setSelectedLocation(profRes.profile.primary_location);
          }
        }
        if (savedRes && savedRes.length > 0) {
          setSavedLocations(savedRes);
          const primaryLoc = savedRes.find(l => l.is_primary);
          if (primaryLoc) {
            setSelectedLocation(primaryLoc.location_name);
          }
        }
        setBackendConnected(true);
      } catch (err) {
        console.error('Initial handshake failed:', err);
        setBackendConnected(false);
      }
    }
    initPlatform();
  }, [user]);

  // Saved Location Actions
  const handleRefreshSavedLocations = async () => {
    try {
      const userId = user?.id || 'default_user';
      const updated = await fetchSavedLocations(userId, true);
      setSavedLocations(updated);
    } catch (err) {
      console.error('Failed to refresh saved locations:', err);
    }
  };

  const handleSaveLocation = async (data) => {
    const userId = user?.id || 'default_user';
    await createSavedLocation(data, userId);
    await handleRefreshSavedLocations();
  };

  const handleUpdateLocation = async (id, data) => {
    const userId = user?.id || 'default_user';
    await updateSavedLocation(id, data, userId);
    await handleRefreshSavedLocations();
  };

  const handleDeleteLocation = async (id) => {
    const userId = user?.id || 'default_user';
    await deleteSavedLocation(id, userId);
    await handleRefreshSavedLocations();
  };

  const handleSetPrimaryLocation = async (id) => {
    const userId = user?.id || 'default_user';
    await updateSavedLocation(id, { is_primary: true }, userId);
    await handleRefreshSavedLocations();
  };

  const handleOpenAddLocationAtCoords = (coords) => {
    setEditingSavedLocation(null);
    setInitialMapCoords(coords);
    setIsSavedLocationsModalOpen(true);
  };

  // Telemetry refresh when location or profile changes
  useEffect(() => {
    async function loadTelemetry() {
      setIsLoading(true);
      try {
        const userId = user?.id || 'default_user';
        const [live, forecast, advice] = await Promise.all([
          fetchLiveForecast(selectedLocation),
          fetchMLPrediction(selectedLocation),
          fetchAIAdvice(selectedLocation, currentProfile, userId)
        ]);
        setLiveData(live);
        setForecastData(forecast);
        setAdviceData(advice);
        setBackendConnected(true);
      } catch (err) {
        console.error('Telemetry refresh failed:', err);
      } finally {
        setIsLoading(false);
      }
    }
    loadTelemetry();
  }, [selectedLocation, currentProfile, userProfile?.preferred_language, user]);

  // Dynamic Profile Updates Callback
  const handleProfileUpdated = async (updatedProfile, updatedConfig) => {
    setUserProfile(updatedProfile);
    setPersonalizationConfig(updatedConfig);
    const cat = updatedProfile.user_category || updatedProfile.profile_type;
    setCurrentProfile(cat);
    // Sync with auth context
    await updateProfileData(updatedProfile);
  };

  const handleLogout = async () => {
    await signOut();
    navigate('/welcome', { replace: true });
  };

  return (
    <div className="min-h-screen bg-[#F5F7F4] text-[#263329] flex flex-col font-sans selection:bg-[#64BC45] selection:text-white">
      {/* Demo Auth Banner if in Demo Mode */}
      {authDisclaimer && (
        <div className="bg-amber-50 border-b border-amber-200 px-4 py-1.5 text-center text-[11px] text-amber-800 flex items-center justify-center space-x-2">
          <span className="font-bold uppercase tracking-wider text-[9px] px-2 py-0.5 rounded bg-amber-200/80 text-amber-900">
            Demo Session
          </span>
          <span>Logged in as <strong>{user?.email || 'demo@atmosai.org'}</strong> ({userProfile?.full_name || 'Citizen'}) &bull; {authDisclaimer}</span>
        </div>
      )}

      {/* Top Mobile & Desktop App Bar with Location & Profile Quick Pills */}
      <Navigation
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        locations={locations}
        selectedLocation={selectedLocation}
        onOpenLocationPicker={() => setIsLocationSheetOpen(true)}
        currentProfile={currentProfile}
        onOpenProfileModal={() => setIsProfileModalOpen(true)}
        onOpenMoreMenu={() => setIsMoreMenuOpen(true)}
        onLogout={handleLogout}
        backendConnected={backendConnected}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl mx-auto w-full p-4 sm:p-6 lg:p-8">
        {currentTab === 'dashboard' && (
          <Dashboard
            liveData={liveData}
            forecastData={forecastData}
            adviceData={adviceData}
            userProfile={userProfile}
            personalizationConfig={personalizationConfig}
            stations={mapStations}
            savedLocations={savedLocations}
            selectedLocation={selectedLocation}
            onSelectLocation={(loc) => setSelectedLocation(loc)}
            onOpenSavedPlacesModal={(loc) => {
              setEditingSavedLocation(loc || null);
              setInitialMapCoords(null);
              setIsSavedLocationsModalOpen(true);
            }}
            onRefreshSavedPlaces={handleRefreshSavedLocations}
            onNavigate={(tab) => setCurrentTab(tab)}
          />
        )}

        {currentTab === 'map' && (
          <PollutionMap
            stations={mapStations}
            locations={locations}
            savedLocations={savedLocations}
            selectedLocation={selectedLocation}
            onSelectLocation={(loc) => {
              setSelectedLocation(loc);
              setCurrentTab('dashboard');
            }}
            onOpenAddLocationModal={handleOpenAddLocationAtCoords}
          />
        )}

        {currentTab === 'forecast' && (
          <ForecastDetails 
            forecastData={forecastData} 
            selectedLocation={selectedLocation}
          />
        )}

        {currentTab === 'accuracy' && (
          <ForecastAccuracyDashboard 
            selectedLocation={selectedLocation} 
          />
        )}

        {currentTab === 'ai' && (
          <ExplainableAI
            adviceData={adviceData}
            selectedLocation={selectedLocation}
            onSelectProfile={() => setIsProfileModalOpen(true)}
          />
        )}

        {currentTab === 'travel' && (
          <TravelIntelligence locations={locations} />
        )}

        {currentTab === 'wear' && (
          <WearablePrototype liveData={liveData} />
        )}

        {currentTab === 'alerts' && (
          <AlertsView currentProfile={currentProfile} userProfile={userProfile} />
        )}
      </main>

      {/* Mobile Location Picker Bottom Sheet */}
      <LocationPickerSheet
        isOpen={isLocationSheetOpen}
        onClose={() => setIsLocationSheetOpen(false)}
        locations={locations}
        savedLocations={savedLocations}
        selectedLocation={selectedLocation}
        onSelectLocation={(loc) => setSelectedLocation(loc)}
        onOpenManagePlaces={() => {
          setEditingSavedLocation(null);
          setInitialMapCoords(null);
          setIsSavedLocationsModalOpen(true);
        }}
      />

      {/* Mobile "More" Suite Drawer */}
      <MoreMenuSheet
        isOpen={isMoreMenuOpen}
        onClose={() => setIsMoreMenuOpen(false)}
        onSelectTab={(tab) => setCurrentTab(tab)}
        onOpenProfile={() => setIsProfileModalOpen(true)}
        currentProfile={currentProfile}
        backendStatus={backendConnected}
      />

      {/* Profile Settings & Personalization Manager Modal */}
      <ProfileSettingsModal
        isOpen={isProfileModalOpen}
        onClose={() => setIsProfileModalOpen(false)}
        userProfile={userProfile}
        onProfileUpdated={handleProfileUpdated}
      />

      {/* Saved Locations Intelligence Manager Modal */}
      <SavedLocationsModal
        isOpen={isSavedLocationsModalOpen}
        onClose={() => {
          setIsSavedLocationsModalOpen(false);
          setEditingSavedLocation(null);
          setInitialMapCoords(null);
        }}
        savedLocations={savedLocations}
        editingLocation={editingSavedLocation}
        initialCoordinates={initialMapCoords}
        onSaveLocation={handleSaveLocation}
        onUpdateLocation={handleUpdateLocation}
        onDeleteLocation={handleDeleteLocation}
        onSetPrimary={handleSetPrimaryLocation}
      />

      {/* Footer (Desktop only) */}
      <footer className="hidden sm:flex border-t border-[#E8ECE7] py-4 px-6 text-xs text-[#788278] items-center justify-between max-w-7xl mx-auto w-full">
        <p>AtmosAI &bull; Breathe Smarter, Live Safer &bull; Initial Target: Bengaluru, India</p>
        <p className="font-mono text-[11px] text-[#469A36]">
          LightGBM ML Engine &bull; Google Gemini &bull; CPCB NAQI
        </p>
      </footer>
    </div>
  );
}
