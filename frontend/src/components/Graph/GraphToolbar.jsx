import React from 'react';

export default function GraphToolbar({
  onZoomIn,
  onZoomOut,
  onResetView,
  onFitToScreen,
  focusMode,
  onToggleFocusMode,
  showMinimap,
  onToggleMinimap,
  isFullscreen,
  onToggleFullscreen,
  hasSelection,
}) {
  return (
    <div className="absolute top-4 right-4 z-20 flex items-center gap-1.5 p-1 rounded-xl bg-surface/90 border border-white/10 backdrop-blur-md shadow-lg">
      <button
        onClick={onZoomIn}
        className="w-8 h-8 flex items-center justify-center rounded-lg text-text-muted hover:text-text-primary hover:bg-white/[0.08] transition-colors"
        title="Zoom In (+)"
        aria-label="Zoom in"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
        </svg>
      </button>

      <button
        onClick={onZoomOut}
        className="w-8 h-8 flex items-center justify-center rounded-lg text-text-muted hover:text-text-primary hover:bg-white/[0.08] transition-colors"
        title="Zoom Out (-)"
        aria-label="Zoom out"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M20 12H4" />
        </svg>
      </button>

      <button
        onClick={onFitToScreen}
        className="w-8 h-8 flex items-center justify-center rounded-lg text-text-muted hover:text-text-primary hover:bg-white/[0.08] transition-colors"
        title="Fit Graph to Screen"
        aria-label="Fit graph to screen"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M4 8V4m0 0h4M4 4l5 5m11-5h-4m4 0v4m0-4l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
        </svg>
      </button>

      <button
        onClick={onResetView}
        className="w-8 h-8 flex items-center justify-center rounded-lg text-text-muted hover:text-text-primary hover:bg-white/[0.08] transition-colors"
        title="Reset 1:1 View"
        aria-label="Reset view"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      </button>

      <div className="w-[1px] h-5 bg-white/10 mx-0.5" />

      {/* Focus Mode button */}
      <button
        onClick={onToggleFocusMode}
        disabled={!hasSelection}
        className={`w-8 h-8 flex items-center justify-center rounded-lg transition-colors ${
          focusMode
            ? 'bg-primary/20 text-primary border border-primary/40'
            : hasSelection
            ? 'text-text-muted hover:text-text-primary hover:bg-white/[0.08]'
            : 'text-text-muted/40 cursor-not-allowed'
        }`}
        title={focusMode ? 'Exit Focus Mode' : 'Focus on Selected Node & Neighborhood'}
        aria-label="Toggle focus mode"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <circle cx="12" cy="12" r="3" />
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 2v3m0 14v3M2 12h3m14 0h3" />
        </svg>
      </button>

      {/* Minimap toggle */}
      {onToggleMinimap && (
        <button
          onClick={onToggleMinimap}
          className={`w-8 h-8 flex items-center justify-center rounded-lg transition-colors ${
            showMinimap
              ? 'bg-primary/20 text-primary border border-primary/40'
              : 'text-text-muted hover:text-text-primary hover:bg-white/[0.08]'
          }`}
          title={showMinimap ? 'Hide Minimap' : 'Show Minimap'}
          aria-label="Toggle minimap"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <rect x="3" y="3" width="18" height="18" rx="2" />
            <rect x="12" y="12" width="6" height="6" rx="1" fill="currentColor" opacity={0.6} />
          </svg>
        </button>
      )}

      {/* Fullscreen toggle */}
      {onToggleFullscreen && (
        <button
          onClick={onToggleFullscreen}
          className="w-8 h-8 flex items-center justify-center rounded-lg text-text-muted hover:text-text-primary hover:bg-white/[0.08] transition-colors"
          title={isFullscreen ? 'Exit Fullscreen' : 'View Fullscreen'}
          aria-label="Toggle fullscreen"
        >
          {isFullscreen ? (
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          ) : (
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 8V4m0 0h4M4 4l5 5m11-5h-4m4 0v4m0-4l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
            </svg>
          )}
        </button>
      )}
    </div>
  );
}

