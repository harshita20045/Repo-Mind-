import React from 'react';
import ChatAssistant from '../components/Review/ChatAssistant';

export default function ChatPage({ user, memberships }) {
  const orgId = memberships?.[0]?.organization_id;

  if (!orgId) {
    return (
      <div className="flex flex-col items-center justify-center h-[600px] text-gray-400">
        <p>You must belong to an organization to use the Chatbot.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-slide-up h-full flex flex-col">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-2">RepoMind AI</h1>
          <p className="text-gray-400 text-sm">Ask questions across your entire organization's codebase and security posture.</p>
        </div>
      </div>

      <div className="flex-1 bg-surface/50 backdrop-blur-md border border-white/5 rounded-2xl p-6 min-h-[600px]">
        <ChatAssistant 
          organizationId={orgId}
          repositoryId={null}
          contextType="organization"
          contextId={orgId}
        />
      </div>
    </div>
  );
}
