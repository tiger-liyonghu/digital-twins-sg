'use client';

import { useRef, useEffect } from 'react';
import type { SophieMessage } from '@/lib/sophie-types';
import { useLocale } from '@/lib/locale-context';
import { useSophieChat } from '@/hooks/useSophieChat';
import { ScenarioCards } from './ScenarioCards';
import { IndustryCards } from './IndustryCards';
import { SurveyConfigCard } from './SurveyConfigCard';
import { ProgressBar } from './ProgressBar';
import { ResultsDisplay } from './ResultsDisplay';

export default function ChatInterface() {
  const { locale } = useLocale();
  const zh = locale === 'zh';

  const {
    messages,
    session,
    inputText,
    setInputText,
    isPolling,
    isSophieThinking,
    pollProgress,
    completedWidgets,
    inputActive,
    handleScenarioSelect,
    handleIndustrySelect,
    handleLaunch,
    handleScaleUp,
    handleRerun,
    handleSendMessage,
    handleFileUpload,
    handleQuickReply,
  } = useSophieChat(zh, locale);

  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, pollProgress, isSophieThinking]);

  // ─── Widget renderer ──
  const renderWidget = (msg: SophieMessage) => {
    if (!msg.widget) return null;
    const done = completedWidgets.has(msg.id);

    switch (msg.widget.type) {
      case 'scenario_cards':
        return <ScenarioCards onSelect={(s) => handleScenarioSelect(s, msg.id)} disabled={done} />;
      case 'industry_cards':
        return <IndustryCards onSelect={(i) => handleIndustrySelect(i, msg.id)} disabled={done} />;
      case 'confirm_summary':
        return session.question ? (
          <SurveyConfigCard
            question={session.question}
            options={session.options}
            audience={session.audience}
            onLaunch={handleLaunch}
            disabled={done}
          />
        ) : null;
      case 'progress':
        return (
          <ProgressBar
            progress={pollProgress.progress}
            total={pollProgress.total}
            isTest={msg.widget.isTest}
            interim={pollProgress.interim}
          />
        );
      case 'results': {
        const result = session.fullResult || session.testResult;
        if (!result) return null;
        const isTest = session.phase === 'test_analysis';
        return (
          <ResultsDisplay
            result={result}
            isTest={isTest}
            onScaleUpN={isTest ? handleScaleUp : undefined}
            onRerun={isTest ? handleRerun : undefined}
          />
        );
      }
      default:
        return null;
    }
  };

  const showUpload = session.phase === 'pain_point' || session.phase === 'objective';

  return (
    <div className="h-full w-full bg-[#050810] flex flex-col">
      {/* Sub-header */}
      <div className="flex items-center justify-between px-6 py-2 border-b border-[#1e293b] bg-[#0a0e1a]/80">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white text-xs font-bold">
            S
          </div>
          <p className="text-xs text-[#94a3b8]">
            Sophie · {zh ? '你的调研助手' : 'Your Research Assistant'}
            {isPolling && <span className="text-green-400 ml-2">&#9679; live</span>}
          </p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-2xl mx-auto space-y-4">
          {messages.map((msg) => (
            <div key={msg.id} className={`flex ${msg.role === 'client' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] ${
                msg.role === 'client'
                  ? 'bg-blue-500/15 border border-blue-500/25 text-blue-100'
                  : 'bg-[#111827] border border-[#1e293b] text-[#e2e8f0]'
              } rounded-2xl px-5 py-4`}>
                {msg.role === 'sophie' && (
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-5 h-5 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white text-[9px] font-bold">S</div>
                    <span className="text-xs text-[#94a3b8] font-semibold">Sophie</span>
                  </div>
                )}
                <div className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</div>

                {/* Quick replies */}
                {msg.quickReplies && msg.quickReplies.length > 0 && !completedWidgets.has(`qr-${msg.id}`) && (
                  <div className="flex flex-wrap gap-2 mt-3">
                    {msg.quickReplies.map((qr, i) => {
                      const isOther = qr === '其他' || qr.toLowerCase() === 'other';
                      return (
                        <button
                          key={i}
                          onClick={() => {
                            const focusInput = handleQuickReply(qr, msg.id);
                            if (focusInput) inputRef.current?.focus();
                          }}
                          disabled={isSophieThinking}
                          className={`px-3 py-1.5 text-xs rounded-full border transition-all disabled:opacity-30 cursor-pointer ${
                            isOther
                              ? 'border-[#334155] text-[#94a3b8] bg-transparent hover:border-[#475569] hover:text-[#cbd5e1]'
                              : 'border-blue-500/30 text-blue-300 bg-blue-500/10 hover:bg-blue-500/20 hover:border-blue-500/50'
                          }`}
                        >
                          {qr}
                        </button>
                      );
                    })}
                  </div>
                )}

                {renderWidget(msg)}
              </div>
            </div>
          ))}

          {/* Thinking indicator */}
          {isSophieThinking && (
            <div className="flex justify-start">
              <div className="bg-[#111827] border border-[#1e293b] rounded-2xl px-5 py-4">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-5 h-5 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white text-[9px] font-bold">S</div>
                  <span className="text-xs text-[#94a3b8] font-semibold">Sophie</span>
                </div>
                <div className="flex items-center gap-1.5 text-sm text-[#64748b]">
                  <span className="animate-pulse">●</span>
                  <span className="animate-pulse" style={{ animationDelay: '0.2s' }}>●</span>
                  <span className="animate-pulse" style={{ animationDelay: '0.4s' }}>●</span>
                </div>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </div>

      {/* Input */}
      {inputActive && (
        <div className="px-4 py-4 border-t border-[#1e293b] bg-[#0a0e1a]/80 backdrop-blur">
          <div className="flex gap-3 max-w-2xl mx-auto items-center">
            {showUpload && (
              <>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".txt,.csv,.md,.json"
                  onChange={handleFileUpload}
                  className="hidden"
                />
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isSophieThinking}
                  title={zh ? '上传问卷' : 'Upload questionnaire'}
                  className="flex-shrink-0 w-10 h-10 flex items-center justify-center rounded-xl border border-[#1e293b] bg-[#111827] text-[#94a3b8] hover:border-blue-500/40 hover:text-blue-400 transition-all disabled:opacity-30"
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <polyline points="17 8 12 3 7 8" />
                    <line x1="12" y1="3" x2="12" y2="15" />
                  </svg>
                </button>
              </>
            )}
            <input
              ref={inputRef}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSendMessage()}
              disabled={isSophieThinking}
              placeholder={
                showUpload
                  ? (zh ? '告诉 Sophie 你想调研什么，或上传问卷...' : 'Tell Sophie what you want to research, or upload a questionnaire...')
                  : (zh ? '问我关于结果的任何问题...' : 'Ask me anything about the results...')
              }
              className="flex-1 bg-[#111827] border border-[#1e293b] rounded-xl px-4 py-3 text-sm text-[#e2e8f0] outline-none focus:border-blue-500/50 placeholder:text-[#475569] disabled:opacity-50"
            />
            <button
              onClick={handleSendMessage}
              disabled={!inputText.trim() || isSophieThinking}
              className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white text-sm rounded-xl font-semibold disabled:opacity-30 hover:shadow-lg hover:shadow-blue-500/25 transition-all"
            >
              {zh ? '发送' : 'Send'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
