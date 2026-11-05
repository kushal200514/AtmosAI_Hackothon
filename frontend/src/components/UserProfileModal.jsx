import React from 'react';
import { 
  X, 
  Footprints, 
  ShieldAlert, 
  Baby, 
  Bike, 
  Briefcase, 
  Users, 
  Check 
} from 'lucide-react';
import { updateUserProfile } from '../services/api';

const PROFILES = [
  {
    id: 'runner',
    title: 'Runner / Athlete',
    description: 'High aerobic respiratory volume during outdoor training. Prioritizes low-particulate windows and pacing guidance.',
    icon: Footprints
  },
  {
    id: 'respiratory_sensitive',
    title: 'Respiratory-Sensitive Individual',
    description: 'Asthma, COPD, or airborne allergy sensitivity. Requires early surge notifications and strict N95 recommendations.',
    icon: ShieldAlert
  },
  {
    id: 'parent',
    title: 'Parent / Guardian',
    description: 'Focused on pediatric lung health during school runs, stroller walks, and outdoor playground activities.',
    icon: Baby
  },
  {
    id: 'delivery_worker',
    title: 'Delivery Worker / Field Professional',
    description: 'Prolonged high-exposure street transit on two-wheelers. Prioritizes route alerts and protective mask guidance.',
    icon: Bike
  },
  {
    id: 'office_commuter',
    title: 'Office Commuter',
    description: 'Daily peak-hour travel across high-congestion arterial roads. Guidance on vehicle recirculation and route exposure.',
    icon: Briefcase
  },
  {
    id: 'general_public',
    title: 'General Public',
    description: 'Everyday environmental awareness, indoor window ventilation schedules, and lifestyle precautions.',
    icon: Users
  }
];

export default function UserProfileModal({ isOpen, onClose, currentProfile, onSelectProfile }) {
  if (!isOpen) return null;

  const handleSelect = async (profileId) => {
    onSelectProfile(profileId);
    try {
      await updateUserProfile({ profile_type: profileId });
    } catch (err) {
      console.error('Failed to sync profile update:', err);
    }
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-fadeIn">
      <div className="w-full max-w-2xl bg-white p-6 border border-[#E8ECE7] rounded-3xl shadow-2xl relative space-y-5">
        <div className="flex items-center justify-between border-b border-[#E8ECE7] pb-3">
          <div>
            <h2 className="text-lg font-bold text-[#263329] tracking-tight">Select Personal Environmental Profile</h2>
            <p className="text-xs text-[#788278]">Customizes AI recommendations and alert thresholds to your lifestyle.</p>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-full bg-[#F5F7F4] hover:bg-[#E8ECE7] text-[#788278] hover:text-[#263329] transition cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Profile Options Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-[60vh] overflow-y-auto pr-1">
          {PROFILES.map((prof) => {
            const Icon = prof.icon;
            const isSelected = currentProfile === prof.id;

            return (
              <div
                key={prof.id}
                onClick={() => handleSelect(prof.id)}
                className={`p-4 rounded-2xl border transition cursor-pointer flex flex-col justify-between space-y-2.5 ${
                  isSelected
                    ? 'bg-[#F1F8ED] border-[#64BC45] shadow-sm ring-1 ring-[#64BC45]'
                    : 'bg-[#F5F7F4] border-[#E8ECE7] hover:border-[#C2EBBA] hover:bg-[#F1F8ED]/40'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2.5">
                    <div className={`p-2 rounded-xl ${isSelected ? 'bg-white text-[#469A36] border border-[#C2EBBA]' : 'bg-white text-[#788278] border border-[#E8ECE7]'}`}>
                      <Icon className="w-4 h-4" />
                    </div>
                    <span className="font-bold text-xs text-[#263329]">{prof.title}</span>
                  </div>
                  {isSelected && (
                    <div className="w-5 h-5 rounded-full bg-[#64BC45] text-white flex items-center justify-center">
                      <Check className="w-3.5 h-3.5 stroke-[3]" />
                    </div>
                  )}
                </div>

                <p className="text-[11px] text-[#788278] leading-relaxed">
                  {prof.description}
                </p>
              </div>
            );
          })}
        </div>

        <div className="pt-2 border-t border-[#E8ECE7] text-[11px] text-[#788278] text-center">
          Profile selection dynamically recalibrates AI health guidance and LightGBM surge warnings.
        </div>
      </div>
    </div>
  );
}

