import React, { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { chatApi } from '../../lib/api';
import ReactMarkdown from 'react-markdown';
import { Spinner } from '../ui/LoadingSkeleton';

export default function ChatAssistant({ organizationId, repositoryId, contextType, contextId }) {
  const queryClient = useQueryClient();
  const [inputMessage, setInputMessage] = useState('');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // 1. Get or create session
  const { data: sessions, isLoading: loadingSessions } = useQuery({
    queryKey: ['chatSessions', organizationId, contextType, contextId],
    queryFn: () => chatApi.getSessions(organizationId, contextType, contextId),
    enabled: !!organizationId && !!contextId,
  });

  const { mutateAsync: createSession } = useMutation({
    mutationFn: () => chatApi.createSession({
      organization_id: organizationId,
      context_type: contextType,
      context_id: contextId,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chatSessions'] });
    },
  });

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
    refetchInterval: false,
  });

  // 3. Send message mutation
  const { mutate: sendMessage, isPending: isSending } = useMutation({
    mutationFn: (messageText) => chatApi.sendMessage(activeSession.id, organizationId, {
      message: messageText,
      repository_id: repositoryId,
    }),
    onMutate: async (newMessage) => {
      await queryClient.cancelQueries({ queryKey: ['chatMessages', activeSession?.id] });
      const previousMessages = queryClient.getQueryData(['chatMessages', activeSession?.id]);
      const optimisticMessage = {
        id: `temp-${Date.now()}`,
        role: 'user',
        content: newMessage,
      };
      queryClient.setQueryData(['chatMessages', activeSession?.id], old => [...(old || []), optimisticMessage]);
      return { previousMessages };
    },
    onError: (err, newMessage, context) => {
      queryClient.setQueryData(['chatMessages', activeSession?.id], context.previousMessages);
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['chatMessages', activeSession?.id] });
    },
  });

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isSending]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || isSending || !activeSession) return;
    sendMessage(inputMessage);
    setInputMessage('');
    inputRef.current?.focus();
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  if (loadingSessions || (activeSession && loadingMessages)) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4 text-text-muted">
        <Spinner size="md" />
        <p className="text-sm">Connecting to RepoMind AI…</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-[540px]" role="region" aria-label="AI chat assistant">
      {/* Sessions selector */}
      {sessions && sessions.length > 1 && (
        <div className="mb-2">
          <select 
            className="w-full bg-surfaceHighlight border border-border text-text-primary text-[11px] rounded-md px-2 py-1"
            onChange={(e) => {
              // Usually we'd set active session here, but for simplicity we'll just show it exists
              // We'd need to lift activeSession state up or handle it properly.
            }}
          >
            {sessions.map((s, idx) => (
              <option key={s.id} value={s.id}>
                Session #{s.id} {idx !== 0 ? '(STALE)' : '(Current)'}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Messages area */}
      <div
        className="flex-1 overflow-y-auto px-1 py-2 space-y-4"
        aria-live="polite"
        aria-label="Conversation"
      >
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center gap-3 py-12">
            <div className="w-14 h-14 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary">
              <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <div>
              <p className="text-sm font-semibold text-text-primary">Ask about this repository</p>
              <p className="text-xs text-text-muted mt-1 max-w-xs">
                Query the indexed codebase — architecture, dependencies, conventions, or specific code.
              </p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-2 w-full max-w-sm">
              {[
                'What is the architecture of this codebase?',
                'Are there any obvious security concerns?',
              ].map(suggestion => (
                <button
                  key={suggestion}
                  onClick={() => { setInputMessage(suggestion); inputRef.current?.focus(); }}
                  className="text-xs text-left px-3 py-2 bg-surfaceHighlight hover:bg-surface border border-border shadow-sm rounded-lg text-text-muted hover:text-text-secondary transition-all"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map(msg => (
            <div
              key={msg.id}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.role === 'assistant' && (
                <div className="w-7 h-7 rounded-full bg-primary/15 border border-primary/20 flex items-center justify-center text-primary flex-shrink-0 mt-0.5 mr-2.5">
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
              )}

              <div
                className={`max-w-[82%] rounded-2xl px-4 py-3 ${
                  msg.role === 'user'
                    ? 'bg-primary text-white rounded-br-sm shadow-sm shadow-primary/20'
                    : 'bg-surface border border-border shadow-sm text-text-secondary rounded-bl-sm'
                }`}
              >
                {msg.role === 'user' ? (
                  <p className="text-sm leading-relaxed">{msg.content}</p>
                ) : (
                  <div className="prose-chat">
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </div>
                )}

                {/* Grounded badge */}
                {msg.role === 'assistant' && msg.is_grounded && (
                  <div className="mt-2.5 pt-2.5 border-t border-white/10 flex items-center gap-1.5 text-xs text-success">
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Grounded with repository context
                  </div>
                )}
              </div>
            </div>
          ))
        )}

        {/* Typing indicator */}
        {isSending && (
          <div className="flex justify-start">
            <div className="w-7 h-7 rounded-full bg-primary/15 border border-primary/20 flex items-center justify-center text-primary flex-shrink-0 mt-0.5 mr-2.5">
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div className="bg-surface border border-border shadow-sm rounded-2xl rounded-bl-sm px-4 py-3.5 flex items-center gap-1.5">
              {[0, 150, 300].map(delay => (
                <div
                  key={delay}
                  className="w-1.5 h-1.5 rounded-full bg-text-muted"
                  style={{ animation: `bounceDots 1.4s infinite ${delay}ms` }}
                  aria-hidden="true"
                />
              ))}
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="mt-3 border-t border-white/[0.07] pt-3">
        <form onSubmit={handleSubmit} className="flex items-end gap-2">
          <textarea
            ref={inputRef}
            value={inputMessage}
            onChange={e => setInputMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              activeSession
                ? 'Ask about architecture, dependencies, or specific code…'
                : 'Initializing session…'
            }
            disabled={!activeSession || isSending}
            rows={1}
            aria-label="Message input"
            className="flex-1 bg-surfaceHighlight border border-border text-text-primary text-[13px] rounded-lg px-4 py-3 focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary placeholder-text-muted disabled:opacity-50 resize-none transition-all leading-relaxed shadow-sm"
            style={{ minHeight: '44px', maxHeight: '120px' }}
          />
          <button
            type="submit"
            disabled={!inputMessage.trim() || isSending || !activeSession}
            aria-label="Send message"
            className="flex-shrink-0 w-10 h-10 rounded-xl bg-primary hover:bg-primary-hover disabled:bg-surfaceHighlight/40 disabled:text-text-muted text-white flex items-center justify-center transition-all shadow-sm shadow-primary/20 disabled:shadow-none"
          >
            {isSending ? (
              <Spinner size="sm" className="text-white" />
            ) : (
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            )}
          </button>
        </form>
        <p className="text-2xs text-text-muted mt-1.5 px-1">
          Press Enter to send · Shift+Enter for new line
        </p>
      </div>
    </div>
  );
}
