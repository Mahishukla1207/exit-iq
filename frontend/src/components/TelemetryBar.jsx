import React from 'react';
import { Users, Flame, AlertCircle, Cpu, Clock, Zap } from 'lucide-react';

export default function TelemetryBar({ metrics }) {
  const m = metrics || {
    people_detected: 0,
    active_hazards: 0,
    highest_risk_zone: 'N/A',
    highest_risk_score: 0.0,
    predicted_peak_congestion: 0.0,
    route_cost: 0.0,
    est_evac_time_sec: 0.0,
    system_latency_ms: 8.5,
    cv_fps: 30.0,
  };

  const statItems = [
    { label: 'PEOPLE DETECTED', value: m.people_detected, icon: Users, color: 'text-sky-400' },
    { label: 'ACTIVE HAZARDS', value: m.active_hazards, icon: Flame, color: 'text-rose-400' },
    { label: 'HIGHEST RISK ZONE', value: `${m.highest_risk_zone} (${m.highest_risk_score})`, icon: AlertCircle, color: 'text-amber-400' },
    { label: 'PEAK PRED DENSITY', value: `${m.predicted_peak_congestion} (Normalized)`, icon: Cpu, color: 'text-purple-400' },
    { label: 'ROUTE DYNAMIC COST', value: m.route_cost, icon: Zap, color: 'text-emerald-400' },
    { label: 'EST. EVAC TIME', value: `${m.est_evac_time_sec}s`, icon: Clock, color: 'text-amber-300' },
    { label: 'SYSTEM LATENCY', value: `${m.system_latency_ms}ms`, icon: Cpu, color: 'text-sky-300' },
  ];

  return (
    <footer className="bg-[#0b101c] border-t border-[#1f293d] px-6 py-2.5 flex items-center justify-between font-mono text-xs select-none">
      <div className="flex items-center space-x-6 overflow-x-auto w-full">
        <span className="text-[10px] text-eoc-muted font-bold tracking-widest uppercase mr-2 border-r border-[#1f293d] pr-4">
          SYSTEM TELEMETRY:
        </span>

        {statItems.map((item, idx) => {
          const Icon = item.icon;
          return (
            <div key={idx} className="flex items-center space-x-2 whitespace-nowrap">
              <Icon className={`w-3.5 h-3.5 ${item.color}`} />
              <div>
                <span className="text-[10px] text-eoc-muted uppercase mr-1.5">{item.label}:</span>
                <span className={`font-bold ${item.color}`}>{item.value}</span>
              </div>
            </div>
          );
        })}
      </div>
    </footer>
  );
}
