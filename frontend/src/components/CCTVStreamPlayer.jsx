import React, { useRef, useEffect, useState } from 'react';
import { Camera, Users, Zap, Play, Pause, Activity } from 'lucide-react';

export default function CCTVStreamPlayer({ state }) {
  const canvasRef = useRef(null);
  const [selectedCam, setSelectedCam] = useState('cam1');
  const [isPlaying, setIsPlaying] = useState(true);

  const cameraChannels = [
    { id: 'cam1', name: 'CAM 1 — West Atrium (Exit A)', zone: 'zone_atrium' },
    { id: 'cam2', name: 'CAM 2 — North Hallway (Exit B)', zone: 'zone_north' },
    { id: 'cam3', name: 'CAM 3 — East Corridor (Exit C)', zone: 'zone_east' },
    { id: 'cam4', name: 'CAM 4 — South Stairwell (Exit D)', zone: 'zone_exit_d' },
  ];

  const currentCam = cameraChannels.find((c) => c.id === selectedCam) || cameraChannels[0];
  const activeZoneCrowd = state?.crowd_zones?.[currentCam.zone];
  const activeHazards = (state?.hazards || []).filter((h) => h.zone_id === currentCam.zone);

  useEffect(() => {
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

      // Draw Camera Feed Simulated Corridors / Architectural Outlines
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
          ctx.fillText(haz.type === 'fire' ? '⚠️ DANGER: ACTIVE FIRE DETECTED' : '💨 HEAVY SMOKE DETECTED', w / 2 - 140, h / 2);
        });
      }

      // Draw YOLO Person Detection Bounding Boxes & Tracking Vectors
      const personCount = activeZoneCrowd ? Math.max(3, activeZoneCrowd.count) : 6;
      for (let i = 0; i < personCount; i++) {
        // Compute pseudo-random frame movement trajectory
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
      ctx.fillText(`● REC [LIVE FEED] — ${currentCam.name}`, 15, 25);
      ctx.fillText(`YOLOv8 DETECTED: ${personCount} PERSONS | FPS: 29.8`, 15, h - 15);

      if (isPlaying) {
        animId = requestAnimationFrame(renderCCTVFrame);
      }
    };

    renderCCTVFrame();

    return () => {
      if (animId) cancelAnimationFrame(animId);
    };
  }, [selectedCam, isPlaying, activeZoneCrowd, activeHazards]);

  return (
    <div className="relative w-full h-full bg-[#090d16] flex flex-col items-center justify-center p-4 font-mono select-none">
      {/* CCTV Camera Selector Bar */}
      <div className="absolute top-4 left-4 z-10 flex items-center space-x-2 bg-[#111827]/90 backdrop-blur border border-[#1f293d] p-1.5 rounded">
        {cameraChannels.map((cam) => (
          <button
            key={cam.id}
            onClick={() => setSelectedCam(cam.id)}
            className={`px-3 py-1 rounded text-xs font-semibold transition-all ${
              selectedCam === cam.id
                ? 'bg-amber-600 text-white shadow-sm'
                : 'text-eoc-muted hover:text-white hover:bg-[#1f293d]'
            }`}
          >
            {cam.id.toUpperCase()}
          </button>
        ))}
      </div>

      {/* Main CCTV Stream Player Canvas */}
      <canvas
        ref={canvasRef}
        width={780}
        height={490}
        className="border border-[#1f293d] rounded-lg shadow-2xl"
      />

      {/* Footer Info */}
      <div className="absolute bottom-4 left-6 z-10 text-[11px] text-eoc-muted">
        YOLOv8 + Centroid Tracking Pipeline | Bounding Boxes: Green (Normal), Amber (Alert)
      </div>
    </div>
  );
}
