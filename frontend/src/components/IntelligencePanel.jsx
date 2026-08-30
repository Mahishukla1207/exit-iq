import React from 'react';
import { ShieldCheck, AlertTriangle, Lightbulb, Flame, TrendingUp, TrendingDown, Minus, Trash2 } from 'lucide-react';

export default function IntelligencePanel({ state, onRemoveHazard }) {
  const activeRoute = state?.active_route;
  const hazards = state?.hazards || [];
  const predictions = state?.predictions || {};

  return (
    <div className="w-96 bg-[#111827] border-l border-[#1f293d] p-5 flex flex-col h-full overflow-y-auto font-mono select-none space-y-5">
      {/* SECTION 1: RECOMMENDED EVACUATION ROUTE */}
      <div className="bg-[#090d16] border border-[#1f293d] rounded-lg p-4 relative overflow-hidden">
        <div className="flex items-center justify-between border-b border-[#1f293d] pb-2 mb-3">
          <span className="text-[10px] text-eoc-muted font-bold uppercase tracking-widest">
            ACTIVE RECOMMENDED ROUTE
          </span>
          <span
            className={`text-[10px] font-bold px-2 py-0.5 rounded ${
              activeRoute?.is_safe
                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                : 'bg-rose-500/20 text-rose-400 border border-rose-500/40 animate-pulse'
            }`}
          >
            {activeRoute?.is_safe ? '● OPTIMAL SAFE PATH' : '⚠️ NO SAFE ROUTE'}
          </span>
        </div>

        <div className="mb-3">
          <div className="text-xs text-eoc-muted">TARGET EXIT POINT</div>
          <div className="text-lg font-black text-white tracking-wide flex items-center space-x-2 mt-0.5">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            <span>{activeRoute?.target_exit_name || 'CALCULATING...'}</span>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2 text-xs bg-[#111827] p-2.5 rounded border border-[#1f293d]">
          <div>
            <div className="text-eoc-muted text-[10px]">TOTAL DISTANCE</div>
            <div className="text-gray-200 font-bold">{activeRoute?.total_distance || 0} meters</div>
          </div>
          <div>
            <div className="text-eoc-muted text-[10px]">DYNAMIC RISK COST</div>
            <div className="text-emerald-400 font-bold">{activeRoute?.total_risk_score || 0}</div>
          </div>
          <div>
            <div className="text-eoc-muted text-[10px]">EST. EVAC TIME</div>
            <div className="text-amber-400 font-bold">{activeRoute?.est_evacuation_time_sec || 0} sec</div>
          </div>
          <div>
            <div className="text-eoc-muted text-[10px]">CORRIDOR STEPS</div>
            <div className="text-sky-400 font-bold">{activeRoute?.path_nodes?.length || 0} zones</div>
          </div>
        </div>
      </div>

      {/* SECTION 2: EXPLAINABILITY ENGINE (WHY THIS ROUTE?) */}
      <div className="bg-[#090d16] border border-sky-950/60 rounded-lg p-4 relative">
        <div className="flex items-center space-x-2 border-b border-[#1f293d] pb-2 mb-3">
          <Lightbulb className="w-4 h-4 text-sky-400" />
          <h3 className="text-xs font-bold text-sky-400 uppercase tracking-wider">
            ROUTE EXPLAINABILITY RATIONALE
          </h3>
        </div>

        <p className="text-xs font-semibold text-gray-200 mb-2">
          {activeRoute?.explanation_summary || 'Analyzing current building risk topology...'}
        </p>

        <ul className="space-y-2 text-[11px] text-eoc-muted">
          {activeRoute?.explanation_details?.map((detail, idx) => (
            <li key={idx} className="flex items-start space-x-2 bg-[#111827] p-2 rounded border border-[#1f293d]">
              <span className="text-sky-400 font-bold font-mono">›</span>
              <span className="leading-relaxed">{detail}</span>
            </li>
          )) || <li className="text-xs italic">No route details available.</li>}
        </ul>
      </div>

      {/* SECTION 3: ACTIVE HAZARDS MONITOR */}
      <div className="bg-[#090d16] border border-[#1f293d] rounded-lg p-4">
        <div className="flex items-center justify-between border-b border-[#1f293d] pb-2 mb-3">
          <div className="flex items-center space-x-2">
            <Flame className="w-4 h-4 text-rose-500" />
            <h3 className="text-xs font-bold text-rose-400 uppercase tracking-wider">
              ACTIVE HAZARDS ({hazards.length})
            </h3>
          </div>
        </div>

        {hazards.length === 0 ? (
          <div className="text-xs text-eoc-muted italic bg-[#111827] p-2.5 rounded text-center border border-[#1f293d]">
            Zero active environmental hazards detected.
          </div>
        ) : (
          <div className="space-y-2 max-h-36 overflow-y-auto">
            {hazards.map((h) => (
              <div
                key={h.id}
                className="bg-[#111827] p-2.5 rounded border border-rose-950/60 flex items-center justify-between text-xs"
              >
                <div>
                  <div className="font-bold text-rose-300 uppercase">{h.description || `${h.type} in ${h.zone_id}`}</div>
                  <div className="text-[10px] text-eoc-muted">
                    Severity: <span className="text-rose-400 font-bold">{Math.round(h.severity * 100)}%</span>
                  </div>
                </div>
                <button
                  onClick={() => onRemoveHazard(h.id)}
                  className="p-1 rounded bg-rose-950/50 hover:bg-rose-900/80 text-rose-400 hover:text-white transition-colors"
                  title="Clear Hazard"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* SECTION 4: LIGHTGBM PREDICTED CONGESTION FORECAST */}
      <div className="bg-[#090d16] border border-[#1f293d] rounded-lg p-4 flex-1">
        <div className="flex items-center justify-between border-b border-[#1f293d] pb-2 mb-3">
          <div className="flex items-center space-x-2">
            <TrendingUp className="w-4 h-4 text-amber-400" />
            <h3 className="text-xs font-bold text-amber-400 uppercase tracking-wider">
              LIGHTGBM CONGESTION FORECAST
            </h3>
          </div>
        </div>

        <div className="space-y-2 max-h-48 overflow-y-auto text-xs">
          {Object.entries(predictions).map(([zid, pred]) => {
            const isHigh = pred.predicted_congestion_prob > 0.5;
            return (
              <div
                key={zid}
                className={`p-2.5 rounded border flex items-center justify-between ${
                  isHigh
                    ? 'bg-amber-950/20 border-amber-500/30'
                    : 'bg-[#111827] border-[#1f293d]'
                }`}
              >
                <div>
                  <div className="font-bold text-gray-200 uppercase">{zid}</div>
                  <div className="text-[10px] text-eoc-muted">
                    Current: {pred.current_density} p/m² | T+1m: <span className="text-amber-400 font-bold">{pred.predicted_density_1m} p/m²</span>
                  </div>
                </div>

                <div className="text-right">
                  <span
                    className={`inline-flex items-center space-x-1 text-[10px] font-bold px-1.5 py-0.5 rounded ${
                      pred.trend === 'RISING'
                        ? 'bg-rose-500/20 text-rose-400'
                        : pred.trend === 'FALLING'
                        ? 'bg-emerald-500/20 text-emerald-400'
                        : 'bg-gray-700/50 text-gray-400'
                    }`}
                  >
                    {pred.trend === 'RISING' ? (
                      <TrendingUp className="w-3 h-3" />
                    ) : pred.trend === 'FALLING' ? (
                      <TrendingDown className="w-3 h-3" />
                    ) : (
                      <Minus className="w-3 h-3" />
                    )}
                    <span>{pred.trend}</span>
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
