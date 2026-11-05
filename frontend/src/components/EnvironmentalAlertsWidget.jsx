import React, { useState, useEffect } from 'react';
import { 
  Bell, 
  AlertTriangle, 
  ShieldAlert, 
  CheckCircle2, 
  ArrowUpRight 
} from 'lucide-react';
import { fetchAlerts } from '../services/api';

export default function EnvironmentalAlertsWidget({ userProfile, onNavigate }) {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const cat = userProfile?.user_category || 'general_public';
        const uid = userProfile?.id || 'default_user';
        const data = await fetchAlerts(cat, uid);
        setAlerts(data);
      } catch (e) {
        console.error('Failed to load alerts widget:', e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [userProfile?.user_category, userProfile?.notifications?.high_pollution_threshold]);

  const getAlertIcon = (severity) => {
    if (severity === 'high' || severity === 'critical') {
      return <ShieldAlert className="w-4 h-4 text-rose-400 flex-shrink-0" />;
    }
    if (severity === 'medium') {
      return <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />;
    }
    return <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />;
  };

  return (
    <div className="atmos-card p-4 sm:p-5 border border-[#E8ECE7] bg-white space-y-3 shadow-xs">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="p-1.5 rounded-lg bg-[#F1F8ED] text-[#469A36]">
            <Bell className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-[#263329]">Active Environmental Alerts</h3>
            <p className="text-[10px] text-[#788278]">
              Personalized to threshold AQI &ge; {userProfile?.notifications?.high_pollution_threshold || 100}
            </p>
          </div>
        </div>

        <button 
          onClick={() => onNavigate('alerts')}
          className="text-[11px] font-semibold text-[#469A36] flex items-center space-x-1 hover:underline cursor-pointer"
        >
          <span>All Alerts</span>
          <ArrowUpRight className="w-3 h-3" />
        </button>
      </div>

      {loading ? (
        <div className="text-xs text-[#788278] py-3 text-center">Checking sensor conditions...</div>
      ) : alerts && alerts.length > 0 ? (
        <div className="space-y-2">
          {alerts.slice(0, 3).map((a, idx) => (
            <div 
              key={idx}
              className={`p-3 rounded-xl border flex items-start space-x-2.5 ${
                a.severity === 'high'
                  ? 'bg-rose-50 border-rose-200 text-rose-900'
                  : a.severity === 'medium'
                  ? 'bg-amber-50 border-amber-200 text-amber-900'
                  : 'bg-[#F1F8ED] border-[#C2EBBA] text-[#263329]'
              }`}
            >
              {getAlertIcon(a.severity)}
              <div className="space-y-0.5 min-w-0">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold truncate text-[#263329]">{a.title}</h4>
                  <span className="text-[10px] opacity-75 font-mono text-[#788278]">{a.location_name}</span>
                </div>
                <p className="text-[11px] leading-snug">{a.message}</p>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="p-3 text-center text-xs text-[#788278] rounded-xl bg-[#F5F7F4]">
          No active pollution surges in your monitored perimeter.
        </div>
      )}
    </div>
  );
}

