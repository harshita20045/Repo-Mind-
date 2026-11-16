import React, { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';

// Initialize mermaid once with strict security settings
mermaid.initialize({
  startOnLoad: false,
  securityLevel: 'strict',
  theme: 'dark',
  themeVariables: {
    darkMode: true,
    background: '#0d1117',
    primaryColor: '#3b82f6',
    primaryTextColor: '#f8fafc',
    primaryBorderColor: '#60a5fa',
    lineColor: '#94a3b8',
    secondaryColor: '#1e293b',
    tertiaryColor: '#0f172a',
  },
  fontFamily: 'Inter, system-ui, sans-serif',
});

export default function MermaidViewer({ chart }) {
  const containerRef = useRef(null);
  const [svg, setSvg] = useState('');
  const [error, setError] = useState(null);
  const [zoom, setZoom] = useState(1);
  const [copied, setCopied] = useState(false);

  const handleZoomIn = () => setZoom((prev) => Math.min(2.5, +(prev + 0.2).toFixed(2)));
  const handleZoomOut = () => setZoom((prev) => Math.max(0.4, +(prev - 0.2).toFixed(2)));
  const handleZoomReset = () => setZoom(1);

  const handleCopyRaw = () => {
    if (!chart) return;
    navigator.clipboard.writeText(chart);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  useEffect(() => {
    let isMounted = true;
    if (!chart || !chart.trim()) {
      setSvg('');
      setError(null);
      return;
    }

    const renderChart = async () => {
      try {
        setError(null);
        // Unique container ID per render
        const id = `mermaid-${Math.random().toString(36).substring(2, 9)}`;
        let cleanChart = chart.trim().replace(/^```mermaid\s*/i, '').replace(/```\s*$/, '').trim();
        
        // Sanitize unquoted node labels with parentheses or special characters:
        // e.g. Router[API Router (app/api/*.py)] -> Router["API Router (app/api/*.py)"]
        cleanChart = cleanChart.replace(/(\b[a-zA-Z0-9_\-]+\[)([^\]\r\n]+)(\])/g, (match, prefix, content, suffix) => {
          const trimmed = content.trim();
          if ((trimmed.startsWith('"') && trimmed.endsWith('"')) || (trimmed.startsWith("'") && trimmed.endsWith("'"))) {
            return match;
          }
          const safeContent = trimmed.replace(/"/g, "'");
          return `${prefix}"${safeContent}"${suffix}`;
        });
        
        const { svg: renderedSvg } = await mermaid.render(id, cleanChart);
        if (isMounted) {
          setSvg(renderedSvg);
        }
      } catch (err) {
        if (isMounted) {
          console.warn('Mermaid rendering failed, falling back to text representation:', err);
          setError(err.message || 'Syntax error in architecture diagram');
        }
      }
    };

    renderChart();

    return () => {
      isMounted = false;
    };
  }, [chart]);

  if (error) {
    return (
      <div className="rounded-xl border border-white/10 bg-surface/80 p-5 backdrop-blur-md">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2 text-warning text-xs font-semibold uppercase tracking-wider">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            Textual Architecture Representation
          </div>
          <span className="text-[11px] text-text-muted">Diagram fallback mode</span>
        </div>
        <pre className="p-4 rounded-lg bg-black/40 border border-white/5 font-mono text-xs text-text-secondary overflow-x-auto whitespace-pre leading-relaxed">
          {chart}
        </pre>
      </div>
    );
  }

  if (!svg) {
    return (
      <div className="h-48 flex items-center justify-center rounded-xl border border-white/5 bg-surfaceHighlight/20 animate-pulse">
        <span className="text-xs text-text-muted font-medium">Rendering architecture flow...</span>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-white/10 bg-surface/90 backdrop-blur-md shadow-lg overflow-hidden flex flex-col">
      {/* Visual Diagram Controls Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-border bg-surfaceHighlight/30 text-xs">
        <div className="flex items-center gap-1.5 text-text-muted">
          <svg className="w-3.5 h-3.5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16m-7 6h7" />
          </svg>
          <span className="font-medium text-[11px] uppercase tracking-wider">Architecture Flow Diagram</span>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={handleZoomIn}
            className="p-1 rounded hover:bg-surfaceHighlight text-text-muted hover:text-text-primary transition-colors"
            title="Zoom In"
            aria-label="Zoom In"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
          </button>
          <button
            onClick={handleZoomOut}
            className="p-1 rounded hover:bg-surfaceHighlight text-text-muted hover:text-text-primary transition-colors"
            title="Zoom Out"
            aria-label="Zoom Out"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
            </svg>
          </button>
          <button
            onClick={handleZoomReset}
            className="px-1.5 py-0.5 rounded text-[10px] font-mono hover:bg-surfaceHighlight text-text-muted hover:text-text-primary transition-colors"
            title="Reset Zoom"
          >
            {Math.round(zoom * 100)}%
          </button>
          <span className="w-px h-3 bg-border mx-1" />
          <button
            onClick={handleCopyRaw}
            className="px-2 py-0.5 rounded text-[11px] hover:bg-surfaceHighlight text-text-muted hover:text-text-primary transition-colors flex items-center gap-1"
            title="Copy Raw Mermaid Chart"
          >
            {copied ? (
              <span className="text-success font-medium">Copied!</span>
            ) : (
              <span>Copy Raw</span>
            )}
          </button>
        </div>
      </div>

      <div className="p-5 overflow-auto max-h-[560px]">
        <div
          ref={containerRef}
          style={{
            transform: `scale(${zoom})`,
            transformOrigin: 'top center',
            transition: 'transform 0.15s ease-out',
          }}
          className="mermaid-svg-container flex justify-center py-2 [&>svg]:max-w-full [&>svg]:h-auto"
          dangerouslySetInnerHTML={{ __html: svg }}
        />
      </div>
    </div>
  );
}

