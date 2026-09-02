import React, { useRef, useEffect, useState } from 'react';
import { Camera, Users, Zap, Play, Pause, Activity, RefreshCw, Layers } from 'lucide-react';
import { startCVStream, stopCVStream, fetchCVStatus } from '../services/api';

export default function CCTVStreamPlayer({ state }) {
  const canvasRef = useRef(null);
  const imgRef = useRef(null);

  const [feedSource, setFeedSource] = useState('live_ucf'); // 'live_ucf' or 'simulated'
  const [selectedCam, setSelectedCam] = useState('cam1');
  const [isPlaying, setIsPlaying] = useState(true);
  const [cvStatus, setCvStatus] = useState(null);
  const [imgLoaded, setImgLoaded] = useState(false);

  const cameraChannels = [
    { id: 'cam1', name: 'CAM 1 — West Atrium (Exit A)', zone: 'zone_atrium' },
    { id: 'cam2', name: 'CAM 2 — North Hallway (Exit B)', zone: 'zone_north' },
    { id: 'cam3', name: 'CAM 3 — East Corridor (Exit C)', zone: 'zone_east' },
    { id: 'cam4', name: 'CAM 4 — South Stairwell (Exit D)', zone: 'zone_south' },
  ];

  const currentCam = cameraChannels.find((c) => c.id === selectedCam) || cameraChannels[0];
  const activeZoneCrowd = state?.crowd_zones?.[currentCam.zone];
  const activeHazards = (state?.hazards || []).filter((h) => h.zone_id === currentCam.zone);

  // Poll CV pipeline status
  useEffect(() => {
    let interval;
    if (feedSource === 'live_ucf') {
      const checkStatus = async () => {
        try {
          const res = await fetchCVStatus();
          setCvStatus(res);
          if (!res.is_running && isPlaying) {
            await startCVStream();
          }
        } catch (e) {
          console.warn('CV Status check failed:', e);
        }
      };
      checkStatus();
      interval = setInterval(checkStatus, 2000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [feedSource, isPlaying]);

  const handleToggleFeed = async (newSource) => {
    setFeedSource(newSource);
    if (newSource === 'live_ucf') {
      try {
        await startCVStream();
        setIsPlaying(true);
      } catch (err) {
        console.error('Failed to start CV pipeline:', err);
      }
    } else {
      try {
        await stopCVStream();
      } catch (err) {
        console.error('Failed to stop CV pipeline:', err);
      }
    }
  };

  // Render simulated canvas feed if feedSource === 'simulated'
  useEffect(() => {
    if (feedSource !== 'simulated') return;

    let animId;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let frameTick = 0;

    const renderCCTVFrame = () => {
      frameTick++;
      const w = canvas.width;
      const h = canvas.height;

      // Dark CCTV Video Room Background
      ctx.fillStyle = '#060911';
      ctx.fillRect(0, 0, w, h);

      // Draw CCTV Grid Scan Lines
      ctx.strokeStyle = 'rgba(31, 41, 61, 0.3)';
      ctx.lineWidth = 1;
      for (let y = 0; y < h; y += 12) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(w, y);
        ctx.stroke();
      }

      // Draw Camera Feed Architectural Outlines
      ctx.strokeStyle = '#1e293b';
      ctx.lineWidth = 3;
      ctx.strokeRect(60, 50, w - 120, h - 100);
      ctx.strokeRect(180, 50, w - 360, h - 100);

      // Draw Active Hazards on Video Feed if present
      if (activeHazards.length > 0) {
        activeHazards.forEach((haz) => {
          ctx.fillStyle = haz.type === 'fire' ? 'rgba(239, 68, 68, 0.35)' : 'rgba(156, 163, 175, 0.35)';
          ctx.beginPath();
          ctx.arc(w / 2, h / 2, 70 + Math.sin(frameTick * 0.1) * 8, 0, Math.PI * 2);
          ctx.fill();

          ctx.fillStyle = '#ef4444';
          ctx.font = 'bold 20px Fira Code';
          ctx.fillText(
            haz.type === 'fire' ? '⚠️ DANGER: ACTIVE FIRE DETECTED' : '💨 HEAVY SMOKE DETECTED',
            w / 2 - 140,
            h / 2
          );
        });
      }

      // Draw YOLO Person Detection Bounding Boxes & Tracking Vectors
      const personCount = activeZoneCrowd ? Math.max(3, activeZoneCrowd.count) : 6;
      for (let i = 0; i < personCount; i++) {
        const offsetX = Math.sin((frameTick + i * 40) * 0.03) * 120;
        const offsetY = Math.cos((frameTick + i * 30) * 0.04) * 80;

        const bx = 160 + (i % 5) * 110 + offsetX;
        const by = 120 + Math.floor(i / 5) * 120 + offsetY;
        const bw = 55;
        const bh = 95;

        // Bounding Box
        ctx.strokeStyle = activeHazards.length > 0 ? '#f59e0b' : '#10b981';
        ctx.lineWidth = 2;
        ctx.strokeRect(bx, by, bw, bh);

        // Bounding Box Header Label
        ctx.fillStyle = activeHazards.length > 0 ? '#f59e0b' : '#10b981';
        ctx.fillRect(bx, by - 18, bw, 18);
        ctx.fillStyle = '#090d16';
        ctx.font = 'bold 10px Fira Code';
        ctx.fillText(`P#${100 + i}`, bx + 4, by - 5);

        // Velocity Tracking Vector Arrow
        const vx = Math.cos((frameTick + i) * 0.05) * 18;
        const vy = Math.sin((frameTick + i) * 0.05) * 18;
        ctx.strokeStyle = '#38bdf8';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(bx + bw / 2, by + bh / 2);
        ctx.lineTo(bx + bw / 2 + vx, by + bh / 2 + vy);
        ctx.stroke();
      }

      // CCTV Telemetry OSD Overlay
      ctx.fillStyle = '#34d399';
      ctx.font = 'bold 12px Fira Code';
      ctx.fillText(`● REC [SIMULATED FEED] — ${currentCam.name}`, 15, 25);
      ctx.fillText(`SIMULATED PERSONS: ${personCount} | FPS: 30.0`, 15, h - 15);

      if (isPlaying) {
        animId = requestAnimationFrame(renderCCTVFrame);
      }
    };

    renderCCTVFrame();

    return () => {
      if (animId) cancelAnimationFrame(animId);
    };
  }, [feedSource, selectedCam, isPlaying, activeZoneCrowd, activeHazards]);

  const streamUrl = 'http://localhost:8000/api/v1/cv/stream';

  return (
    <div className="relative w-full h-full bg-[#090d16] flex flex-col items-center justify-center p-4 font-mono select-none">
      {/* CCTV Feed Mode & Camera Selector Bar */}
      <div className="absolute top-4 left-4 right-4 z-10 flex items-center justify-between bg-[#111827]/90 backdrop-blur border border-[#1f293d] p-2 rounded shadow-md">
        {/* Left: Feed Source Selector */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => handleToggleFeed('live_ucf')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded text-xs font-bold transition-all ${
              feedSource === 'live_ucf'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'text-eoc-muted hover:text-white hover:bg-[#1f293d]'
            }`}
          >
            <Camera className="w-3.5 h-3.5" />
            <span>LIVE UCF CV FEED</span>
          </button>

          <button
            onClick={() => handleToggleFeed('simulated')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded text-xs font-bold transition-all ${
              feedSource === 'simulated'
                ? 'bg-amber-600 text-white shadow-sm'
                : 'text-eoc-muted hover:text-white hover:bg-[#1f293d]'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>SIMULATED FEED</span>
          </button>
        </div>

        {/* Center: Camera Channel Selector */}
        <div className="hidden md:flex items-center space-x-1">
          {cameraChannels.map((cam) => (
            <button
              key={cam.id}
              onClick={() => setSelectedCam(cam.id)}
              className={`px-2.5 py-1 rounded text-[11px] font-semibold transition-all ${
                selectedCam === cam.id
                  ? 'bg-gray-800 text-emerald-400 border border-emerald-500/40'
                  : 'text-eoc-muted hover:text-white hover:bg-[#1f293d]'
              }`}
            >
              {cam.id.toUpperCase()}
            </button>
          ))}
        </div>

        {/* Right: Live Video Status Indicator */}
        <div className="flex items-center space-x-3 text-xs">
          <div className="flex items-center space-x-1.5">
            <span className="relative flex h-2 w-2">
              <span
                className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                  feedSource === 'live_ucf' ? 'bg-emerald-400' : 'bg-amber-400'
                }`}
              ></span>
              <span
                className={`relative inline-flex rounded-full h-2 w-2 ${
                  feedSource === 'live_ucf' ? 'bg-emerald-500' : 'bg-amber-500'
                }`}
              ></span>
            </span>
            <span className="text-gray-200 font-semibold text-[11px]">
              {feedSource === 'live_ucf' ? 'UCF CROWD STREAM' : 'SIMULATION MESH'}
            </span>
          </div>

          {cvStatus?.video_info && (
            <span className="text-[10px] text-eoc-muted hidden lg:inline">
              File: {cvStatus.video_info.video_path}
            </span>
          )}
        </div>
      </div>

      {/* Main Stream Player Viewport */}
      <div className="relative mt-8 border border-[#1f293d] rounded-lg overflow-hidden shadow-2xl bg-[#060911] flex items-center justify-center min-w-[780px] min-h-[490px]">
        {feedSource === 'live_ucf' ? (
          <div className="relative w-[780px] h-[490px] flex items-center justify-center">
            <img
              ref={imgRef}
              src={streamUrl}
              alt="Live UCF Video Stream with YOLO + Tracking"
              onLoad={() => setImgLoaded(true)}
              onError={(e) => {
                setImgLoaded(false);
              }}
              className="w-full h-full object-contain"
            />

            {!imgLoaded && (
              <div className="absolute inset-0 flex flex-col items-center justify-center bg-[#060911]/90 text-eoc-muted space-y-3 font-mono">
                <RefreshCw className="w-8 h-8 animate-spin text-emerald-500" />
                <div className="text-sm font-semibold text-white">Connecting to UCF Video Stream...</div>
                <div className="text-xs text-eoc-muted">
                  YOLOv8 + Centroid Tracking Pipeline Loading
                </div>
              </div>
            )}
          </div>
        ) : (
          <canvas ref={canvasRef} width={780} height={490} className="w-full h-full" />
        )}
      </div>

      {/* Footer Pipeline Telemetry */}
      <div className="absolute bottom-3 left-6 right-6 z-10 flex items-center justify-between text-[11px] text-eoc-muted">
        <div>
          <span className="text-emerald-400 font-bold">UCF → YOLOv8 → Tracking → Zone Analytics → LightGBM → Risk Engine → Risk-Aware A*</span>
        </div>
        <div>
          Confidence Threshold: <span className="text-white font-semibold">0.25</span> | Class: <span className="text-white font-semibold">Person (0)</span>
        </div>
      </div>
    </div>
  );
}
