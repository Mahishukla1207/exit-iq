import React from 'react';
import { Play, Pause, RotateCcw, AlertTriangle, ShieldCheck, Flame, Users, Sparkles, AlertOctagon } from 'lucide-react';

export default function ScenarioBar({
  activeScenario,
  onSelectScenario,
  isRunning,
  onToggleRun,
  onReset,
  onOpenHazardModal,
}) {
  const scenarios = [
    { id: 'NORMAL', label: '1. Normal Evacuation', icon: ShieldCheck, color: 'hover:border-emerald-500/50 text-emerald-400' },
    { id: 'FIRE_CORRIDOR', label: '2. Fire Blocks Corridor', icon: Flame, color: 'hover:border-rose-500/50 text-rose-400' },
    { id: 'EXIT_CONGESTION', label: '3. Exit Congestion', icon: Users, color: 'hover:border-amber-500/50 text-amber-400' },
    { id: 'PREDICTIVE_CONGESTION', label: '4. Predictive Congestion', icon: Sparkles, color: 'hover:border-sky-500/50 text-sky-400' },
    { id: 'MULTI_HAZARD', label: '5. Multi-Hazard', icon: AlertTriangle, color: 'hover:border-purple-500/50 text-purple-400' },
    { id: 'NO_SAFE_ROUTE', label: '6. No Safe Route', icon: AlertOctagon, color: 'hover:border-red-600/50 text-red-500' },
  ];

  return (
    <div className="bg-[#0b101c] border-b border-[#1f293d] px-6 py-2.5 flex items-center justify-between font-mono text-xs select-none">
      {/* Demo Scenario Buttons */}
      <div className="flex items-center space-x-2">
        <span className="text-eoc-muted font-semibold tracking-wider text-[11px] uppercase mr-1">
          DEMO SCENARIOS:
        </span>
        {scenarios.map((sc) => {
          const Icon = sc.icon;
          const isActive = activeScenario === sc.id;
          return (
            <button
              key={sc.id}
              onClick={() => onSelectScenario(sc.id)}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded border transition-all ${
                isActive
                  ? 'bg-[#1e293b] border-eoc-accent text-white font-bold shadow-sm'
                  : 'bg-[#111827] border-[#1f293d] text-eoc-muted hover:text-white ' + sc.color
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{sc.label}</span>
            </button>
          );
        })}
      </div>

      {/* Simulation Controls */}
      <div className="flex items-center space-x-2">
        <button
          onClick={onToggleRun}
          className={`flex items-center space-x-1.5 px-3 py-1.5 rounded font-semibold transition-all ${
            isRunning
              ? 'bg-amber-600/20 text-amber-400 border border-amber-500/30 hover:bg-amber-600/30'
              : 'bg-emerald-600/20 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-600/30'
          }`}
        >
          {isRunning ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
          <span>{isRunning ? 'PAUSE TICK' : 'START SIMULATION'}</span>
        </button>

        <button
          onClick={onReset}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-[#111827] hover:bg-[#1f293d] border border-[#1f293d] text-eoc-muted hover:text-white transition-all"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>RESET</span>
        </button>

        <button
          onClick={onOpenHazardModal}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-rose-950/40 hover:bg-rose-900/60 border border-rose-600/40 text-rose-300 font-semibold transition-all"
        >
          <Flame className="w-3.5 h-3.5" />
          <span>+ INJECT HAZARD</span>
        </button>
      </div>
    </div>
  );
}
