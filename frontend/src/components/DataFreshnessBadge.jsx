import React from 'react';
import { Radio, Database, Clock, AlertTriangle, CheckCircle2, AlertCircle, HelpCircle } from 'lucide-react';

/**
 * Compact Data Freshness & Provenance Pill
 * Ideal for mobile cards, widget headers, and table rows.
 */
export default function DataFreshnessBadge({ 
  freshnessStatus = "FRESH", 
  sourceType = "MEASURED", 
  ageMinutes = null,
  onClick = null,
  className = "" 
}) {
  const status = (freshnessStatus || "UNAVAILABLE").toUpperCase();
  const source = (sourceType || "ESTIMATED").toUpperCase();

  const getStatusBadge = () => {
    switch (status) {
      case 'FRESH':
        return {
          label: ageMinutes !== null ? `${Math.round(ageMinutes)}m ago` : 'Fresh',
          className: 'bg-[#F1F8ED] border-[#C2EBBA] text-[#469A36]',
          dot: 'bg-[#64BC45]'
        };
      case 'AGING':
        return {
          label: ageMinutes !== null ? `${Math.round(ageMinutes)}m old` : 'Aging',
          className: 'bg-amber-50 border-amber-200 text-amber-700',
          dot: 'bg-amber-500'
        };
      case 'STALE':
        return {
          label: 'STALE DATA',
          className: 'bg-red-50 border-red-200 text-red-700 animate-pulse font-black',
          dot: 'bg-red-500'
        };
      case 'UNAVAILABLE':
      default:
        return {
          label: 'Unavailable',
          className: 'bg-[#F5F7F4] border-[#E8ECE7] text-[#788278]',
          dot: 'bg-[#788278]'
        };
    }
  };

  const getSourceIcon = () => {
    switch (source) {
      case 'MEASURED':
        return Radio;
      case 'FORECAST':
        return Database;
      case 'DEMO':
        return HelpCircle;
      case 'ESTIMATED':
      default:
        return Database;
    }
  };

  const statusBadge = getStatusBadge();
  const SourceIcon = getSourceIcon();

  return (
    <div 
      onClick={onClick}
      className={`inline-flex items-center space-x-1.5 px-2 py-0.5 rounded-full border text-[10px] font-bold uppercase transition-all ${statusBadge.className} ${onClick ? 'cursor-pointer hover:opacity-85' : ''} ${className}`}
      title={`Source: ${source} | Status: ${status} | Note: Freshness reflects age, not accuracy.`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${statusBadge.dot}`} />
      <SourceIcon className="w-2.5 h-2.5" />
      <span>{source}</span>
      <span className="opacity-50">&bull;</span>
      <span>{statusBadge.label}</span>
    </div>
  );
}

