import React, { useState, useEffect } from 'react';
import { 
  X, 
  MapPin, 
  Plus, 
  Search, 
  Compass, 
  Home, 
  GraduationCap, 
  Briefcase, 
  Star, 
  Save, 
  Check, 
  AlertCircle,
  Radio,
  Clock
} from 'lucide-react';
import { searchLocations } from '../services/api';

/**
 * Saved Places Manager Modal
 * Search, manual coordinate entry, GPS detection, place type tagging, and CRUD editing.
 */
export default function SavedLocationsModal({
  isOpen,
  onClose,
  savedLocations = [],
  onSaveLocation,
  onUpdateLocation,
  onDeleteLocation,
  onSetPrimary,
  editingLocation = null,
  initialCoordinates = null
}) {
  const [activeTab, setActiveTab] = useState(editingLocation ? 'form' : 'list');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);

  // Form State
  const [formData, setFormData] = useState({
    location_id: null,
    location_name: '',
    location_type: 'home',
    address: '',
    latitude: 12.9716,
    longitude: 77.5946,
    is_primary: false
  });
  const [formError, setFormError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [gpsLoading, setGpsLoading] = useState(false);

  useEffect(() => {
    if (editingLocation) {
      setFormData({
        location_id: editingLocation.location_id,
        location_name: editingLocation.location_name,
        location_type: editingLocation.location_type || 'custom',
        address: editingLocation.address || '',
        latitude: editingLocation.latitude,
        longitude: editingLocation.longitude,
        is_primary: editingLocation.is_primary || false
      });
      setActiveTab('form');
    } else if (initialCoordinates) {
      setFormData(prev => ({
        ...prev,
        latitude: initialCoordinates.latitude,
        longitude: initialCoordinates.longitude,
        address: `Selected Map Point (${initialCoordinates.latitude.toFixed(4)}, ${initialCoordinates.longitude.toFixed(4)})`
      }));
      setActiveTab('form');
    } else {
      setFormData({
        location_id: null,
        location_name: '',
        location_type: 'home',
        address: '',
        latitude: 12.9716,
        longitude: 77.5946,
        is_primary: savedLocations.length === 0
      });
    }
  }, [editingLocation, initialCoordinates, isOpen]);

  // Debounced Place Search
  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }
    const timer = setTimeout(async () => {
      setIsSearching(true);
      try {
        const results = await searchLocations(searchQuery);
        setSearchResults(results);
      } catch (err) {
        console.error('Location search failed:', err);
      } finally {
        setIsSearching(false);
      }
    }, 250);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  if (!isOpen) return null;

  const handleSelectSearchResult = (result) => {
    setFormData(prev => ({
      ...prev,
      location_name: prev.location_name || result.display_name.split('(')[0].trim(),
      address: result.address,
      latitude: result.latitude,
      longitude: result.longitude
    }));
    setActiveTab('form');
  };

  const handleGPSDetect = () => {
    if (!navigator.geolocation) {
      setFormError('Geolocation is not supported by your browser. Please enter coordinates manually.');
      return;
    }
    setGpsLoading(true);
    setFormError('');

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setFormData(prev => ({
          ...prev,
          latitude: parseFloat(pos.coords.latitude.toFixed(5)),
          longitude: parseFloat(pos.coords.longitude.toFixed(5)),
          address: 'Current GPS Location (Device Sensor)'
        }));
        setGpsLoading(false);
      },
      (err) => {
        setFormError('GPS permission denied or timed out. Manual coordinate entry remains fully supported.');
        setGpsLoading(false);
      },
      { timeout: 8000 }
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormError('');

    if (!formData.location_name.trim()) {
      setFormError('Please provide a name for this place.');
      return;
    }
    if (isNaN(formData.latitude) || formData.latitude < -90 || formData.latitude > 90) {
      setFormError('Latitude must be between -90 and 90.');
      return;
    }
    if (isNaN(formData.longitude) || formData.longitude < -180 || formData.longitude > 180) {
      setFormError('Longitude must be between -180 and 180.');
      return;
    }

    setIsSubmitting(true);
    try {
      if (formData.location_id) {
        await onUpdateLocation(formData.location_id, {
          location_name: formData.location_name,
          location_type: formData.location_type,
          address: formData.address,
          latitude: formData.latitude,
          longitude: formData.longitude,
          is_primary: formData.is_primary
        });
      } else {
        await onSaveLocation({
          location_name: formData.location_name,
          location_type: formData.location_type,
          address: formData.address,
          latitude: formData.latitude,
          longitude: formData.longitude,
          is_primary: formData.is_primary
        });
      }
      onClose();
    } catch (err) {
      setFormError(err.message || 'Failed to save location.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-3 sm:p-4 animate-fade-in">
      <div className="relative w-full max-w-lg bg-white rounded-3xl border border-[#E8ECE7] shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-[#E8ECE7] bg-white">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-[#F1F8ED] text-[#469A36]">
              <MapPin className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-[#263329] text-base">Saved Location Intelligence</h3>
              <p className="text-xs text-[#788278]">Monitor air quality across your important places</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-full bg-[#F5F7F4] text-[#788278] hover:text-[#263329] hover:bg-[#E8ECE7] transition cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Tab Switcher */}
        <div className="flex border-b border-[#E8ECE7] bg-[#F5F7F4] p-2 gap-2">
          <button
            onClick={() => setActiveTab('list')}
            className={`flex-1 py-2 text-xs font-bold rounded-xl transition cursor-pointer ${
              activeTab === 'list' 
                ? 'bg-white text-[#469A36] border border-[#C2EBBA] shadow-xs' 
                : 'text-[#788278] hover:text-[#263329]'
            }`}
          >
            My Places ({savedLocations.length})
          </button>
          <button
            onClick={() => setActiveTab('form')}
            className={`flex-1 py-2 text-xs font-bold rounded-xl transition cursor-pointer ${
              activeTab === 'form' 
                ? 'bg-white text-[#469A36] border border-[#C2EBBA] shadow-xs' 
                : 'text-[#788278] hover:text-[#263329]'
            }`}
          >
            {formData.location_id ? 'Edit Place' : '+ Add New Place'}
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {activeTab === 'list' && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-[#788278]">Your monitored locations</span>
                <button
                  onClick={() => {
                    setFormData({
                      location_id: null,
                      location_name: '',
                      location_type: 'home',
                      address: '',
                      latitude: 12.9716,
                      longitude: 77.5946,
                      is_primary: false
                    });
                    setActiveTab('form');
                  }}
                  className="text-xs font-bold text-[#469A36] flex items-center space-x-1 hover:underline cursor-pointer"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Add Place</span>
                </button>
              </div>

              {savedLocations.length === 0 ? (
                <div className="text-center py-8 text-[#788278] text-xs space-y-2">
                  <p>No saved places yet.</p>
                  <button
                    onClick={() => setActiveTab('form')}
                    className="px-4 py-2 rounded-xl bg-[#64BC45] text-white font-bold hover:bg-[#469A36] transition cursor-pointer"
                  >
                    Add Your First Location
                  </button>
                </div>
              ) : (
                <div className="space-y-2.5">
                  {savedLocations.map((loc) => (
                    <div 
                      key={loc.location_id}
                      className="p-3 rounded-xl border border-[#E8ECE7] bg-[#F5F7F4] flex items-center justify-between gap-2"
                    >
                      <div className="space-y-0.5 min-w-0">
                        <div className="flex items-center space-x-1.5">
                          <span className="text-xs font-bold text-[#263329] truncate">{loc.location_name}</span>
                          <span className="text-[9px] uppercase px-1.5 py-0.5 rounded bg-white text-[#788278] border border-[#E8ECE7] font-mono">
                            {loc.location_type.replace('_', ' ')}
                          </span>
                          {loc.is_primary && (
                            <span className="text-[9px] uppercase px-1.5 py-0.5 rounded bg-[#F1F8ED] text-[#469A36] border border-[#C2EBBA] font-bold">
                              Primary
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] text-[#788278] truncate">{loc.address}</p>
                      </div>

                      <div className="flex items-center space-x-1 flex-shrink-0">
                        {!loc.is_primary && (
                          <button
                            onClick={() => onSetPrimary(loc.location_id)}
                            className="p-1.5 rounded-lg text-[#788278] hover:text-[#469A36] hover:bg-white transition cursor-pointer"
                            title="Set as Primary Default"
                          >
                            <Star className="w-3.5 h-3.5" />
                          </button>
                        )}
                        <button
                          onClick={() => {
                            setFormData({
                              location_id: loc.location_id,
                              location_name: loc.location_name,
                              location_type: loc.location_type,
                              address: loc.address,
                              latitude: loc.latitude,
                              longitude: loc.longitude,
                              is_primary: loc.is_primary
                            });
                            setActiveTab('form');
                          }}
                          className="p-1.5 rounded-lg text-[#788278] hover:text-[#263329] hover:bg-white transition cursor-pointer"
                          title="Edit"
                        >
                          <MapPin className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'form' && (
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Autocomplete Search Bar */}
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-[#263329]">
                  Search Bengaluru Locality or Landmark
                </label>
                <div className="relative">
                  <Search className="w-4 h-4 text-[#788278] absolute left-3 top-3" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="e.g. Indiranagar, PES University, Bellandur, Whitefield..."
                    className="w-full pl-9 pr-4 py-2.5 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7] text-xs text-[#263329] placeholder-[#788278] focus:outline-none focus:border-[#64BC45] focus:bg-white transition"
                  />
                  {isSearching && (
                    <Clock className="w-4 h-4 text-[#64BC45] animate-spin absolute right-3 top-3" />
                  )}
                </div>

                {/* Instant Suggestions Dropdown */}
                {searchResults.length > 0 && (
                  <div className="p-1 rounded-xl bg-white border border-[#E8ECE7] shadow-xl max-h-48 overflow-y-auto space-y-1">
                    {searchResults.map((res, i) => (
                      <div
                        key={i}
                        onClick={() => handleSelectSearchResult(res)}
                        className="p-2.5 rounded-lg hover:bg-[#F1F8ED] cursor-pointer transition text-xs space-y-0.5"
                      >
                        <p className="font-bold text-[#469A36]">{res.display_name}</p>
                        <p className="text-[10px] text-[#788278] truncate">{res.address}</p>
                        <p className="text-[10px] text-[#788278] font-mono">
                          Nearest station: {res.nearest_station_name} ({res.nearest_station_distance_km} km away)
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Optional GPS Auto-detect Button */}
              <div className="flex items-center justify-between p-3 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7]">
                <div className="flex items-center space-x-2">
                  <Compass className="w-4 h-4 text-[#469A36] flex-shrink-0" />
                  <div>
                    <p className="text-xs font-bold text-[#263329]">Device Location (Optional)</p>
                    <p className="text-[10px] text-[#788278]">GPS permission is never required</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={handleGPSDetect}
                  disabled={gpsLoading}
                  className="px-3 py-1.5 rounded-lg bg-white border border-[#E8ECE7] hover:bg-[#F1F8ED] text-[#469A36] text-xs font-semibold cursor-pointer disabled:opacity-50 transition"
                >
                  {gpsLoading ? 'Detecting...' : 'Use GPS'}
                </button>
              </div>

              {/* Place Name */}
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-[#263329]">
                  Place Name *
                </label>
                <input
                  type="text"
                  value={formData.location_name}
                  onChange={(e) => setFormData({ ...formData, location_name: e.target.value })}
                  placeholder="e.g. My Apartment, PES College Campus, Office"
                  className="w-full px-3 py-2 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7] text-xs text-[#263329] placeholder-[#788278] focus:outline-none focus:border-[#64BC45] focus:bg-white transition"
                  required
                />
              </div>

              {/* Location Type Picker */}
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-[#263329]">
                  Location Type
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                  {[
                    { id: 'home', label: 'Home', icon: Home },
                    { id: 'college_school', label: 'College / School', icon: GraduationCap },
                    { id: 'office', label: 'Office', icon: Briefcase },
                    { id: 'favourite_place', label: 'Favourite Place', icon: Star },
                    { id: 'custom', label: 'Custom', icon: MapPin }
                  ].map((t) => {
                    const TypeIcon = t.icon;
                    const isSelected = formData.location_type === t.id;
                    return (
                      <button
                        key={t.id}
                        type="button"
                        onClick={() => setFormData({ ...formData, location_type: t.id })}
                        className={`p-2.5 rounded-xl border text-xs font-bold flex items-center space-x-2 transition cursor-pointer ${
                          isSelected
                            ? 'bg-[#F1F8ED] border-[#64BC45] text-[#469A36] ring-1 ring-[#64BC45]'
                            : 'bg-[#F5F7F4] border-[#E8ECE7] text-[#788278] hover:text-[#263329] hover:border-[#C2EBBA]'
                        }`}
                      >
                        <TypeIcon className="w-3.5 h-3.5 flex-shrink-0" />
                        <span className="truncate">{t.label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Address / Landmark */}
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-[#263329]">
                  Address or Locality
                </label>
                <input
                  type="text"
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  placeholder="e.g. 100 Feet Road, Indiranagar, Bengaluru"
                  className="w-full px-3 py-2 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7] text-xs text-[#263329] placeholder-[#788278] focus:outline-none focus:border-[#64BC45] focus:bg-white transition"
                />
              </div>

              {/* Coordinates */}
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-[11px] font-bold text-[#788278]">Latitude</label>
                  <input
                    type="number"
                    step="0.0001"
                    value={formData.latitude}
                    onChange={(e) => setFormData({ ...formData, latitude: parseFloat(e.target.value) })}
                    className="w-full px-3 py-2 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7] text-xs text-[#263329] font-mono focus:outline-none focus:border-[#64BC45] focus:bg-white transition"
                    required
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-[11px] font-bold text-[#788278]">Longitude</label>
                  <input
                    type="number"
                    step="0.0001"
                    value={formData.longitude}
                    onChange={(e) => setFormData({ ...formData, longitude: parseFloat(e.target.value) })}
                    className="w-full px-3 py-2 rounded-xl bg-[#F5F7F4] border border-[#E8ECE7] text-xs text-[#263329] font-mono focus:outline-none focus:border-[#64BC45] focus:bg-white transition"
                    required
                  />
                </div>
              </div>

              {/* Primary Location Toggle */}
              <div className="flex items-center space-x-2 pt-1">
                <input
                  type="checkbox"
                  id="is_primary"
                  checked={formData.is_primary}
                  onChange={(e) => setFormData({ ...formData, is_primary: e.target.checked })}
                  className="w-4 h-4 rounded border-[#E8ECE7] text-[#64BC45] focus:ring-[#64BC45] bg-[#F5F7F4] cursor-pointer"
                />
                <label htmlFor="is_primary" className="text-xs text-[#263329] cursor-pointer">
                  Set as Primary Place (Default for Dashboard & Alerts)
                </label>
              </div>

              {formError && (
                <div className="p-2.5 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0" />
                  <span>{formError}</span>
                </div>
              )}

              {/* Submit Buttons */}
              <div className="flex items-center justify-end space-x-2 pt-2 border-t border-[#E8ECE7]">
                <button
                  type="button"
                  onClick={() => setActiveTab('list')}
                  className="px-4 py-2 rounded-xl bg-[#F5F7F4] text-[#788278] text-xs font-bold hover:bg-[#E8ECE7] hover:text-[#263329] transition cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2 rounded-xl bg-[#64BC45] hover:bg-[#469A36] text-white text-xs font-extrabold transition cursor-pointer flex items-center space-x-1.5 shadow-sm shadow-[#64BC45]/20 disabled:opacity-50"
                >
                  <Save className="w-3.5 h-3.5" />
                  <span>{isSubmitting ? 'Saving...' : formData.location_id ? 'Update Place' : 'Save Place'}</span>
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}

