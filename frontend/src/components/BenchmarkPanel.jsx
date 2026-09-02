import React, { useState, useEffect } from 'react';
import { Cpu, CheckCircle, RefreshCw, BarChart2 } from 'lucide-react';
import { fetchMLBenchmark } from '../services/api';

export default function BenchmarkPanel() {
  const [benchmarkData, setBenchmarkData] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchBenchmark = async () => {
    setLoading(true);
    try {
      const data = await fetchMLBenchmark();
      setBenchmarkData(data);
    } catch (err) {
      console.warn('Failed to fetch benchmark:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBenchmark();
  }, []);

  return (
    <div className="bg-[#090d16] border border-[#1f293d] rounded-lg p-4 font-mono select-none">
      <div className="flex items-center justify-between border-b border-[#1f293d] pb-2.5 mb-3">
        <div className="flex items-center space-x-2">
          <BarChart2 className="w-4 h-4 text-sky-400" />
          <h3 className="text-xs font-bold text-sky-400 uppercase tracking-wider">
            ML MODEL COMPARATIVE BENCHMARK
          </h3>
        </div>
        <button
          onClick={fetchBenchmark}
          disabled={loading}
          className="p-1.5 rounded bg-[#111827] hover:bg-[#1f293d] border border-[#1f293d] text-eoc-muted hover:text-white transition-colors"
          title="Re-run ML Benchmark"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {loading ? (
        <div className="text-xs text-eoc-muted italic py-4 text-center">
          Evaluating LightGBM vs XGBoost vs Random Forest...
        </div>
      ) : benchmarkData ? (
        <div className="space-y-3">
          <div className="text-[11px] text-eoc-muted flex justify-between">
            <span>Target: <strong className="text-gray-200">Future Congestion Prob</strong></span>
            <span>Test Samples: <strong className="text-sky-400">{benchmarkData.num_test_samples}</strong></span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-[#1f293d] text-eoc-muted text-[10px] uppercase">
                  <th className="py-1.5 px-2">MODEL</th>
                  <th className="py-1.5 px-2">MAE</th>
                  <th className="py-1.5 px-2">RMSE</th>
                  <th className="py-1.5 px-2">R² SCORE</th>
                  <th className="py-1.5 px-2">LATENCY</th>
                </tr>
              </thead>
              <tbody>
                {benchmarkData.models_evaluated.map((m, idx) => (
                  <tr
                    key={idx}
                    className={`border-b border-[#1f293d]/50 ${
                      m.is_recommended ? 'bg-sky-950/30 text-sky-200 font-bold' : 'text-gray-300'
                    }`}
                  >
                    <td className="py-2 px-2 flex items-center space-x-1.5">
                      {m.is_recommended && <CheckCircle className="w-3.5 h-3.5 text-sky-400" />}
                      <span>{m.model_name}</span>
                    </td>
                    <td className="py-2 px-2">{m.mae}</td>
                    <td className="py-2 px-2">{m.rmse}</td>
                    <td className="py-2 px-2">{m.r2_score}</td>
                    <td className="py-2 px-2 text-emerald-400">{m.inference_latency_us} µs</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="text-xs text-rose-400">Benchmark offline.</div>
      )}
    </div>
  );
}
