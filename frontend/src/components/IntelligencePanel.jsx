import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  Lightbulb,
  Flame,
  TrendingUp,
  TrendingDown,
  Minus,
  Trash2,
  PieChart,
  Coins,
  Wallet,
  CheckCircle2,
  Clock,
  AlertCircle,
  ArrowRight,
  ExternalLink,
  Users,
  Sparkles,
} from 'lucide-react';
import BenchmarkPanel from './BenchmarkPanel';
import { fetchCapacityFlow } from '../services/api';

export default function IntelligencePanel({
  state,
  onRemoveHazard,
  peraAccount,
  onConnectPera,
  onExecutePayment,
  paymentStatus,
  paidData,
  isPaying,
}) {
  const [activeTab, setActiveTab] = useState('intelligence'); // 'intelligence' | 'benchmark' | 'x402'
  const [capacityFlow, setCapacityFlow] = useState(null);

  const activeRoute = state?.active_route;
  const hazards = state?.hazards || [];

  useEffect(() => {
    const loadCapacityFlow = async () => {
      try {
        const data = await fetchCapacityFlow();
        setCapacityFlow(data);
      } catch (err) {
        console.warn('Failed to fetch capacity flow:', err);
      }
    };
    loadCapacityFlow();
    const interval = setInterval(loadCapacityFlow, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="w-96 bg-[#111827] border-l border-[#1f293d] p-4 flex flex-col h-full overflow-y-auto font-mono select-none space-y-4">
      {/* TAB SWITCHER HEADER */}
      <div className="flex items-center space-x-1.5 bg-[#090d16] p-1 rounded border border-[#1f293d] text-xs">
        <button
          onClick={() => setActiveTab('intelligence')}
          className={`flex-1 py-1.5 rounded font-semibold text-center text-[11px] transition-all ${
            activeTab === 'intelligence'
              ? 'bg-[#1f293d] text-white shadow-sm'
              : 'text-eoc-muted hover:text-white'
          }`}
        >
          EVAC INTEL
        </button>
        <button
          onClick={() => setActiveTab('benchmark')}
          className={`flex-1 py-1.5 rounded font-semibold text-center text-[11px] transition-all ${
            activeTab === 'benchmark'
              ? 'bg-[#1f293d] text-sky-400 shadow-sm'
              : 'text-eoc-muted hover:text-white'
          }`}
        >
          BENCHMARKS
        </button>
        <button
          onClick={() => setActiveTab('x402')}
          className={`flex-1 py-1.5 rounded font-semibold text-center text-[11px] flex items-center justify-center space-x-1 transition-all ${
            activeTab === 'x402'
              ? 'bg-[#f5dc26]/20 text-[#f5dc26] border border-[#f5dc26]/40 shadow-sm'
              : 'text-amber-400/80 hover:text-amber-300'
          }`}
        >
          <Coins className="w-3 h-3 text-[#f5dc26]" />
          <span>x402 PAID</span>
        </button>
      </div>

      {activeTab === 'benchmark' ? (
        <BenchmarkPanel />
      ) : activeTab === 'x402' ? (
        /* X402 PAID INTELLIGENCE SECTION */
        <div className="space-y-3.5">
          {/* Header Protocol Info */}
          <div className="bg-[#090d16] border border-[#f5dc26]/30 rounded-lg p-3.5 relative overflow-hidden">
            <div className="flex items-center justify-between border-b border-[#1f293d] pb-2 mb-2.5">
              <div className="flex items-center space-x-1.5">
                <Coins className="w-4 h-4 text-[#f5dc26]" />
                <span className="text-xs font-bold text-white uppercase tracking-wider">
                  x402 AVM Gateway
                </span>
              </div>
              <span className="text-[9px] font-bold px-2 py-0.5 rounded bg-[#f5dc26]/10 text-[#f5dc26] border border-[#f5dc26]/30">
                TESTNET V2
              </span>
            </div>

            <div className="space-y-1.5 text-xs text-eoc-muted">
              <div className="flex justify-between">
                <span>Protected Endpoint:</span>
                <span className="text-gray-300 font-semibold text-[11px]">/api/v1/paid/emergency-analysis</span>
              </div>
              <div className="flex justify-between">
                <span>Required Price:</span>
                <span className="text-[#f5dc26] font-bold">0.005 USDC (5,000 atomic)</span>
              </div>
              <div className="flex justify-between">
                <span>Payment Asset:</span>
                <span className="text-sky-300 font-bold">USDC ASA 10458941</span>
              </div>
              <div className="flex justify-between">
                <span>Facilitator:</span>
                <span className="text-emerald-400 font-semibold text-[11px]">GoPlausible (Live)</span>
              </div>
            </div>

            {/* Wallet Connect or Trigger Payment */}
            <div className="mt-3 pt-2.5 border-t border-[#1f293d]">
              {!peraAccount ? (
                <button
                  onClick={onConnectPera}
                  className="w-full flex items-center justify-center space-x-2 py-2 px-3 rounded bg-[#f5dc26]/20 hover:bg-[#f5dc26]/30 border border-[#f5dc26]/50 text-[#f5dc26] font-bold text-xs transition-all shadow-sm"
                >
                  <Wallet className="w-4 h-4 text-[#f5dc26]" />
                  <span>Connect Pera Wallet to Pay</span>
                </button>
              ) : (
                <button
                  onClick={onExecutePayment}
                  disabled={isPaying}
                  className="w-full flex items-center justify-center space-x-2 py-2.5 px-3 rounded bg-emerald-600 hover:bg-emerald-500 disabled:bg-gray-800 border border-emerald-400/40 text-white font-bold text-xs transition-all shadow-md disabled:opacity-60 disabled:cursor-not-allowed"
                >
                  <Sparkles className="w-4 h-4 text-emerald-200" />
                  <span>{isPaying ? 'Processing Payment...' : 'Request Emergency Analysis (0.005 USDC)'}</span>
                </button>
              )}
            </div>
          </div>

          {/* Payment Progress Tracker Card */}
          {paymentStatus && (
            <div
              className={`bg-[#090d16] border rounded-lg p-3.5 space-y-2.5 transition-all ${
                paymentStatus.status === 'error'
                  ? 'border-rose-600/60'
                  : paymentStatus.status === 'success'
                  ? 'border-emerald-500/60'
                  : 'border-sky-500/40'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  {paymentStatus.status === 'pending' || paymentStatus.status === 'signing' || paymentStatus.status === 'settling' ? (
                    <Clock className="w-4 h-4 text-amber-400 animate-spin" />
                  ) : paymentStatus.status === 'success' ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  ) : (
                    <AlertCircle className="w-4 h-4 text-rose-400" />
                  )}
                  <span className="text-xs font-bold text-gray-200 uppercase">
                    {paymentStatus.title}
                  </span>
                </div>
                {paymentStatus.step > 0 && (
                  <span className="text-[10px] text-eoc-muted font-mono">
                    Step {paymentStatus.step}/{paymentStatus.totalSteps}
                  </span>
                )}
              </div>
              <p className="text-[11px] text-eoc-muted leading-relaxed">
                {paymentStatus.details}
              </p>
            </div>
          )}

          {/* Paid Intelligence Data Display */}
          {paidData ? (
            <div className="space-y-3">
              {/* Settlement Proof Card */}
              <div className="bg-[#090d16] border border-emerald-500/40 rounded-lg p-3 text-xs space-y-1.5">
                <div className="flex items-center justify-between border-b border-[#1f293d] pb-1.5">
                  <span className="text-[10px] text-emerald-400 font-bold uppercase tracking-wider">
                    ON-CHAIN SETTLEMENT VERIFIED
                  </span>
                  <span className="text-[9px] px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-500/30">
                    SETTLED
                  </span>
                </div>
                <div className="text-[11px] text-gray-300">
                  <div className="text-eoc-muted text-[10px]">Payment Signature:</div>
                  <div className="font-mono text-[10px] bg-[#111827] p-1.5 rounded text-sky-300 break-all border border-[#1f293d]">
                    {paidData.settlement?.payment_signature
                      ? `${paidData.settlement.payment_signature.slice(0, 32)}...`
                      : 'Verified by GoPlausible'}
                  </div>
                </div>
              </div>

              {/* Recommended Evac Route from Paid Payload */}
              <div className="bg-[#090d16] border border-[#1f293d] rounded-lg p-3 space-y-2">
                <div className="flex items-center justify-between border-b border-[#1f293d] pb-1.5">
                  <span className="text-[10px] text-eoc-muted font-bold uppercase tracking-wider">
                    PAID EVACUATION ROUTE
                  </span>
                  <span
                    className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${
                      paidData.recommended_evacuation_route?.is_safe
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                        : 'bg-rose-500/20 text-rose-400 border border-rose-500/40'
                    }`}
                  >
                    {paidData.recommended_evacuation_route?.is_safe ? 'OPTIMAL SAFE' : 'HAZARD BLOCKED'}
                  </span>
                </div>
                <div>
                  <div className="text-eoc-muted text-[10px]">TARGET EXIT</div>
                  <div className="text-sm font-bold text-white flex items-center space-x-1.5 mt-0.5">
                    <ShieldCheck className="w-4 h-4 text-emerald-400" />
                    <span>{paidData.recommended_evacuation_route?.target_exit_name || 'N/A'}</span>
                  </div>
                </div>
                <div className="text-[11px] text-eoc-muted bg-[#111827] p-2 rounded border border-[#1f293d]">
                  {paidData.route_explanation || paidData.recommended_evacuation_route?.explanation_summary}
                </div>
              </div>

              {/* Real-time Crowd Telemetry from Paid Payload */}
              {paidData.people_crowd_info && paidData.people_crowd_info.length > 0 && (
                <div className="bg-[#090d16] border border-[#1f293d] rounded-lg p-3 space-y-2">
                  <div className="flex items-center space-x-1.5 border-b border-[#1f293d] pb-1.5">
                    <Users className="w-3.5 h-3.5 text-sky-400" />
                    <span className="text-[10px] font-bold text-sky-400 uppercase tracking-wider">
                      CROWD ZONES ({paidData.people_crowd_info.length})
                    </span>
                  </div>
                  <div className="space-y-1.5 max-h-32 overflow-y-auto text-xs">
                    {paidData.people_crowd_info.map((z) => (
                      <div key={z.zone_id} className="flex justify-between items-center bg-[#111827] p-1.5 rounded border border-[#1f293d]">
                        <span className="font-bold text-gray-200">{z.zone_id}</span>
                        <div className="text-[11px] text-eoc-muted space-x-2">
                          <span>Count: <b className="text-white">{z.count}</b></span>
                          <span>Density: <b className="text-amber-400">{(z.density * 100).toFixed(0)}%</b></span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Congestion Predictions from Paid Payload */}
              {paidData.congestion_predictions && paidData.congestion_predictions.length > 0 && (
                <div className="bg-[#090d16] border border-[#1f293d] rounded-lg p-3 space-y-2">
                  <div className="flex items-center space-x-1.5 border-b border-[#1f293d] pb-1.5">
                    <TrendingUp className="w-3.5 h-3.5 text-amber-400" />
                    <span className="text-[10px] font-bold text-amber-400 uppercase tracking-wider">
                      LIGHTGBM PREDICTIONS
                    </span>
                  </div>
                  <div className="space-y-1.5 max-h-32 overflow-y-auto text-xs">
                    {paidData.congestion_predictions.map((p) => (
                      <div key={p.zone_id} className="flex justify-between items-center bg-[#111827] p-1.5 rounded border border-[#1f293d]">
                        <span className="font-bold text-gray-200">{p.zone_id}</span>
                        <div className="text-[10px] text-eoc-muted space-x-1.5">
                          <span>1m: <b className="text-sky-300">{(p.predicted_density_1m * 100).toFixed(0)}%</b></span>
                          <span>3m: <b className="text-amber-300">{(p.predicted_density_3m * 100).toFixed(0)}%</b></span>
                          <span className={`font-bold ${p.trend === 'rising' ? 'text-rose-400' : 'text-emerald-400'}`}>
                            {p.trend.toUpperCase()}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-[#090d16] border border-[#1f293d] rounded-lg p-4 text-center text-xs text-eoc-muted space-y-1.5">
              <Coins className="w-8 h-8 text-[#f5dc26]/40 mx-auto" />
              <div className="font-semibold text-gray-300">No Paid Intelligence Loaded Yet</div>
              <p className="text-[11px] leading-relaxed">
                Connect your Pera Testnet wallet and execute payment (0.005 USDC) to unlock real-time EOC emergency evacuation intelligence.
              </p>
            </div>
          )}
        </div>
      ) : (
        /* EXISTING STANDARD SIMULATION TAB */
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
                <div className="text-gray-200 font-bold">
                  {activeRoute?.is_safe && activeRoute?.total_risk_score < 99999 ? `${activeRoute?.total_distance || 0}m` : '—'}
                </div>
              </div>
              <div>
                <div className="text-eoc-muted text-[10px]">DYNAMIC RISK COST</div>
                <div className={activeRoute?.is_safe && activeRoute?.total_risk_score < 99999 ? "text-emerald-400 font-bold" : "text-rose-400 font-bold"}>
                  {activeRoute?.is_safe && activeRoute?.total_risk_score < 99999 ? (activeRoute?.total_risk_score || 0) : '—'}
                </div>
              </div>
              <div>
                <div className="text-eoc-muted text-[10px]">EST. EVAC TIME</div>
                <div className="text-amber-400 font-bold">
                  {activeRoute?.is_safe && activeRoute?.total_risk_score < 99999 ? `${activeRoute?.est_evacuation_time_sec || 0}s` : '—'}
                </div>
              </div>
              <div>
                <div className="text-eoc-muted text-[10px]">CORRIDOR STEPS</div>
                <div className="text-sky-400 font-bold">
                  {activeRoute?.is_safe && activeRoute?.total_risk_score < 99999 ? `${activeRoute?.path_nodes?.length || 0} zones` : '—'}
                </div>
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

