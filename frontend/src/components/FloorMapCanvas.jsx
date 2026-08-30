import React, { useRef, useEffect } from 'react';

export default function FloorMapCanvas({ state, onToggleEdgeBlock, onNodeClick }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;

    // Clear canvas
    ctx.fillStyle = '#090d16';
    ctx.fillRect(0, 0, width, height);

    // Draw Tactical Grid
    ctx.strokeStyle = '#111827';
    ctx.lineWidth = 1;
    const gridSize = 40;
    for (let x = 0; x < width; x += gridSize) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }
    for (let y = 0; y < height; y += gridSize) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }

    if (!state || !state.nodes) return;

    const nodesMap = {};
    state.nodes.forEach((n) => {
      nodesMap[n.id] = n;
    });

    const activeRoute = state.active_route;
    const pathEdges = activeRoute ? activeRoute.path_edges || [] : [];
    const altEdges = activeRoute && activeRoute.alternate_route ? activeRoute.alternate_route.path_edges || [] : [];

    // 1. Draw Edges / Corridors
    state.edges.forEach((edge) => {
      const source = nodesMap[edge.source];
      const target = nodesMap[edge.target];
      if (!source || !target) return;

      const isPath = pathEdges.includes(edge.id);
      const isAlt = altEdges.includes(edge.id);

      ctx.beginPath();
      ctx.moveTo(source.x, source.y);
      ctx.lineTo(target.x, target.y);

      if (edge.is_blocked) {
        ctx.strokeStyle = '#ef4444';
        ctx.lineWidth = 5;
        ctx.setLineDash([8, 6]);
      } else if (isPath) {
        ctx.strokeStyle = '#10b981';
        ctx.lineWidth = 6;
        ctx.setLineDash([]);
      } else if (isAlt) {
        ctx.strokeStyle = '#f59e0b';
        ctx.lineWidth = 4;
        ctx.setLineDash([6, 4]);
      } else {
        ctx.strokeStyle = '#1f293d';
        ctx.lineWidth = 4;
        ctx.setLineDash([]);
      }
      ctx.stroke();
      ctx.setLineDash([]);

      // Draw Blocked X if impassable
      if (edge.is_blocked) {
        const midX = (source.x + target.x) / 2;
        const midY = (source.y + target.y) / 2;
        ctx.fillStyle = '#ef4444';
        ctx.font = 'bold 13px Fira Code';
        ctx.fillText('✖ BLOCKED', midX - 30, midY + 4);
      }
    });

    // 2. Draw Crowd Density Heat Overlay per Zone
    if (state.crowd_zones) {
      Object.entries(state.crowd_zones).forEach(([zid, crowd]) => {
        const zoneNodes = state.nodes.filter((n) => n.zone_id === zid);
        if (zoneNodes.length === 0) return;

        zoneNodes.forEach((n) => {
          if (crowd.density > 0.5) {
            const radius = Math.min(45, crowd.density * 12);
            const grad = ctx.createRadialGradient(n.x, n.y, 2, n.x, n.y, radius);
            const alpha = Math.min(0.6, crowd.density * 0.15);

            if (crowd.density > 3.0) {
              grad.addColorStop(0, `rgba(239, 68, 68, ${alpha})`);
              grad.addColorStop(1, 'rgba(239, 68, 68, 0)');
            } else {
              grad.addColorStop(0, `rgba(245, 158, 11, ${alpha})`);
              grad.addColorStop(1, 'rgba(245, 158, 11, 0)');
            }

            ctx.fillStyle = grad;
            ctx.beginPath();
            ctx.arc(n.x, n.y, radius, 0, Math.PI * 2);
            ctx.fill();
          }
        });
      });
    }

    // 3. Draw Environmental Hazards (Fire / Smoke / Obstacle)
    if (state.hazards) {
      state.hazards.forEach((hazard) => {
        let hX = 375, hY = 250;
        if (hazard.node_id && nodesMap[hazard.node_id]) {
          hX = nodesMap[hazard.node_id].x;
          hY = nodesMap[hazard.node_id].y;
        } else if (hazard.zone_id) {
          const zn = state.nodes.find((n) => n.zone_id === hazard.zone_id);
          if (zn) {
            hX = zn.x;
            hY = zn.y;
          }
        }

        // Draw Glowing Fire Ring
        const isFire = hazard.type === 'fire';
        const isSmoke = hazard.type === 'smoke';

        const grad = ctx.createRadialGradient(hX, hY, 4, hX, hY, 35);
        grad.addColorStop(0, isFire ? 'rgba(239, 68, 68, 0.7)' : (isSmoke ? 'rgba(156, 163, 175, 0.6)' : 'rgba(245, 158, 11, 0.6)'));
        grad.addColorStop(1, 'rgba(0, 0, 0, 0)');

        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(hX, hY, 35, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = isFire ? '#f87171' : (isSmoke ? '#e5e7eb' : '#fbbf24');
        ctx.font = 'bold 15px Fira Code';
        const label = isFire ? '🔥 FIRE' : (isSmoke ? '💨 SMOKE' : '🧱 DEBRIS');
        ctx.fillText(label, hX - 22, hY - 26);
      });
    }

    // 4. Draw Nodes (Rooms & Exits)
    state.nodes.forEach((node) => {
      const isExit = node.is_exit;
      const isStart = node.id === 'node_start';
      const isRouteNode = activeRoute && activeRoute.path_nodes.includes(node.id);

      ctx.beginPath();
      ctx.arc(node.x, node.y, isExit ? 16 : (isStart ? 14 : 10), 0, Math.PI * 2);

      if (isExit) {
        const isTargetExit = activeRoute && activeRoute.target_exit === node.id;
        ctx.fillStyle = isTargetExit ? '#10b981' : '#4b5563';
        ctx.strokeStyle = isTargetExit ? '#34d399' : '#9ca3af';
        ctx.lineWidth = 3;
      } else if (isStart) {
        ctx.fillStyle = '#38bdf8';
        ctx.strokeStyle = '#7dd3fc';
        ctx.lineWidth = 3;
      } else if (isRouteNode) {
        ctx.fillStyle = '#10b981';
        ctx.strokeStyle = '#6ee7b7';
        ctx.lineWidth = 2;
      } else {
        ctx.fillStyle = '#1f293d';
        ctx.strokeStyle = '#374151';
        ctx.lineWidth = 2;
      }

      ctx.fill();
      ctx.stroke();

      // Node Labels
      ctx.fillStyle = isExit ? '#34d399' : (isStart ? '#38bdf8' : '#e5e7eb');
      ctx.font = isExit ? 'bold 12px Fira Code' : '11px Inter';
      ctx.fillText(node.name, node.x - 30, node.y + (isExit ? 32 : 22));
    });

  }, [state]);

  const handleCanvasClick = (e) => {
    if (!state || !state.nodes || !canvasRef.current) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;

    const nodesMap = {};
    state.nodes.forEach((n) => { nodesMap[n.id] = n; });

    // 1. Check if clicked near a node -> Open Hazard Modal targeting node
    for (const node of state.nodes) {
      const dist = Math.hypot(clickX - node.x, clickY - node.y);
      if (dist < 22) {
        if (onNodeClick) onNodeClick(node);
        return;
      }
    }

    // 2. Check if clicked near an edge corridor midpoint -> Toggle edge blockage
    for (const edge of state.edges) {
      const s = nodesMap[edge.source];
      const t = nodesMap[edge.target];
      if (s && t) {
        const midX = (s.x + t.x) / 2;
        const midY = (s.y + t.y) / 2;
        const dist = Math.hypot(clickX - midX, clickY - midY);
        if (dist < 28) {
          onToggleEdgeBlock(edge.id);
          return;
        }
      }
    }
  };

  return (
    <div className="relative w-full h-full bg-[#090d16] flex items-center justify-center overflow-hidden">
      {/* Tactical Canvas Overlay Header */}
      <div className="absolute top-4 left-4 z-10 bg-[#111827]/90 backdrop-blur border border-[#1f293d] px-3.5 py-2 rounded font-mono text-xs shadow-md">
        <div className="text-eoc-muted text-[10px]">EVACUATION FLOOR MAP</div>
        <div className="text-white font-bold tracking-wider">LEVEL 1 MAIN CONCOURSE</div>
        <div className="text-[10px] text-emerald-400 mt-0.5">● Dynamic A* Mesh Active</div>
      </div>

      <div className="absolute top-4 right-4 z-10 bg-[#111827]/90 backdrop-blur border border-[#1f293d] px-3 py-2 rounded font-mono text-[11px] space-y-1">
        <div className="flex items-center space-x-2">
          <span className="w-3 h-1 bg-emerald-500 rounded"></span>
          <span className="text-emerald-400 font-semibold">Recommended Safest Path</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-3 h-1 bg-amber-500 rounded border-dashed"></span>
          <span className="text-amber-400">Alternate Path</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-3 h-1 bg-rose-500 rounded"></span>
          <span className="text-rose-400">Corridor Blocked</span>
        </div>
      </div>

      {/* Main Floor Map Canvas */}
      <canvas
        ref={canvasRef}
        width={800}
        height={520}
        onClick={handleCanvasClick}
        className="border border-[#1f293d] rounded-lg shadow-2xl cursor-pointer hover:border-eoc-accent/50 transition-colors"
      />

      {/* Footer hint */}
      <div className="absolute bottom-3 left-4 z-10 text-[11px] font-mono text-eoc-muted">
        Tip: Click any node to inject fire/smoke; click corridor midpoint to toggle blockage.
      </div>
    </div>
  );
}
