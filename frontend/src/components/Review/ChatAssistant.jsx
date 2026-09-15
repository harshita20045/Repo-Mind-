import React, { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { chatApi } from '../../lib/api';
import ReactMarkdown from 'react-markdown';

export default function ChatAssistant({ organizationId, repositoryId, contextType, contextId }) {
  const queryClient = useQueryClient();
  const [inputMessage, setInputMessage] = useState('');
  const messagesEndRef = useRef(null);

  // 1. Get or create session
  const { data: sessions, isLoading: loadingSessions } = useQuery({
    queryKey: ['chatSessions', organizationId, contextType, contextId],
    queryFn: () => chatApi.getSessions(organizationId, contextType, contextId),
    enabled: !!organizationId && !!contextId
  });

  const { mutateAsync: createSession } = useMutation({
    mutationFn: () => chatApi.createSession({
      organization_id: organizationId,
      context_type: contextType,
      context_id: contextId
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chatSessions'] });
    }
  });

  // Automatically create a session if none exists
  useEffect(() => {
    if (sessions && sessions.length === 0 && organizationId && contextId) {
      createSession();
    }
  }, [sessions, organizationId, contextId, createSession]);

  const activeSession = sessions?.[0];

  // 2. Load message history
  const { data: messages = [], isLoading: loadingMessages } = useQuery({
    queryKey: ['chatMessages', activeSession?.id],
    queryFn: () => chatApi.getHistory(activeSession.id, organizationId),
    enabled: !!activeSession?.id && !!organizationId,
    refetchInterval: false
  });

  // 3. Send message mutation
  const { mutate: sendMessage, isPending: isSending } = useMutation({
    mutationFn: (messageText) => chatApi.sendMessage(activeSession.id, organizationId, {
      message: messageText,
      repository_id: repositoryId
    }),
    onMutate: async (newMessage) => {
      // Optimistic update
      await queryClient.cancelQueries({ queryKey: ['chatMessages', activeSession?.id] });
      const previousMessages = queryClient.getQueryData(['chatMessages', activeSession?.id]);
      
      const optimisticMessage = {
        id: `temp-${Date.now()}`,
        role: 'user',
        content: newMessage
      };
      
      queryClient.setQueryData(['chatMessages', activeSession?.id], old => [...(old || []), optimisticMessage]);
      return { previousMessages };
    },
    onError: (err, newMessage, context) => {
      queryClient.setQueryData(['chatMessages', activeSession?.id], context.previousMessages);
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['chatMessages', activeSession?.id] });
    }
  });

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isSending]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || isSending || !activeSession) return;
    
    sendMessage(inputMessage);
    setInputMessage('');
  };

  if (loadingSessions || (activeSession && loadingMessages)) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-400 py-12">
        <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mb-4"></div>
        Connecting to RepoMind AI...
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full h-[600px] bg-surface/30 rounded-xl overflow-hidden border border-white/5 shadow-inner">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-500 text-center space-y-4 opacity-70">
            <svg className="w-16 h-16 text-primary/40" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
            <div>
              <p className="font-medium text-gray-300">Ask about this Pull Request</p>
              <p className="text-sm">I have full context of the code changes, semantics, and risk.</p>
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[85%] rounded-2xl p-4 ${
                msg.role === 'user' 
                  ? 'bg-primary text-white shadow-lg shadow-primary/20 rounded-br-sm' 
                  : 'bg-surfaceHighlight/50 border border-white/5 text-gray-200 rounded-bl-sm'
              }`}>
                <div className="prose prose-invert prose-sm max-w-none">
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                </div>
                
                {msg.role === 'assistant' && msg.is_grounded && (
                  <div className="mt-3 pt-3 border-t border-white/10 flex items-center gap-2 text-xs text-success">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Grounded with RAG context
                  </div>
                )}
              </div>
            </div>
          ))
        )}
        
        {isSending && (
          <div className="flex justify-start">
            <div className="max-w-[85%] rounded-2xl p-4 bg-surfaceHighlight/30 border border-white/5 text-gray-400 rounded-bl-sm flex items-center gap-2">
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 bg-surfaceHighlight/20 border-t border-white/5">
        <form onSubmit={handleSubmit} className="relative flex items-center">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder={activeSession ? "Ask about architectural impact, bugs, or request a refactor..." : "Initializing session..."}
            disabled={!activeSession || isSending}
            className="w-full bg-surface/50 border border-white/10 text-gray-200 text-sm rounded-xl pl-4 pr-12 py-3.5 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-transparent transition-all placeholder-gray-500 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!inputMessage.trim() || isSending || !activeSession}
            className="absolute right-2 p-2 text-primary hover:text-primary-hover disabled:text-gray-600 transition-colors bg-white/5 hover:bg-white/10 rounded-lg disabled:bg-transparent"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </form>
      </div>
    </div>
  );
}
