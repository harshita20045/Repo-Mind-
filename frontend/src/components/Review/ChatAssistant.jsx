import React, { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { chatApi } from '../../lib/api';
import ReactMarkdown from 'react-markdown';
import { Spinner } from '../ui/LoadingSkeleton';

const SUPPORTED_QUESTIONS = [
  { label: 'Explain this module', query: 'Explain this module and its architectural structure.' },
  { label: 'How does authentication work?', query: 'How does authentication work in this repository?' },
  { label: 'Where is this API implemented?', query: 'Where is this API implemented and which routes handle it?' },
  { label: 'Which service accesses this database?', query: 'Which service accesses this database or database models?' },
  { label: 'Why was this PR flagged?', query: 'Why was this PR flagged in the code review?' },
  { label: 'Which modules depend on this function?', query: 'Which modules depend on this function or call it?' },
  { label: 'What happens when this endpoint is called?', query: 'What happens when this endpoint is called from request to database?' },
  { label: 'Which tests cover this functionality?', query: 'Which tests cover this functionality and where are coverage gaps?' },
];

const SOURCE_TYPE_STYLES = {
  code_symbol: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  documentation: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  architecture_rule: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  dependency_graph: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
  pr_diff: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  review_finding: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
  historical_decision: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
  test_scenario: 'bg-teal-500/10 text-teal-400 border-teal-500/20',
  source_code: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  test_code: 'bg-teal-500/10 text-teal-400 border-teal-500/20',
};

export default function ChatAssistant({ organizationId, repositoryId, contextType, contextId }) {
  const queryClient = useQueryClient();
  const [inputMessage, setInputMessage] = useState('');
  const [expandedSources, setExpandedSources] = useState({});
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const toggleSources = (msgId) => {
    setExpandedSources(prev => ({
      ...prev,
      [msgId]: !prev[msgId],
    }));
  };

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

  const handlePromptClick = (queryText) => {
    if (isSending || !activeSession) return;
    sendMessage(queryText);
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
    <div className="flex flex-col h-[580px]" role="region" aria-label="AI chat assistant">
      {/* Sessions selector */}
      {sessions && sessions.length > 1 && (
        <div className="mb-2">
          <select 
            aria-label="Active chat session"
            className="w-full bg-surfaceHighlight border border-border text-text-primary text-[11px] rounded-md px-2 py-1"
          >
            {sessions.map((s, idx) => (
              <option key={s.id} value={s.id}>
                Session #{s.id} {idx !== 0 ? '(STALE)' : '(Current)'}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Quick Prompt Chips */}
      <div className="mb-2 pb-2 border-b border-white/[0.06] flex items-center gap-1.5 overflow-x-auto no-scrollbar py-0.5">
        <span className="text-[11px] font-semibold text-text-muted uppercase tracking-wider whitespace-nowrap pl-0.5 mr-1">
          Supported:
        </span>
        {SUPPORTED_QUESTIONS.map(q => (
          <button
            key={q.label}
            type="button"
            onClick={() => handlePromptClick(q.query)}
            disabled={!activeSession || isSending}
            className="text-[11px] whitespace-nowrap px-2.5 py-1 rounded-full bg-surfaceHighlight/80 hover:bg-surface border border-white/[0.08] text-text-secondary hover:text-text-primary transition-all disabled:opacity-40 disabled:cursor-not-allowed flex-shrink-0"
          >
            {q.label}
          </button>
        ))}
      </div>

      {/* Messages area */}
      <div
        className="flex-1 overflow-y-auto px-1 py-2 space-y-4"
        aria-live="polite"
        aria-label="Conversation"
      >
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center gap-3 py-10">
            <div className="w-14 h-14 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary">
              <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <div>
              <p className="text-sm font-semibold text-text-primary">Ask about this repository</p>
              <p className="text-xs text-text-muted mt-1 max-w-sm">
                Query the indexed codebase — architecture rules, dependency graph, PR diffs, review findings, and test scenarios.
              </p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-2 w-full max-w-md">
              {SUPPORTED_QUESTIONS.slice(0, 4).map(suggestion => (
                <button
                  key={suggestion.label}
                  onClick={() => { setInputMessage(suggestion.query); inputRef.current?.focus(); }}
                  className="text-xs text-left px-3 py-2 bg-surfaceHighlight hover:bg-surface border border-border shadow-sm rounded-lg text-text-muted hover:text-text-secondary transition-all"
                >
                  {suggestion.label}
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
                className={`max-w-[84%] rounded-2xl px-4 py-3 ${
                  msg.role === 'user'
                    ? 'bg-primary text-white rounded-br-sm shadow-sm shadow-primary/20'
                    : 'bg-surface border border-border shadow-sm text-text-secondary rounded-bl-sm'
                }`}
              >
                {msg.role === 'user' ? (
                  <p className="text-sm leading-relaxed text-white">{msg.content}</p>
                ) : (
                  <div className="prose-chat text-sm leading-relaxed space-y-2">
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </div>
                )}

                {/* Grounding & Evidence Section */}
                {msg.role === 'assistant' && (
                  <div className="mt-3 pt-2.5 border-t border-white/[0.08] space-y-2">
                    <div className="flex items-center justify-between gap-2 flex-wrap text-xs">
                      {/* Grounded status */}
                      {msg.is_grounded ? (
                        <span className="flex items-center gap-1.5 text-success font-medium">
                          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          Grounded with repository evidence
                        </span>
                      ) : (
                        <span className="flex items-center gap-1.5 text-warning font-medium">
                          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                          </svg>
                          Insufficient repository evidence
                        </span>
                      )}

                      {/* Source Citations Toggle */}
                      {msg.sources && msg.sources.length > 0 && (
                        <button
                          type="button"
                          onClick={() => toggleSources(msg.id)}
                          className="text-[11px] text-text-muted hover:text-text-primary flex items-center gap-1 underline underline-offset-2"
                        >
                          <span>{expandedSources[msg.id] ? 'Hide' : 'Show'} Citations ({msg.sources.length})</span>
                          <svg
                            className={`w-3 h-3 transform transition-transform ${expandedSources[msg.id] ? 'rotate-180' : ''}`}
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                          >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                          </svg>
                        </button>
                      )}
                    </div>

                    {/* Expandable Citations Drawer */}
                    {msg.sources && msg.sources.length > 0 && expandedSources[msg.id] && (
                      <div className="mt-2 bg-surfaceHighlight/50 border border-white/[0.07] rounded-lg p-2.5 space-y-2 text-xs animate-slide-up">
                        <div className="text-[11px] font-semibold text-text-secondary uppercase tracking-wider">
                          Retrieved Repository Evidence:
                        </div>
                        <div className="grid grid-cols-1 gap-1.5 max-h-48 overflow-y-auto pr-1">
                          {msg.sources.map((src, sIdx) => {
                            const badgeStyle = SOURCE_TYPE_STYLES[src.type] || 'bg-white/10 text-text-secondary border-white/20';
                            return (
                              <div
                                key={sIdx}
                                className="flex flex-col gap-0.5 bg-surface/80 border border-white/[0.05] rounded p-2"
                              >
                                <div className="flex items-center gap-2 flex-wrap">
                                  <span className={`text-[10px] font-mono uppercase px-1.5 py-0.5 rounded border ${badgeStyle}`}>
                                    {src.type}
                                  </span>
                                  <span className="font-mono text-text-primary text-[11px] truncate max-w-[280px]">
                                    {src.path}
                                  </span>
                                  {src.symbol && (
                                    <span className="text-primary font-mono text-[11px]">
                                      #{src.symbol}
                                    </span>
                                  )}
                                </div>
                                {src.summary && (
                                  <p className="text-text-muted text-[11px] leading-tight mt-0.5">
                                    {src.summary}
                                  </p>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}
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
