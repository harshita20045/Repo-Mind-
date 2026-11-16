import React, { useRef, useEffect, useState, useCallback } from 'react';
import { useGraphSimulation, NODE_COLORS } from './useGraphSimulation';
import GraphToolbar from './GraphToolbar';
import GraphFilterBar from './GraphFilterBar';
import NodeDetailsDrawer from './NodeDetailsDrawer';
import EdgeDetailsModal from './EdgeDetailsModal';
import GraphMinimap from './GraphMinimap';
import EmptyState from '../ui/EmptyState';

export default function EngineeringGraphEngine({
  nodes: rawNodes = [],
  edges: rawEdges = [],
  repositoryId,
  graphMode = 'all',
  onGraphModeChange,
  availableModes = [],
  isLoading = false,
  onRefresh,
  height = '640px',
  className = '',
}) {
  const containerRef = useRef(null);
  const canvasRef = useRef(null);

  const [dimensions, setDimensions] = useState({ width: 900, height: 600 });
  const [nodeTypeFilter, setNodeTypeFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [showMinimap, setShowMinimap] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Measure container size safely across browsers and jsdom test environment
  useEffect(() => {
    if (!containerRef.current) return;
    const updateSize = () => {
      if (!containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      if (rect.width > 0 && rect.height > 0) {
        setDimensions({ width: rect.width, height: rect.height });
      }
    };
    updateSize();

    if (typeof ResizeObserver !== 'undefined') {
      const ro = new ResizeObserver(updateSize);
      ro.observe(containerRef.current);
      return () => ro.disconnect();
    }
  }, []);

  const {
    nodes,
    edges,
    transform,
    setTransform,
    selectedNodeId,
    setSelectedNodeId,
    hoveredNodeId,
    setHoveredNodeId,
    selectedEdgeId,
    setSelectedEdgeId,
    selectedNode,
    selectedEdge,
    focusMode,
    setFocusMode,
    relationshipInfo,
    zoomIn,
    zoomOut,
    resetView,
    fitToScreen,
    startDragNode,
    updateDragNode,
    endDragNode,
  } = useGraphSimulation({
    rawNodes,
    rawEdges,
    width: dimensions.width,
    height: dimensions.height,
    filterType: nodeTypeFilter,
    searchQuery,
  });

  const isDraggingCanvasRef = useRef(false);
  const isDraggingNodeRef = useRef(false);
  const dragStartPosRef = useRef({ x: 0, y: 0 });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || typeof canvas.getContext !== 'function') return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = dimensions.width * dpr;
    canvas.height = dimensions.height * dpr;
    ctx.scale(dpr, dpr);

    ctx.clearRect(0, 0, dimensions.width, dimensions.height);

    ctx.save();
    ctx.translate(transform.x, transform.y);
    ctx.scale(transform.k, transform.k);

    const activeNodeId = selectedNodeId || hoveredNodeId;
    const hasFocus = !!activeNodeId;
    const { incomingIds, outgoingIds } = relationshipInfo;

    const gridSpacing = 40;
    const startX = -transform.x / transform.k - 100;
    const startY = -transform.y / transform.k - 100;
    const endX = startX + dimensions.width / transform.k + 200;
    const endY = startY + dimensions.height / transform.k + 200;

    ctx.fillStyle = 'rgba(255, 255, 255, 0.03)';
    for (let gx = Math.floor(startX / gridSpacing) * gridSpacing; gx < endX; gx += gridSpacing) {
      for (let gy = Math.floor(startY / gridSpacing) * gridSpacing; gy < endY; gy += gridSpacing) {
        ctx.fillRect(gx, gy, 1.2, 1.2);
      }
    }

    const nodeMap = new Map(nodes.map((n) => [n.id, n]));

    // 1. Draw Edges
    for (const edge of edges) {
      const src = nodeMap.get(edge.source);
      const tgt = nodeMap.get(edge.target);
      if (!src || !tgt) continue;

      const isIncoming = activeNodeId && edge.target === activeNodeId;
      const isOutgoing = activeNodeId && edge.source === activeNodeId;

      let strokeColor = 'rgba(255, 255, 255, 0.12)';
      let lineWidth = 1.2;

      if (hasFocus) {
        if (isIncoming) {
          strokeColor = '#10b981';
          lineWidth = 2.4;
        } else if (isOutgoing) {
          strokeColor = '#0ea5e9';
          lineWidth = 2.4;
        } else {
          strokeColor = 'rgba(255, 255, 255, 0.04)';
        }
      }

      ctx.beginPath();
      ctx.strokeStyle = strokeColor;
      ctx.lineWidth = lineWidth;

      if (edge.is_inferred) {
        ctx.setLineDash([4, 4]);
      } else {
        ctx.setLineDash([]);
      }

      ctx.moveTo(src.x, src.y);
      ctx.lineTo(tgt.x, tgt.y);
      ctx.stroke();
      ctx.setLineDash([]);

      const dx = tgt.x - src.x;
      const dy = tgt.y - src.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist > tgt.radius + 10) {
        const arrowDist = dist - tgt.radius - 4;
        const arrowX = src.x + (dx / dist) * arrowDist;
        const arrowY = src.y + (dy / dist) * arrowDist;
        const angle = Math.atan2(dy, dx);

        ctx.save();
        ctx.translate(arrowX, arrowY);
        ctx.rotate(angle);
        ctx.fillStyle = strokeColor;
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(-7, -4);
        ctx.lineTo(-7, 4);
        ctx.closePath();
        ctx.fill();
        ctx.restore();
      }
    }

    // 2. Draw Nodes
    for (const node of nodes) {
      const isSelected = selectedNodeId === node.id;
      const isHovered = hoveredNodeId === node.id;
      const isIncoming = incomingIds.has(node.id);
      const isOutgoing = outgoingIds.has(node.id);
      const isFocused = !hasFocus || isSelected || isHovered || isIncoming || isOutgoing;

      if (focusMode && !isFocused) {
        continue;
      }

      const opacity = isFocused ? 1.0 : 0.22;
      const style = node.style || NODE_COLORS.default;

      if (isSelected || isHovered) {
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius + 8, 0, Math.PI * 2);
        ctx.fillStyle = isSelected ? 'rgba(24, 214, 193, 0.25)' : 'rgba(255, 255, 255, 0.15)';
        ctx.fill();
      }

      if (hasFocus && !isSelected && !isHovered) {
        if (isIncoming) {
          ctx.beginPath();
          ctx.arc(node.x, node.y, node.radius + 4, 0, Math.PI * 2);
          ctx.strokeStyle = '#10b981';
          ctx.lineWidth = 2;
          ctx.stroke();
        } else if (isOutgoing) {
          ctx.beginPath();
          ctx.arc(node.x, node.y, node.radius + 4, 0, Math.PI * 2);
          ctx.strokeStyle = '#0ea5e9';
          ctx.lineWidth = 2;
          ctx.stroke();
        }
      }

      ctx.beginPath();
      ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
      ctx.fillStyle = style.bg;
      ctx.globalAlpha = opacity;
      ctx.fill();

      ctx.lineWidth = isSelected ? 2.5 : 1.5;
      ctx.strokeStyle = isSelected ? '#ffffff' : style.border;
      ctx.stroke();
      ctx.globalAlpha = 1.0;

      ctx.font = `600 ${Math.max(10, node.radius * 0.55)}px Inter, sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillStyle = style.text;
      ctx.globalAlpha = opacity;
      const initial = node.node_type === 'api_endpoint' ? 'API' : node.name.charAt(0).toUpperCase();
      ctx.fillText(initial, node.x, node.y);
      ctx.globalAlpha = 1.0;

      const labelFontSize = Math.max(10, Math.min(13, 11 / transform.k));
      ctx.font = `500 ${labelFontSize}px Inter, sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';

      let labelColor = '#f1f5f9';
      if (isSelected) labelColor = '#18d6c1';
      else if (isIncoming) labelColor = '#34d399';
      else if (isOutgoing) labelColor = '#38bdf8';
      else if (!isFocused) labelColor = '#64748b';

      ctx.fillStyle = labelColor;
      ctx.globalAlpha = opacity;

      const maxLabelLen = 22;
      const labelText = node.name.length > maxLabelLen ? `${node.name.slice(0, 20)}…` : node.name;
      ctx.fillText(labelText, node.x, node.y + node.radius + 5);
      ctx.globalAlpha = 1.0;
    }

    ctx.restore();
  }, [nodes, edges, transform, selectedNodeId, hoveredNodeId, relationshipInfo, focusMode, dimensions]);

  const screenToWorld = useCallback(
    (clientX, clientY) => {
      const canvas = canvasRef.current;
      if (!canvas) return { x: 0, y: 0 };
      const rect = canvas.getBoundingClientRect();
      const screenX = clientX - rect.left;
      const screenY = clientY - rect.top;
      const worldX = (screenX - transform.x) / transform.k;
      const worldY = (screenY - transform.y) / transform.k;
      return { x: worldX, y: worldY };
    },
    [transform]
  );

  const findNodeAt = useCallback(
    (worldX, worldY) => {
      for (let i = nodes.length - 1; i >= 0; i--) {
        const n = nodes[i];
        const dx = n.x - worldX;
        const dy = n.y - worldY;
        if (dx * dx + dy * dy <= (n.radius + 4) * (n.radius + 4)) {
          return n;
        }
      }
      return null;
    },
    [nodes]
  );

  const findEdgeAt = useCallback(
    (worldX, worldY) => {
      const nodeMap = new Map(nodes.map((n) => [n.id, n]));
      for (const e of edges) {
        const src = nodeMap.get(e.source);
        const tgt = nodeMap.get(e.target);
        if (!src || !tgt) continue;

        const A = worldX - src.x;
        const B = worldY - src.y;
        const C = tgt.x - src.x;
        const D = tgt.y - src.y;
        const dot = A * C + B * D;
        const lenSq = C * C + D * D;
        let param = -1;
        if (lenSq !== 0) param = dot / lenSq;

        let xx, yy;
        if (param < 0) {
          xx = src.x;
          yy = src.y;
        } else if (param > 1) {
          xx = tgt.x;
          yy = tgt.y;
        } else {
          xx = src.x + param * C;
          yy = src.y + param * D;
        }

        const dx = worldX - xx;
        const dy = worldY - yy;
        if (dx * dx + dy * dy < 36) {
          return e;
        }
      }
      return null;
    },
    [nodes, edges]
  );

  const handleWheel = (e) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.15 : 0.88;
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    setTransform((t) => {
      const nextK = Math.max(0.15, Math.min(4.0, t.k * zoomFactor));
      const nextX = mouseX - (mouseX - t.x) * (nextK / t.k);
      const nextY = mouseY - (mouseY - t.y) * (nextK / t.k);
      return { x: nextX, y: nextY, k: nextK };
    });
  };

  const handleMouseDown = (e) => {
    if (e.button !== 0) return;
    const { x, y } = screenToWorld(e.clientX, e.clientY);
    const hitNode = findNodeAt(x, y);

    if (hitNode) {
      isDraggingNodeRef.current = true;
      startDragNode(hitNode.id);
    } else {
      isDraggingCanvasRef.current = true;
      dragStartPosRef.current = { x: e.clientX - transform.x, y: e.clientY - transform.y };
    }
  };

  const handleMouseMove = (e) => {
    const { x, y } = screenToWorld(e.clientX, e.clientY);

    if (isDraggingNodeRef.current && selectedNodeId) {
      updateDragNode(selectedNodeId, x, y);
      return;
    }

    if (isDraggingCanvasRef.current) {
      setTransform((t) => ({
        ...t,
        x: e.clientX - dragStartPosRef.current.x,
        y: e.clientY - dragStartPosRef.current.y,
      }));
      return;
    }

    const hitNode = findNodeAt(x, y);
    if (hitNode) {
      if (hoveredNodeId !== hitNode.id) setHoveredNodeId(hitNode.id);
      if (canvasRef.current) canvasRef.current.style.cursor = 'pointer';
    } else {
      if (hoveredNodeId !== null) setHoveredNodeId(null);
      if (canvasRef.current) canvasRef.current.style.cursor = 'grab';
    }
  };

  const handleMouseUp = () => {
    if (isDraggingNodeRef.current) {
      isDraggingNodeRef.current = false;
      endDragNode();
      return;
    }

    if (isDraggingCanvasRef.current) {
      isDraggingCanvasRef.current = false;
    }
  };

  const handleClick = (e) => {
    const { x, y } = screenToWorld(e.clientX, e.clientY);
    const hitNode = findNodeAt(x, y);

    if (hitNode) {
      setSelectedNodeId(hitNode.id);
      setSelectedEdgeId(null);
    } else {
      const hitEdge = findEdgeAt(x, y);
      if (hitEdge) {
        setSelectedEdgeId(hitEdge.id);
        setSelectedNodeId(null);
      } else {
        setSelectedNodeId(null);
        setSelectedEdgeId(null);
      }
    }
  };

  const handleDoubleClick = (e) => {
    const { x, y } = screenToWorld(e.clientX, e.clientY);
    const hitNode = findNodeAt(x, y);
    if (hitNode) {
      setTransform({
        x: dimensions.width / 2 - hitNode.x * 1.8,
        y: dimensions.height / 2 - hitNode.y * 1.8,
        k: 1.8,
      });
      setSelectedNodeId(hitNode.id);
    }
  };

  return (
    <div
      ref={containerRef}
      className={`relative rounded-xl border border-white/10 bg-background overflow-hidden flex flex-col select-none ${
        isFullscreen ? 'fixed inset-0 z-50 rounded-none' : ''
      } ${className}`}
      style={{ height: isFullscreen ? '100vh' : height }}
    >
      <GraphFilterBar
        graphMode={graphMode}
        onGraphModeChange={onGraphModeChange}
        availableModes={availableModes}
        nodeTypeFilter={nodeTypeFilter}
        onNodeTypeFilterChange={setNodeTypeFilter}
        searchQuery={searchQuery}
        onSearchQueryChange={setSearchQuery}
        totalNodes={rawNodes.length}
        totalEdges={rawEdges.length}
        visibleNodes={nodes.length}
        visibleEdges={edges.length}
      />

      <div className="relative flex-1 w-full h-full min-h-0 bg-[#07090e] overflow-hidden">
        {isLoading ? (
          <div className="absolute inset-0 z-20 flex flex-col items-center justify-center gap-3 bg-surface/60 backdrop-blur-sm">
            <div className="w-8 h-8 rounded-full border-2 border-primary border-t-transparent animate-spin" />
            <span className="text-xs text-text-muted font-medium">Indexing code graph perspectives…</span>
          </div>
        ) : rawNodes.length === 0 ? (
          <div className="absolute inset-0 z-10 flex items-center justify-center p-6">
            <EmptyState
              icon="repo"
              title="Knowledge Graph Empty"
              description="This repository has not been indexed yet. Re-index the repository to extract AST symbols and relationship edges."
              action={
                onRefresh && (
                  <button
                    onClick={onRefresh}
                    className="px-4 py-2 rounded-lg bg-primary text-background font-semibold text-xs shadow-md hover:bg-primary-hover transition-colors"
                  >
                    Index Repository Now
                  </button>
                )
              }
            />
          </div>
        ) : nodes.length === 0 ? (
          <div className="absolute inset-0 z-10 flex items-center justify-center p-6">
            <EmptyState
              icon="analytics"
              title="No Matching Entities"
              description={`No graph nodes matched the filter "${nodeTypeFilter}" or query "${searchQuery}".`}
              action={
                <button
                  onClick={() => {
                    setNodeTypeFilter('all');
                    setSearchQuery('');
                  }}
                  className="px-3.5 py-1.5 rounded-lg bg-surfaceHighlight border border-white/10 text-xs text-text-primary hover:bg-white/[0.08] transition-colors"
                >
                  Reset Filters
                </button>
              }
            />
          </div>
        ) : null}

        <canvas
          ref={canvasRef}
          onWheel={handleWheel}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onClick={handleClick}
          onDoubleClick={handleDoubleClick}
          className="w-full h-full block cursor-grab active:cursor-grabbing"
        />

        <GraphToolbar
          onZoomIn={zoomIn}
          onZoomOut={zoomOut}
          onResetView={resetView}
          onFitToScreen={fitToScreen}
          focusMode={focusMode}
          onToggleFocusMode={() => setFocusMode(!focusMode)}
          showMinimap={showMinimap}
          onToggleMinimap={() => setShowMinimap(!showMinimap)}
          isFullscreen={isFullscreen}
          onToggleFullscreen={() => setIsFullscreen(!isFullscreen)}
          hasSelection={!!selectedNodeId}
        />

        {showMinimap && (
          <GraphMinimap
            nodes={nodes}
            transform={transform}
            canvasWidth={dimensions.width}
            canvasHeight={dimensions.height}
          />
        )}

        {selectedNode && (
          <NodeDetailsDrawer
            node={selectedNode}
            allNodes={rawNodes}
            edges={rawEdges}
            repositoryId={repositoryId}
            onClose={() => setSelectedNodeId(null)}
            onSelectNode={(id) => setSelectedNodeId(id)}
          />
        )}

        {selectedEdge && (
          <EdgeDetailsModal
            edge={selectedEdge}
            allNodes={rawNodes}
            onClose={() => setSelectedEdgeId(null)}
          />
        )}
      </div>
    </div>
  );
}
