import React, { useState, useEffect } from 'react';
import { X, Flame, Users, AlertTriangle, Zap } from 'lucide-react';

export default function HazardControlModal({
  isOpen,
  onClose,
  onInjectHazard,
  onUpdateCrowd,
  selectedNode,
}) {
  const [selectedZone, setSelectedZone] = useState('zone_atrium');
  const [hazardType, setHazardType] = useState('fire');
  const [severity, setSeverity] = useState(0.85);
  const [crowdDensity, setCrowdDensity] = useState(3.5);

  useEffect(() => {
    if (selectedNode && selectedNode.zone_id) {
      setSelectedZone(selectedNode.zone_id);
    }
  }, [selectedNode]);

  if (!isOpen) return null;

  const handleAddHazard = () => {
    const node_id = selectedNode ? selectedNode.id : null;
    onInjectHazard(
      selectedZone,
      hazardType,
      severity,
      `Manual ${hazardType} in ${selectedZone}`,
      node_id
    );
    onClose();
  };

  const handleApplyCrowd = () => {
    onUpdateCrowd(selectedZone, crowdDensity, Math.round(crowdDensity * 20));
    onClose();
  };

  const zoneMap = [
    { id: 'zone_atrium', label: 'zone_atrium — West Atrium (Exit A Path)' },
    { id: 'zone_west', label: 'zone_west — West Main Corridor' },
    { id: 'zone_north', label: 'zone_north — North Wing (Exit B Path)' },
    { id: 'zone_east', label: 'zone_east — East Corridor (Exit C Path)' },
    { id: 'zone_south', label: 'zone_south — South Wing (Exit D Path)' },
    { id: 'zone_hall', label: 'zone_hall — Main Assembly Hall' },
    { id: 'zone_atrium_east', label: 'zone_atrium_east — East Wing Atrium' },
  ];

  const injectQuickHazard = (zone_id, type, sev, desc) => {
    onInjectHazard(zone_id, type, sev, desc);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 font-mono select-none">
      <div className="bg-[#111827] border border-[#1f293d] rounded-lg w-full max-w-md p-6 shadow-2xl space-y-5">
        <div className="flex items-center justify-between border-b border-[#1f293d] pb-3">
          <div className="flex items-center space-x-2">
            <Flame className="w-5 h-5 text-rose-500" />
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              MANUAL HAZARD / CROWD INJECTION
            </h3>
          </div>
          <button onClick={onClose} className="text-eoc-muted hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* QUICK PRESET ACTION BUTTONS */}
        <div className="bg-rose-950/30 border border-rose-600/30 rounded p-3 space-y-2">
          <div className="text-[10px] text-rose-400 font-bold uppercase tracking-wider flex items-center space-x-1">
            <Zap className="w-3.5 h-3.5" />
            <span>INSTANT REROUTE PRESETS</span>
          </div>

          <div className="grid grid-cols-1 gap-1.5 text-xs">
            <button
              onClick={() => injectQuickHazard('zone_atrium', 'fire', 0.9, 'Fire in West Atrium (Exit A blocked)')}
              className="w-full text-left px-3 py-1.5 rounded bg-rose-900/40 hover:bg-rose-800/60 border border-rose-600/50 text-rose-200 font-semibold flex items-center justify-between transition-colors"
            >
              <span>🔥 Inject Fire on Exit A Path (West Atrium)</span>
              <span className="text-[10px] bg-rose-950 px-1.5 py-0.5 rounded border border-rose-500/40">Reroute → Exit B</span>
            </button>

            <button
              onClick={() => injectQuickHazard('zone_north', 'fire', 0.9, 'Fire in North Wing (Exit B blocked)')}
              className="w-full text-left px-3 py-1.5 rounded bg-[#090d16] hover:bg-rose-950/40 border border-[#1f293d] hover:border-rose-500/40 text-gray-300 hover:text-rose-200 transition-colors"
            >
              <span>🔥 Inject Fire on Exit B Path (North Wing)</span>
            </button>
          </div>
        </div>

        {/* Target Zone Selector */}
        <div className="space-y-1.5 text-xs">
          <label className="text-eoc-muted font-semibold">TARGET BUILDING ZONE</label>
          <select
            value={selectedZone}
            onChange={(e) => setSelectedZone(e.target.value)}
            className="w-full bg-[#090d16] border border-[#1f293d] rounded px-3 py-2 text-white font-mono focus:border-eoc-accent focus:outline-none"
          >
            {zoneMap.map((z) => (
              <option key={z.id} value={z.id}>
                {z.label}
              </option>
            ))}
          </select>
        </div>

        {/* Hazard Inject Form */}
        <div className="bg-[#090d16] border border-[#1f293d] rounded p-4 space-y-3 text-xs">
          <div className="font-bold text-rose-400 flex items-center space-x-1.5">
            <AlertTriangle className="w-4 h-4" />
            <span>CUSTOM ENVIRONMENTAL HAZARD</span>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="text-eoc-muted text-[10px]">HAZARD TYPE</label>
              <select
                value={hazardType}
                onChange={(e) => setHazardType(e.target.value)}
                className="w-full bg-[#111827] border border-[#1f293d] rounded px-2 py-1.5 text-white"
              >
                <option value="fire">Fire 🔥</option>
                <option value="smoke">Heavy Smoke 💨</option>
                <option value="obstacle">Structural Debris 🧱</option>
              </select>
            </div>
            <div>
              <label className="text-eoc-muted text-[10px]">SEVERITY ({Math.round(severity * 100)}%)</label>
              <input
                type="range"
                min="0.2"
                max="1.0"
                step="0.05"
                value={severity}
                onChange={(e) => setSeverity(parseFloat(e.target.value))}
                className="w-full mt-2 accent-rose-500"
              />
            </div>
          </div>

          <button
            onClick={handleAddHazard}
            className="w-full bg-rose-600 hover:bg-rose-500 text-white font-bold py-2 rounded text-xs transition-colors shadow-lg"
          >
            INJECT HAZARD INTO {selectedZone.toUpperCase()}
          </button>
        </div>

        {/* Crowd Surge Control */}
        <div className="bg-[#090d16] border border-[#1f293d] rounded p-4 space-y-3 text-xs">
          <div className="font-bold text-amber-400 flex items-center space-x-1.5">
            <Users className="w-4 h-4" />
            <span>CROWD SURGE CONGESTION</span>
          </div>

          <div>
            <label className="text-eoc-muted text-[10px]">CROWD NORMALIZED DENSITY ({crowdDensity})</label>
            <input
              type="range"
              min="0.5"
              max="4.5"
              step="0.2"
              value={crowdDensity}
              onChange={(e) => setCrowdDensity(parseFloat(e.target.value))}
              className="w-full mt-2 accent-amber-500"
            />
          </div>

          <button
            onClick={handleApplyCrowd}
            className="w-full bg-amber-600 hover:bg-amber-500 text-white font-bold py-2 rounded text-xs transition-colors"
          >
            APPLY CROWD DENSITY TO {selectedZone.toUpperCase()}
          </button>
        </div>
      </div>
    </div>
  );
}
