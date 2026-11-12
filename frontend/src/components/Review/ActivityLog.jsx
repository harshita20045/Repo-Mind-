import React from 'react';

export default function ActivityLog({ events }) {
  if (!events || events.length === 0) {
    return <div className="text-sm text-text-muted italic py-4">No activity history found.</div>;
  }

  return (
    <div className="space-y-4 py-2">
      {events.map((evt, idx) => (
        <div key={evt.id || idx} className="flex gap-4 relative animate-fade-in">
          {/* Vertical line connecting events */}
          {idx !== events.length - 1 && (
            <div className="absolute left-[11px] top-6 bottom-[-16px] w-[2px] bg-white/[0.05]" />
          )}

          <div className="w-6 h-6 rounded-full bg-white/[0.05] border border-white/10 flex items-center justify-center flex-shrink-0 z-10">
            <div className="w-2 h-2 rounded-full bg-primary/80" />
          </div>

          <div className="flex-1 pb-4">
            <div className="flex items-baseline justify-between gap-4">
              <span className="text-sm text-text-primary">
                {evt.actor_login && <span className="font-bold mr-1">{evt.actor_login}</span>}
                <span className="text-text-secondary capitalize">{evt.event_type?.replace(/_/g, ' ')}</span>
              </span>
              {evt.timestamp && (
                <span className="text-xs text-text-muted font-mono shrink-0">
                  {new Date(evt.timestamp).toLocaleString()}
                </span>
              )}
            </div>
            {evt.commit_sha && (
              <div className="text-xs text-text-muted mt-1 font-mono">
                commit: {evt.commit_sha.substring(0, 7)}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

