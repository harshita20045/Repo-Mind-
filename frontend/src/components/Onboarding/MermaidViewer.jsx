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
    <div className="rounded-xl border border-white/10 bg-surface/90 p-5 backdrop-blur-md shadow-lg overflow-x-auto">
      <div
        ref={containerRef}
        className="mermaid-svg-container flex justify-center py-2 [&>svg]:max-w-full [&>svg]:h-auto"
        dangerouslySetInnerHTML={{ __html: svg }}
      />
    </div>
  );
}

