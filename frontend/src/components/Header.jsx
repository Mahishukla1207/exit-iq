import React, { useState, useEffect } from 'react';
import { ShieldAlert, Cpu, Camera, RefreshCw, Volume2, VolumeX } from 'lucide-react';
import { setAudioMuted, isAudioMuted } from '../utils/audio';

export default function Header({ mode, setMode, activeScenario, onRefresh }) {
  const [timeStr, setTimeStr] = useState('');
  const [muted, setMuted] = useState(isAudioMuted());

  useEffect(() => {
    const updateTime = () => {
      const d = new Date();
      setTimeStr(d.toTimeString().split(' ')[0] + '.' + String(d.getMilliseconds()).padStart(3, '0'));
    };
    updateTime();
    const interval = setInterval(updateTime, 100);
    return () => clearInterval(interval);
  }, []);

  const handleToggleMute = () => {
    const nextMuted = !muted;
    setMuted(nextMuted);
    setAudioMuted(nextMuted);
  };

  return (
    <header className="bg-[#111827] border-b border-[#1f293d] px-6 py-3 flex items-center justify-between shadow-lg select-none">
      {/* Brand & Tagline */}
      <div className="flex items-center space-x-4">
        <div className="flex items-center justify-center w-10 h-10 rounded bg-rose-950/60 border border-rose-600/50 text-rose-400">
          <ShieldAlert className="w-6 h-6 animate-pulse" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-xl font-black tracking-widest text-white uppercase font-mono">
              EXIT<span className="text-rose-500">IQ</span>
            </h1>
            <span className="text-[10px] font-mono tracking-wider font-semibold px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20 uppercase">
              EOC v1.0
            </span>
          </div>
          <p className="text-xs text-eoc-muted font-medium italic">
            "Nearest exit nahi. Safest exit."
          </p>
        </div>
      </div>

      {/* Center Mode Switcher */}
      <div className="flex items-center space-x-2 bg-[#090d16] p-1 rounded-md border border-[#1f293d]">
        <button
          onClick={() => setMode('simulation')}
          className={`flex items-center space-x-2 px-3.5 py-1.5 rounded text-xs font-semibold font-mono transition-all ${
            mode === 'simulation'
              ? 'bg-rose-600 text-white shadow-sm'
              : 'text-eoc-muted hover:text-white hover:bg-[#111827]'
          }`}
        >
          <Cpu className="w-3.5 h-3.5" />
          <span>SIMULATION MESH</span>
        </button>

        <button
          onClick={() => setMode('cctv')}
          className={`flex items-center space-x-2 px-3.5 py-1.5 rounded text-xs font-semibold font-mono transition-all ${
            mode === 'cctv'
              ? 'bg-amber-600 text-white shadow-sm'
              : 'text-eoc-muted hover:text-white hover:bg-[#111827]'
          }`}
        >
          <Camera className="w-3.5 h-3.5" />
          <span>CCTV / VIDEO MODE</span>
        </button>
      </div>

      {/* Right Telemetry Controls */}
      <div className="flex items-center space-x-4 font-mono text-xs">
        <button
          onClick={handleToggleMute}
          className={`flex items-center space-x-1.5 px-2.5 py-1 rounded border transition-colors ${
            muted
              ? 'bg-gray-800 text-gray-400 border-gray-700'
              : 'bg-emerald-950/40 text-emerald-400 border-emerald-500/40'
          }`}
          title="Toggle Voice Alerts"
        >
          {muted ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
          <span>{muted ? 'VOICE OFF' : 'VOICE ON'}</span>
        </button>

        <div className="flex items-center space-x-2 bg-[#090d16] px-3 py-1 rounded border border-[#1f293d]">
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
          </span>
          <span className="text-emerald-400 font-semibold uppercase tracking-wider text-[11px]">LIVE</span>
        </div>

        <div className="text-right">
          <div className="text-eoc-muted text-[10px]">SCENARIO</div>
          <div className="text-amber-400 font-bold tracking-wide">{activeScenario || 'NORMAL'}</div>
        </div>

        <div className="text-right min-w-[95px]">
          <div className="text-eoc-muted text-[10px]">CLOCK</div>
          <div className="text-gray-200 font-bold">{timeStr}</div>
        </div>

        <button
          onClick={onRefresh}
          className="p-2 rounded bg-[#090d16] hover:bg-[#1f293d] border border-[#1f293d] text-eoc-muted hover:text-white transition-colors"
          title="Refresh Telemetry"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
}
