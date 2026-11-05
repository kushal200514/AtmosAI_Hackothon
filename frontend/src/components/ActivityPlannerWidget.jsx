import React, { useState, useEffect } from 'react';
import { 
  Calendar, 
  Clock, 
  Sparkles, 
  CheckCircle2, 
  AlertCircle, 
  ChevronRight, 
  PlusCircle,
  Footprints,
  Bike,
  Baby,
  Briefcase,
  GraduationCap,
  Activity
} from 'lucide-react';
import { fetchActivityPlanner } from '../services/api';

const ALL_POSSIBLE_ACTIVITIES = [
  { id: 'running', label: 'Running / Jogging', icon: Footprints },
  { id: 'cycling', label: 'Cycling', icon: Bike },
  { id: 'walking', label: 'Brisk Walking', icon: Footprints },
  { id: 'campus_walks', label: 'Campus Transit', icon: GraduationCap },
  { id: 'outdoor_sports', label: 'Outdoor Sports', icon: Activity },
  { id: 'playground_trips', label: 'Playground Trips', icon: Baby },
  { id: 'stroller_walks', label: 'Stroller Walks', icon: Baby },
  { id: 'morning_transit', label: 'Morning Commute', icon: Briefcase },
  { id: 'evening_transit', label: 'Evening Transit', icon: Briefcase },
  { id: 'street_deliveries', label: 'Street Deliveries', icon: Bike },
  { id: 'outdoor_shifts', label: 'Outdoor Shifts', icon: Activity }
];

export default function ActivityPlannerWidget({ location, userProfile, onNavigate }) {
  const [plannerScores, setPlannerScores] = useState([]);
  const [selectedActivity, setSelectedActivity] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showAddMenu, setShowAddMenu] = useState(false);

  useEffect(() => {
    async function loadPlanner() {
      setLoading(true);
      try {
        const scores = await fetchActivityPlanner(location, userProfile?.id || 'default_user');
        setPlannerScores(scores);
        if (scores && scores.length > 0) {
          const distinct = [...new Set(scores.map(s => s.activity_name))];
          if (!selectedActivity || !distinct.includes(selectedActivity)) {
            setSelectedActivity(distinct[0]);
          }
        }
      } catch (err) {
        console.error('Failed to load activity planner:', err);
      } finally {
        setLoading(false);
      }
    }
    loadPlanner();
  }, [location, userProfile?.user_category, userProfile?.preferred_activities]);

  const distinctActivities = [...new Set(plannerScores.map(s => s.activity_name))];
  const activeScores = plannerScores.filter(s => s.activity_name === selectedActivity);

  const getScoreColor = (score) => {
    if (score >= 75) return { text: 'text-[#469A36]', bg: 'bg-[#F1F8ED]', border: 'border-[#C2EBBA]', tag: 'Optimal' };
    if (score >= 50) return { text: 'text-amber-700', bg: 'bg-amber-50', border: 'border-amber-200', tag: 'Moderate' };
    return { text: 'text-rose-700', bg: 'bg-rose-50', border: 'border-rose-200', tag: 'Challenging' };
  };

  return (
    <div className="atmos-card p-4 sm:p-6 border border-[#E8ECE7] bg-white space-y-4 shadow-xs">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="p-2 rounded-xl bg-[#F1F8ED] text-[#469A36] border border-[#C2EBBA]">
            <Calendar className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-[#263329] flex items-center space-x-1.5">
              <span>Smart Activity Planner</span>
            </h3>
            <p className="text-[11px] text-[#788278]">
              Multi-horizon forecast window comparison
            </p>
          </div>
        </div>

        <button 
          onClick={() => setShowAddMenu(!showAddMenu)}
          className="text-xs text-[#469A36] hover:text-[#263329] flex items-center space-x-1 cursor-pointer bg-[#F1F8ED] hover:bg-[#C2EBBA] px-2.5 py-1 rounded-lg border border-[#C2EBBA] transition font-semibold"
        >
          <PlusCircle className="w-3.5 h-3.5" />
          <span>Switch Activity</span>
        </button>
      </div>

      {/* Selectable Activity Chips */}
      <div className="flex items-center space-x-2 overflow-x-auto pb-1.5 no-scrollbar">
        {distinctActivities.map((act) => {
          const isSelected = act === selectedActivity;
          return (
            <button
              key={act}
              onClick={() => setSelectedActivity(act)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition cursor-pointer flex items-center space-x-1.5 ${
                isSelected 
                  ? 'bg-[#64BC45] text-white shadow-xs font-bold'
                  : 'bg-[#F5F7F4] text-[#263329] hover:bg-[#F1F8ED] border border-[#E8ECE7]'
              }`}
            >
              <span>{act}</span>
            </button>
          );
        })}
      </div>

      {/* Add / Switch Activity Picker Popover */}
      {showAddMenu && (
        <div className="p-3 rounded-xl bg-white border border-[#C2EBBA] shadow-lg space-y-2 animate-fadeIn">
          <p className="text-[11px] font-semibold text-[#788278] uppercase tracking-wider">
            Explore Other Daily Activities
          </p>
          <div className="flex flex-wrap gap-1.5">
            {ALL_POSSIBLE_ACTIVITIES.map(item => (
              <button
                key={item.id}
                onClick={() => {
                  setSelectedActivity(item.label);
                  setShowAddMenu(false);
                }}
                className="px-2.5 py-1 rounded-lg text-[11px] bg-[#F5F7F4] hover:bg-[#F1F8ED] text-[#263329] hover:text-[#469A36] border border-[#E8ECE7] transition cursor-pointer font-medium"
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Forecast Windows Comparison Grid */}
      {loading ? (
        <div className="p-8 text-center text-[#788278] text-xs">Evaluating atmospheric windows...</div>
      ) : activeScores.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {activeScores.map((w, idx) => {
            const colors = getScoreColor(w.suitability_score);
            return (
              <div 
                key={idx}
                className={`p-3.5 rounded-2xl border transition ${colors.bg} ${colors.border} space-y-2.5 relative overflow-hidden`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-1.5">
                    <Clock className="w-3.5 h-3.5 text-[#788278]" />
                    <span className="text-xs font-bold text-[#263329]">{w.horizon_label}</span>
                  </div>
                  <span className={`text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-md border ${colors.bg} ${colors.border} ${colors.text}`}>
                    {colors.tag} ({w.suitability_score}/100)
                  </span>
                </div>

                <div className="flex items-baseline justify-between">
                  <div>
                    <span className="text-[10px] text-[#788278] block">Forecast PM2.5</span>
                    <span className="text-xl font-black font-mono text-[#263329]">
                      {w.predicted_pm25} <span className="text-xs text-[#788278] font-normal">µg/m³</span>
                    </span>
                  </div>
                </div>

                {/* Explainable Why This Window Is Best / Challenging */}
                <div className="pt-2 border-t border-[#E8ECE7] text-[11px] text-[#263329] flex items-start space-x-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-[#469A36] flex-shrink-0 mt-0.5" />
                  <p className="leading-snug">{w.explanation}</p>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="p-6 text-center text-[#788278] text-xs rounded-xl bg-[#F5F7F4]">
          Select an activity to view forecast window suitability comparisons.
        </div>
      )}
    </div>
  );
}

