import React from 'react';

export default function GraphMinimap({
  nodes = [],
  transform = { x: 0, y: 0, k: 1 },
  canvasWidth = 800,
  canvasHeight = 600,
  minimapWidth = 140,
  minimapHeight = 100,
}) {
  if (nodes.length === 0) return null;

  let minX = 0;
  let maxX = canvasWidth;
  let minY = 0;
  let maxY = canvasHeight;

  for (const n of nodes) {
    if (n.x < minX) minX = n.x;
    if (n.x > maxX) maxX = n.x;
    if (n.y < minY) minY = n.y;
    if (n.y > maxY) maxY = n.y;
  }

  const worldWidth = maxX - minX || 1;
  const worldHeight = maxY - minY || 1;

  const scaleX = minimapWidth / worldWidth;
  const scaleY = minimapHeight / worldHeight;
  const scale = Math.min(scaleX, scaleY) * 0.85;

  const viewWorldX = (-transform.x) / transform.k;
  const viewWorldY = (-transform.y) / transform.k;
  const viewWorldW = canvasWidth / transform.k;
  const viewWorldH = canvasHeight / transform.k;

  const camX = Math.max(0, (viewWorldX - minX) * scale);
  const camY = Math.max(0, (viewWorldY - minY) * scale);
  const camW = Math.min(minimapWidth, viewWorldW * scale);
  const camH = Math.min(minimapHeight, viewWorldH * scale);

  return (
    <div
      className="absolute bottom-4 right-4 z-20 rounded-lg bg-surface/90 border border-white/10 shadow-lg overflow-hidden backdrop-blur-md pointer-events-none"
      style={{ width: minimapWidth, height: minimapHeight }}
    >
      <svg width={minimapWidth} height={minimapHeight} className="w-full h-full">
        {nodes.map((n) => {
          const mx = (n.x - minX) * scale;
          const my = (n.y - minY) * scale;
          return (
            <circle
              key={n.id}
              cx={mx}
              cy={my}
              r={2}
              fill={n.style?.border || '#38bdf8'}
              opacity={0.7}
            />
          );
        })}

        <rect
          x={camX}
          y={camY}
          width={Math.max(8, camW)}
          height={Math.max(6, camH)}
          fill="rgba(24, 214, 193, 0.12)"
          stroke="#18d6c1"
          strokeWidth={1}
          rx={1}
        />
      </svg>
    </div>
  );
}

