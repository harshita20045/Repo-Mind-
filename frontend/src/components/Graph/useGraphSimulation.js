import { useState, useEffect, useRef, useCallback, useMemo } from 'react';

export const NODE_COLORS = {
  module: { bg: '#0284c7', border: '#38bdf8', text: '#e0f2fe' },
  file: { bg: '#334155', border: '#94a3b8', text: '#f8fafc' },
  class: { bg: '#7e22ce', border: '#c084fc', text: '#f3e8ff' },
  function: { bg: '#0f766e', border: '#18d6c1', text: '#ccfbf1' },
  method: { bg: '#115e59', border: '#2dd4bf', text: '#ccfbf1' },
  api_endpoint: { bg: '#065f46', border: '#10b981', text: '#d1fae5' },
  db_model: { bg: '#3730a3', border: '#818cf8', text: '#e0e7ff' },
  service: { bg: '#b45309', border: '#f59e0b', text: '#fef3c7' },
  test: { bg: '#15803d', border: '#22c55e', text: '#dcfce7' },
  hotspot: { bg: '#9f1239', border: '#f43f5e', text: '#ffe4e6' },
  changed_origin: { bg: '#991b1b', border: '#ef4444', text: '#fee2e2' },
  hop_1: { bg: '#b45309', border: '#f59e0b', text: '#fef3c7' },
  hop_2: { bg: '#1d4ed8', border: '#3b82f6', text: '#dbeafe' },
  default: { bg: '#1f2937', border: '#64748b', text: '#f1f5f9' },
};

export function useGraphSimulation({
  rawNodes = [],
  rawEdges = [],
  width = 800,
  height = 600,
  filterType = 'all',
  searchQuery = '',
}) {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [transform, setTransform] = useState({ x: 0, y: 0, k: 1 });
  const [selectedNodeId, setSelectedNodeId] = useState(null);
  const [hoveredNodeId, setHoveredNodeId] = useState(null);
  const [selectedEdgeId, setSelectedEdgeId] = useState(null);
  const [focusMode, setFocusMode] = useState(false);
  const [isSimulating, setIsSimulating] = useState(false);

  const animFrameRef = useRef(null);
  const draggingNodeRef = useRef(null);
  const simEnergyRef = useRef(1.0);

  // Filter nodes based on active filterType and searchQuery
  const filteredData = useMemo(() => {
    let validNodes = rawNodes;

    if (filterType && filterType !== 'all') {
      validNodes = validNodes.filter((n) => n.node_type === filterType);
    }

    if (searchQuery && searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      validNodes = validNodes.filter(
        (n) =>
          n.name.toLowerCase().includes(q) ||
          (n.file_path && n.file_path.toLowerCase().includes(q)) ||
          (n.node_type && n.node_type.toLowerCase().includes(q))
      );
    }

    const validNodeIdSet = new Set(validNodes.map((n) => n.id));
    const validEdges = rawEdges.filter(
      (e) => validNodeIdSet.has(e.source_node_id || e.source) && validNodeIdSet.has(e.target_node_id || e.target)
    );

    return { nodes: validNodes, edges: validEdges };
  }, [rawNodes, rawEdges, filterType, searchQuery]);

  // Initialize nodes with positions
  useEffect(() => {
    if (!filteredData.nodes || filteredData.nodes.length === 0) {
      setNodes([]);
      setEdges([]);
      return;
    }

    const n = filteredData.nodes.length;
    const radius = Math.min(width, height) * 0.38;
    const angleStep = (2 * Math.PI) / Math.max(n, 1);

    const initializedNodes = filteredData.nodes.map((node, i) => {
      const angle = i * angleStep;
      const jitter = (Math.random() - 0.5) * 40;
      const x = width / 2 + (radius + jitter) * Math.cos(angle);
      const y = height / 2 + (radius + jitter) * Math.sin(angle);

      const degree = (node.in_degree || 0) + (node.out_degree || 0);
      const nodeRadius = Math.max(16, Math.min(36, 16 + degree * 2.5));

      return {
        ...node,
        x: isNaN(x) ? width / 2 : x,
        y: isNaN(y) ? height / 2 : y,
        vx: 0,
        vy: 0,
        radius: nodeRadius,
        style: NODE_COLORS[node.node_type] || NODE_COLORS.default,
      };
    });

    const initializedEdges = filteredData.edges.map((edge) => ({
      ...edge,
      source: edge.source_node_id !== undefined ? edge.source_node_id : edge.source,
      target: edge.target_node_id !== undefined ? edge.target_node_id : edge.target,
    }));

    setNodes(initializedNodes);
    setEdges(initializedEdges);
    simEnergyRef.current = 1.0;
    setIsSimulating(true);
  }, [filteredData, width, height]);

  // Run Force-Directed Physics Simulation with cooling
  useEffect(() => {
    if (!isSimulating || nodes.length === 0) return;

    let tick = 0;
    const maxTicks = 220;

    const runPhysicsStep = () => {
      simEnergyRef.current *= 0.94;

      if (simEnergyRef.current < 0.005 || tick >= maxTicks) {
        setIsSimulating(false);
        return;
      }

      setNodes((prevNodes) => {
        const nodeMap = new Map(prevNodes.map((n) => [n.id, n]));
        const kRepulsion = 1600;
        const springLength = 85;
        const springStiffness = 0.045;
        const centerGravity = 0.018;
        const cx = width / 2;
        const cy = height / 2;

        for (let i = 0; i < prevNodes.length; i++) {
          const a = prevNodes[i];
          for (let j = i + 1; j < prevNodes.length; j++) {
            const b = prevNodes[j];
            const dx = b.x - a.x;
            const dy = b.y - a.y;
            let dist = Math.sqrt(dx * dx + dy * dy);
            if (dist < 1) dist = 1;

            const force = (kRepulsion / (dist * dist)) * simEnergyRef.current;
            const fx = (dx / dist) * force;
            const fy = (dy / dist) * force;

            if (draggingNodeRef.current !== a.id) {
              a.vx -= fx;
              a.vy -= fy;
            }
            if (draggingNodeRef.current !== b.id) {
              b.vx += fx;
              b.vy += fy;
            }
          }
        }

        for (const edge of edges) {
          const source = nodeMap.get(edge.source);
          const target = nodeMap.get(edge.target);
          if (!source || !target) continue;

          const dx = target.x - source.x;
          const dy = target.y - source.y;
          let dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 1) dist = 1;

          const displacement = dist - springLength;
          const force = displacement * springStiffness * simEnergyRef.current;
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;

          if (draggingNodeRef.current !== source.id) {
            source.vx += fx;
            source.vy += fy;
          }
          if (draggingNodeRef.current !== target.id) {
            target.vx -= fx;
            target.vy -= fy;
          }
        }

        return prevNodes.map((n) => {
          if (draggingNodeRef.current === n.id) {
            return n;
          }

          const gx = (cx - n.x) * centerGravity * simEnergyRef.current;
          const gy = (cy - n.y) * centerGravity * simEnergyRef.current;
          const vx = (n.vx + gx) * 0.82;
          const vy = (n.vy + gy) * 0.82;

          return {
            ...n,
            x: Math.max(n.radius, Math.min(width - n.radius, n.x + vx)),
            y: Math.max(n.radius, Math.min(height - n.radius, n.y + vy)),
            vx,
            vy,
          };
        });
      });

      tick++;
      animFrameRef.current = requestAnimationFrame(runPhysicsStep);
    };

    animFrameRef.current = requestAnimationFrame(runPhysicsStep);

    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, [isSimulating, edges, width, height]);

  const activeFocusId = selectedNodeId || hoveredNodeId;

  const relationshipInfo = useMemo(() => {
    if (!activeFocusId) {
      return { incomingIds: new Set(), outgoingIds: new Set(), activeEdgeIds: new Set() };
    }

    const incomingIds = new Set();
    const outgoingIds = new Set();
    const activeEdgeIds = new Set();

    for (const e of edges) {
      if (e.target === activeFocusId) {
        incomingIds.add(e.source);
        activeEdgeIds.add(e.id);
      }
      if (e.source === activeFocusId) {
        outgoingIds.add(e.target);
        activeEdgeIds.add(e.id);
      }
    }

    return { incomingIds, outgoingIds, activeEdgeIds };
  }, [activeFocusId, edges]);

  const zoomIn = useCallback(() => {
    setTransform((t) => ({ ...t, k: Math.min(4.0, t.k * 1.25) }));
  }, []);

  const zoomOut = useCallback(() => {
    setTransform((t) => ({ ...t, k: Math.max(0.15, t.k * 0.8) }));
  }, []);

  const resetView = useCallback(() => {
    setTransform({ x: 0, y: 0, k: 1 });
  }, []);

  const fitToScreen = useCallback(() => {
    if (nodes.length === 0) return;

    let minX = Infinity;
    let maxX = -Infinity;
    let minY = Infinity;
    let maxY = -Infinity;

    for (const n of nodes) {
      if (n.x < minX) minX = n.x;
      if (n.x > maxX) maxX = n.x;
      if (n.y < minY) minY = n.y;
      if (n.y > maxY) maxY = n.y;
    }

    const graphWidth = maxX - minX + 80;
    const graphHeight = maxY - minY + 80;

    const scaleX = width / Math.max(graphWidth, 1);
    const scaleY = height / Math.max(graphHeight, 1);
    const k = Math.min(Math.max(Math.min(scaleX, scaleY), 0.25), 1.6);

    const centerX = (minX + maxX) / 2;
    const centerY = (minY + maxY) / 2;

    const x = width / 2 - centerX * k;
    const y = height / 2 - centerY * k;

    setTransform({ x, y, k });
  }, [nodes, width, height]);

  const startDragNode = useCallback((nodeId) => {
    draggingNodeRef.current = nodeId;
    simEnergyRef.current = 0.4;
    setIsSimulating(true);
  }, []);

  const updateDragNode = useCallback((nodeId, clientX, clientY) => {
    if (draggingNodeRef.current !== nodeId) return;

    setNodes((prevNodes) =>
      prevNodes.map((n) => {
        if (n.id === nodeId) {
          return { ...n, x: clientX, y: clientY, vx: 0, vy: 0 };
        }
        return n;
      })
    );
  }, []);

  const endDragNode = useCallback(() => {
    draggingNodeRef.current = null;
  }, []);

  const selectedNode = useMemo(
    () => nodes.find((n) => n.id === selectedNodeId) || null,
    [nodes, selectedNodeId]
  );

  const selectedEdge = useMemo(
    () => edges.find((e) => e.id === selectedEdgeId) || null,
    [edges, selectedEdgeId]
  );

  return {
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
    isSimulating,
    relationshipInfo,
    zoomIn,
    zoomOut,
    resetView,
    fitToScreen,
    startDragNode,
    updateDragNode,
    endDragNode,
  };
}

