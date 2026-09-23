import re

file_path = 'frontend/src/pages/ReviewPage.jsx'
with open(file_path, 'r') as f:
    content = f.read()

activity_log_component = """
// ─── Activity Log (Phase 18) ──────────────────────────────────────────────────
function ActivityLog({ events }) {
  if (!events || events.length === 0) {
    return <div className="text-sm text-text-muted italic">No activity history found.</div>;
  }
  
  return (
    <div className="space-y-4">
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
                <span className="text-text-secondary">{evt.event_type.replace(/_/g, ' ')}</span>
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
"""

content = content.replace("// ─── Main Review Page", activity_log_component + "\n// ─── Main Review Page")

# Add the 'events' tab
content = content.replace(
    "    { id: 'chat', label: 'AI Assistant', count: null },",
    "    { id: 'chat', label: 'AI Assistant', count: null },\n    { id: 'events', label: 'Activity Log', count: null },"
)

# Fetch events using query
events_query = """
  const { data: prEvents } = useQuery({
    queryKey: ['pullRequestEvents', prid],
    queryFn: () => githubApi.getPullRequestEvents(prid),
    enabled: !!prid,
  });
"""
content = content.replace(
    "  const { data: repoData } = useQuery({",
    events_query + "\n  const { data: repoData } = useQuery({"
)

# Render the events tab
events_render = """
                {activeTab === 'events' && <ActivityLog events={prEvents} />}
"""
content = content.replace(
    "                {activeTab === 'conflicts' && <ConflictList conflicts={conflicts} />}",
    "                {activeTab === 'conflicts' && <ConflictList conflicts={conflicts} />}" + events_render
)

with open(file_path, 'w') as f:
    f.write(content)
