import React, { useState, useRef, useEffect } from 'react';
import { sendChatMessage, getReportPdfUrl } from '../../services/api';

const DEFAULT_MESSAGES = [
  {
    sender: 'bot',
    text: 'Hello! I am your AquaVision AI Water Science Copilot, integrated with your live telemetry feeds, pre-trained ML models (CatBoost WQI regressor, Gradient Boosting classifier, ARIMA forecaster), and WHO / Pakistan NSDWQ standards.\n\nYou can switch between **Overall Context** to query the entire distribution fleet or select an **Individual Tanker** for targeted diagnostics, health risk assessments, WQI predictions, and automated laboratory audit reports.',
  },
];

export default function AIAssistantView({
  tankers = [],
  selectedTanker,
  setSelectedTanker,
  setSelectedReport,
  onNewReportGenerated,
  profile,
}) {
  const [messages, setMessages] = useState(DEFAULT_MESSAGES);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [contextMode, setContextMode] = useState('overall'); // 'overall' or 'tanker'
  const [activeTankerId, setActiveTankerId] = useState(selectedTanker?.id || (tankers[0]?.id || ''));
  const messagesEndRef = useRef(null);

  // Keep activeTankerId in sync if selectedTanker changes externally
  useEffect(() => {
    if (selectedTanker?.id && contextMode === 'tanker') {
      setActiveTankerId(selectedTanker.id);
    }
  }, [selectedTanker]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const currentTanker = tankers.find((t) => t.id === activeTankerId) || selectedTanker || tankers[0];

  const handleContextChange = (e) => {
    const val = e.target.value;
    if (val === 'overall') {
      setContextMode('overall');
    } else {
      setContextMode('tanker');
      setActiveTankerId(val);
      const found = tankers.find((t) => t.id === val);
      if (found && setSelectedTanker) {
        setSelectedTanker(found);
      }
    }
  };

  const handleSend = async (textToSend) => {
    const query = (textToSend || input).trim();
    if (!query || loading) return;

    setInput('');

    // Add user message to UI
    const userMsg = { sender: 'user', text: query };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const targetTankerId = contextMode === 'tanker' ? (activeTankerId || currentTanker?.id) : null;
      const result = await sendChatMessage(
        query,
        'aquavision-session',
        targetTankerId,
        contextMode
      );

      const botMsg = {
        sender: 'bot',
        text: result.response,
        isReport: result.is_report,
        report: result.report,
        warning: result.warning,
      };

      setMessages((prev) => [...prev, botMsg]);

      // If a report was dynamically generated via the chatbot
      if (result.is_report && result.report && onNewReportGenerated) {
        onNewReportGenerated(result.report);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          sender: 'bot',
          text: `Error processing request: ${err.message}. Please verify the AquaVision backend is running.`,
          isError: true,
          retryText: query,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleClearChat = () => {
    setMessages(DEFAULT_MESSAGES);
  };

  const handleFormSubmit = (e) => {
    e.preventDefault();
    handleSend();
  };

  const getInitials = (name) => {
    if (!name) return 'AV';
    const parts = name.trim().split(/\s+/);
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  };

  // Dynamic quick prompts based on context
  const quickPrompts = contextMode === 'overall'
    ? [
        'How many tankers are currently registered?',
        'Compare the water quality of all registered tankers',
        'Which tanker currently has the best water quality readings?',
        'What are the health risks of high nitrate levels for children?',
        'What is the difference between TDS and turbidity?',
        'Why is pH important in drinking water?',
        'Predict WQI for pH 7.2 and TDS 450',
        'Explain how the Water Quality Index (WQI) works',
        'Hi, what can you help me with?',
      ]
    : [
        `Give me a complete overview of this tanker's water quality`,
        'Which parameters are outside their recommended ranges?',
        'Explain the latest readings in simple language',
        "What actions would you recommend to improve this tanker's water quality?",
        `Generate an official water quality report for ${currentTanker?.id || 'this tanker'}`,
        'What can cause high turbidity in drinking water?',
      ];

  // Helper to render text with bold formatting and clean paragraphs
  const renderFormattedText = (text) => {
    if (!text) return null;
    return text.split('\n').map((line, idx) => {
      // Parse markdown bold **text**
      const parts = line.split(/(\*\*.*?\*\*)/g);
      return (
        <span key={idx} className="block min-h-[1.25rem]">
          {parts.map((part, pIdx) => {
            if (part.startsWith('**') && part.endsWith('**')) {
              return <strong key={pIdx} className="font-bold text-brand-dark">{part.slice(2, -2)}</strong>;
            }
            if (part.startsWith('*') && part.endsWith('*')) {
              return <em key={pIdx} className="italic text-brand-charcoal">{part.slice(1, -1)}</em>;
            }
            return part;
          })}
        </span>
      );
    });
  };

  return (
    <section className="h-full flex flex-col min-h-0 gap-2 animate-in fade-in duration-200">
      {/* Sleek Compact Header Bar */}
      <div className="flex items-center justify-between gap-2 px-3 py-1.5 bg-brand-surface rounded-xl border border-brand-silver/60 shadow-2xs flex-shrink-0">
        {/* Left Side: Copilot Title & Context Selector */}
        <div className="flex items-center gap-2 sm:gap-3 flex-wrap min-w-0">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-brand-primary animate-pulse"></span>
            <span className="font-tech-code font-extrabold text-xs text-brand-dark tracking-wide uppercase">
              AI Copilot
            </span>
          </div>

          <div className="h-4 w-px bg-brand-silver/60 hidden sm:block"></div>

          {/* Context Selector */}
          <div className="flex items-center gap-1.5">
            <span className="text-[11px] font-bold text-brand-charcoal uppercase hidden md:inline">Scope:</span>
            <select
              value={contextMode === 'overall' ? 'overall' : activeTankerId}
              onChange={handleContextChange}
              className="bg-brand-surfaceAlt text-brand-dark text-xs font-semibold px-2 py-1 rounded-lg border border-brand-silver/70 focus:outline-none focus:ring-1 focus:ring-brand-primary cursor-pointer max-w-[210px] truncate"
            >
              <option value="overall">🌐 Overall Fleet ({tankers.length} Tankers)</option>
              <optgroup label="Individual Tankers">
                {tankers.map((t) => (
                  <option key={t.id} value={t.id}>
                    🚚 {t.id}: {t.name} ({t.city})
                  </option>
                ))}
              </optgroup>
            </select>
          </div>

          {/* Active Scope Pill */}
          <div className="hidden lg:flex items-center gap-1.5 px-2 py-0.5 rounded-lg bg-brand-surfaceAlt/80 border border-brand-silver/40 text-[11px] text-brand-charcoal truncate max-w-xs">
            {contextMode === 'overall' ? (
              <span className="text-brand-primary font-semibold">Fleet Grounding ({tankers.length} Units)</span>
            ) : (
              <span className="truncate">
                <strong className="text-brand-dark">{currentTanker?.name || currentTanker?.id}</strong> ({currentTanker?.city})
                {currentTanker?.wqi_score && (
                  <span className="ml-1.5 px-1.5 py-0.2 rounded bg-brand-secondary/40 text-brand-dark font-mono-data text-[10px] font-bold">
                    WQI {currentTanker.wqi_score}
                  </span>
                )}
              </span>
            )}
          </div>
        </div>

        {/* Right Side: Gemini Status & Clear Chat */}
        <div className="flex items-center gap-2 flex-shrink-0">
          <div className="hidden sm:flex items-center gap-1.5 text-[10px] font-tech-code text-brand-charcoal bg-brand-surfaceAlt px-2 py-1 rounded-lg border border-brand-silver/50">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
            <span>GEMINI 3.1</span>
          </div>

          <button
            onClick={handleClearChat}
            className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-brand-surfaceAlt hover:bg-brand-secondary/30 text-brand-charcoal hover:text-brand-dark border border-brand-silver/70 flex items-center gap-1 transition-all shadow-2xs cursor-pointer"
            title="Reset conversation session"
          >
            <span className="material-symbols-outlined text-[15px]">restart_alt</span>
            <span>Clear</span>
          </button>
        </div>
      </div>

      {/* Main Chat Container — Maximum Available Height */}
      <div className="bg-brand-surface rounded-xl border border-brand-silver/70 shadow-2xs flex-1 flex flex-col min-h-0 overflow-hidden">
        {/* Messages Scroll Area */}
        <div className="flex-1 p-3 sm:p-5 overflow-y-auto space-y-3.5 text-xs leading-relaxed">
          {messages.map((msg, idx) => {
            const isUser = msg.sender === 'user';
            return (
              <div
                key={idx}
                className={`flex items-start gap-2.5 max-w-3xl ${
                  isUser ? 'ml-auto justify-end' : ''
                }`}
              >
                {!isUser && (
                  <div className="w-7 h-7 rounded-lg bg-brand-primary text-white flex items-center justify-center flex-shrink-0 shadow-2xs mt-0.5">
                    <span className="material-symbols-outlined text-[16px]">smart_toy</span>
                  </div>
                )}

                <div className="space-y-1.5 max-w-2xl">
                  <div
                    className={`p-3.5 rounded-2xl ${
                      isUser
                        ? 'bg-brand-primary text-white shadow-2xs'
                        : msg.isError
                        ? 'bg-rose-50 border border-rose-200 text-rose-800'
                        : 'bg-brand-surfaceAlt border border-brand-silver/50 text-brand-dark'
                    }`}
                  >
                    {!isUser && (
                      <div className="font-bold text-brand-primary mb-1.5 flex items-center justify-between gap-2 border-b border-brand-silver/30 pb-1">
                        <div className="flex items-center gap-1.5">
                          <span className="font-tech-code text-[11px] uppercase font-bold">AquaVision AI Copilot</span>
                          {msg.warning && (
                            <span className="text-[10px] text-amber-700 bg-brand-warning px-1.5 py-0.2 rounded font-normal font-tech-code">
                              Failover active
                            </span>
                          )}
                        </div>
                        <span className="text-[10px] text-brand-charcoal font-tech-code">NSDWQ Grounded</span>
                      </div>
                    )}

                    <div className="leading-relaxed space-y-1">
                      {isUser ? msg.text : renderFormattedText(msg.text)}
                    </div>

                    {msg.retryText && (
                      <button
                        onClick={() => handleSend(msg.retryText)}
                        className="mt-2 text-xs font-bold text-rose-700 underline flex items-center gap-1 cursor-pointer"
                      >
                        <span className="material-symbols-outlined text-[14px]">refresh</span>
                        Retry Request
                      </button>
                    )}

                    {/* Embedded Report Card if generated in this message */}
                    {msg.isReport && msg.report && (
                      <div className="mt-2.5 p-3 rounded-xl bg-brand-surface border border-brand-primary/40 shadow-2xs space-y-2 text-xs">
                        <div className="flex items-center justify-between">
                          <span className="font-tech-code text-brand-primary font-bold">
                            REPORT #{msg.report.id}
                          </span>
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">
                            {msg.report.status || 'Verified Safe'}
                          </span>
                        </div>
                        <div className="font-bold text-brand-dark text-sm">{msg.report.title}</div>
                        <div className="flex items-center gap-4 text-brand-charcoal text-[11px] font-mono-data">
                          <span>WQI: <strong>{msg.report.wqi_score}</strong></span>
                          <span>Quality Tier: <strong>{msg.report.quality_class}</strong></span>
                        </div>
                        <div className="flex items-center gap-2 pt-2 border-t border-brand-silver/30">
                          <button
                            onClick={() => setSelectedReport(msg.report)}
                            className="px-2.5 py-1.5 rounded-lg bg-brand-secondary/40 hover:bg-brand-secondary text-brand-dark font-bold text-xs transition-all flex items-center gap-1 cursor-pointer"
                          >
                            <span className="material-symbols-outlined text-[15px]">visibility</span>
                            Preview in AquaVision
                          </button>
                          <a
                            href={getReportPdfUrl(msg.report.id)}
                            download
                            className="px-2.5 py-1.5 rounded-lg bg-brand-primary hover:bg-brand-primary-dark text-white font-bold text-xs transition-all flex items-center gap-1 shadow-2xs"
                          >
                            <span className="material-symbols-outlined text-[15px]">download</span>
                            Download PDF
                          </a>
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {isUser && (
                  <div className="w-7 h-7 rounded-lg bg-brand-secondary text-brand-dark font-bold text-xs flex items-center justify-center flex-shrink-0 shadow-2xs mt-0.5">
                    {getInitials(profile?.name)}
                  </div>
                )}
              </div>
            );
          })}

          {/* Loading Indicator */}
          {loading && (
            <div className="flex items-start gap-2.5 max-w-2xl">
              <div className="w-7 h-7 rounded-lg bg-brand-primary text-white flex items-center justify-center flex-shrink-0 shadow-2xs mt-0.5">
                <span className="material-symbols-outlined text-[16px]">smart_toy</span>
              </div>
              <div className="bg-brand-surfaceAlt border border-brand-silver/50 p-3 rounded-2xl text-xs text-brand-charcoal flex items-center gap-2">
                <span className="inline-block w-3.5 h-3.5 border-2 border-brand-primary border-t-transparent rounded-full animate-spin"></span>
                <span>Reasoning with CatBoost WQI regressor, RAG standards &amp; fleet telemetry...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Compact Single-Row Horizontal Quick Prompts Bar */}
        <div className="px-3 py-1.5 border-t border-brand-silver/30 flex items-center gap-1.5 bg-brand-surfaceAlt/60 flex-shrink-0 overflow-x-auto no-scrollbar">
          <span className="text-[10px] font-bold text-brand-charcoal font-tech-code uppercase whitespace-nowrap flex-shrink-0">
            SUGGESTED:
          </span>
          <div className="flex items-center gap-1.5 flex-nowrap">
            {quickPrompts.map((p, i) => (
              <button
                key={i}
                onClick={() => handleSend(p)}
                disabled={loading}
                className="whitespace-nowrap px-2.5 py-1 rounded-full text-[11px] bg-brand-surface hover:bg-brand-secondary/40 text-brand-dark border border-brand-silver/60 transition-colors shadow-2xs cursor-pointer flex-shrink-0"
              >
                {p}
              </button>
            ))}
          </div>
        </div>

        {/* Compact Chat Input Bar */}
        <form
          onSubmit={handleFormSubmit}
          className="p-2.5 sm:p-3 border-t border-brand-silver/50 bg-brand-surface flex items-center gap-2 flex-shrink-0"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
            placeholder={
              contextMode === 'overall'
                ? "Ask about entire fleet, standards, or WQI prediction (e.g. 'How many tankers are registered?')..."
                : `Ask about ${currentTanker?.name || currentTanker?.id || 'this tanker'} (e.g. 'Analyze its water quality' or 'Generate report')...`
            }
            className="flex-1 px-3 py-2 text-xs rounded-xl border border-brand-silver bg-brand-surfaceAlt/30 text-brand-dark focus:outline-none focus:ring-2 focus:ring-brand-primary"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="bg-brand-primary hover:bg-brand-primary-dark disabled:opacity-50 text-white px-4 py-2 rounded-xl text-xs font-bold transition-all shadow-sm flex items-center gap-1 cursor-pointer flex-shrink-0"
          >
            <span>Send</span>
            <span className="material-symbols-outlined text-[15px]">send</span>
          </button>
        </form>
      </div>
    </section>
  );
}
