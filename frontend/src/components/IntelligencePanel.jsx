import React, { useState, useEffect } from 'react';
import { ShieldCheck, Lightbulb, Flame, TrendingUp, TrendingDown, Minus, Trash2, PieChart, BarChart2 } from 'lucide-react';
import BenchmarkPanel from './BenchmarkPanel';
import axios from 'axios';

export default function IntelligencePanel({ state, onRemoveHazard }) {
  const [activeTab, setActiveTab] = useState('intelligence'); // intelligence or benchmark
  const [capacityFlow, setCapacityFlow] = useState(null);

  const activeRoute = state?.active_route;
  const hazards = state?.hazards || [];
  const predictions = state?.predictions || {};

  useEffect(() => {
    const fetchCapacityFlow = async () => {
      try {
        const res = await axios.get('http://localhost:8000/api/v1/route/capacity-flow');
        setCapacityFlow(res.data);
      } catch (err) {
        console.warn('Failed to fetch capacity flow:', err);
      }
    };
    fetchCapacityFlow();
    const interval = setInterval(fetchCapacityFlow, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="w-96 bg-[#111827] border-l border-[#1f293d] p-4 flex flex-col h-full overflow-y-auto font-mono select-none space-y-4">
      {/* TAB SWITCHER HEADER */}
      <div className="flex items-center space-x-2 bg-[#090d16] p-1 rounded border border-[#1f293d] text-xs">
        <button
          onClick={() => setActiveTab('intelligence')}
          className={`flex-1 py-1.5 rounded font-semibold text-center transition-all ${
            activeTab === 'intelligence'
              ? 'bg-[#1f293d] text-white shadow-sm'
              : 'text-eoc-muted hover:text-white'
          }`}
        >
          EVAC INTELLIGENCE
        </button>
        <button
          onClick={() => setActiveTab('benchmark')}
          className={`flex-1 py-1.5 rounded font-semibold text-center transition-all ${
            activeTab === 'benchmark'
              ? 'bg-[#1f293d] text-sky-400 shadow-sm'
              : 'text-eoc-muted hover:text-white'
          }`}
        >
          ML BENCHMARKS
        </button>
      </div>

      {activeTab === 'benchmark' ? (
        <BenchmarkPanel />
      ) : (
        <>
          {/* SECTION 1: RECOMMENDED EVACUATION ROUTE */}
          <div className="bg-[#090d16] border border-[#1f293d] rounded-lg p-3.5 relative overflow-hidden">
            <div className="flex items-center justify-between border-b border-[#1f293d] pb-2 mb-2.5">
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

            <div className="mb-2.5">
              <div className="text-[10px] text-eoc-muted">TARGET EXIT POINT</div>
              <div className="text-base font-black text-white tracking-wide flex items-center space-x-2 mt-0.5">
                <ShieldCheck className="w-5 h-5 text-emerald-400" />
                <span>{activeRoute?.target_exit_name || 'CALCULATING...'}</span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs bg-[#111827] p-2 rounded border border-[#1f293d]">
              <div>
                <div className="text-eoc-muted text-[10px]">TOTAL DISTANCE</div>
                <div className="text-gray-200 font-bold">{activeRoute?.total_distance || 0}m</div>
              </div>
              <div>
                <div className="text-eoc-muted text-[10px]">DYNAMIC RISK COST</div>
                <div className="text-emerald-400 font-bold">{activeRoute?.total_risk_score || 0}</div>
              </div>
              <div>
                <div className="text-eoc-muted text-[10px]">EST. EVAC TIME</div>
                <div className="text-amber-400 font-bold">{activeRoute?.est_evacuation_time_sec || 0}s</div>
              </div>
              <div>
                <div className="text-eoc-muted text-[10px]">CORRIDOR STEPS</div>
                <div className="text-sky-400 font-bold">{activeRoute?.path_nodes?.length || 0} zones</div>
              </div>
            </div>
          </div>

          {/* SECTION 2: CAPACITY-AWARE MULTI-EXIT FLOW DISTRIBUTION */}
          {capacityFlow && capacityFlow.is_safe && capacityFlow.exit_distributions?.length > 1 && (
            <div className="bg-[#090d16] border border-amber-950/60 rounded-lg p-3.5">
              <div className="flex items-center space-x-2 border-b border-[#1f293d] pb-2 mb-2.5">
                <PieChart className="w-4 h-4 text-amber-400" />
                <h3 className="text-xs font-bold text-amber-400 uppercase tracking-wider">
                  MULTI-EXIT FLOW ALLOCATION
                </h3>
              </div>

              <div className="space-y-2 text-xs">
                {capacityFlow.exit_distributions.map((dist) => (
                  <div key={dist.exit_id} className="space-y-1">
                    <div className="flex justify-between text-[11px]">
                      <span className="font-semibold text-gray-200">{dist.exit_name}</span>
                      <span className="font-bold text-amber-400">{dist.flow_percentage}% ({dist.recommended_count} people)</span>
                    </div>
                    <div className="w-full bg-[#111827] rounded-full h-2 overflow-hidden border border-[#1f293d]">
                      <div
                        className="bg-amber-500 h-full rounded-full transition-all duration-500"
                        style={{ width: `${dist.flow_percentage}%` }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* SECTION 3: EXPLAINABILITY RATIONALE */}
          <div className="bg-[#090d16] border border-sky-950/60 rounded-lg p-3.5">
            <div className="flex items-center space-x-2 border-b border-[#1f293d] pb-2 mb-2">
              <Lightbulb className="w-4 h-4 text-sky-400" />
              <h3 className="text-xs font-bold text-sky-400 uppercase tracking-wider">
                ROUTE EXPLAINABILITY
              </h3>
            </div>

            <p className="text-xs font-semibold text-gray-200 mb-2">
              {activeRoute?.explanation_summary || 'Analyzing building topology...'}
            </p>

            <ul className="space-y-1.5 text-[11px] text-eoc-muted">
              {activeRoute?.explanation_details?.map((detail, idx) => (
                <li key={idx} className="flex items-start space-x-1.5 bg-[#111827] p-2 rounded border border-[#1f293d]">
                  <span className="text-sky-400 font-bold font-mono">›</span>
                  <span className="leading-relaxed">{detail}</span>
                </li>
              )) || <li className="text-xs italic">No route details.</li>}
            </ul>
          </div>

          {/* SECTION 4: ACTIVE HAZARDS MONITOR */}
          <div className="bg-[#090d16] border border-[#1f293d] rounded-lg p-3.5">
            <div className="flex items-center justify-between border-b border-[#1f293d] pb-2 mb-2">
              <div className="flex items-center space-x-2">
                <Flame className="w-4 h-4 text-rose-500" />
                <h3 className="text-xs font-bold text-rose-400 uppercase tracking-wider">
                  ACTIVE HAZARDS ({hazards.length})
                </h3>
              </div>
            </div>

            {hazards.length === 0 ? (
              <div className="text-xs text-eoc-muted italic bg-[#111827] p-2 rounded text-center border border-[#1f293d]">
                Zero active hazards.
              </div>
            ) : (
              <div className="space-y-1.5 max-h-32 overflow-y-auto">
                {hazards.map((h) => (
                  <div
                    key={h.id}
                    className="bg-[#111827] p-2 rounded border border-rose-950/60 flex items-center justify-between text-xs"
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
        </>
      )}
    </div>
  );
}
