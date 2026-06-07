"use client";

import { useState, useRef, useEffect } from 'react';
import { chatWithAgent } from '@/lib/api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: Date;
}

export default function ChatbotPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    setMessages([
      {
        id: 'welcome',
        sender: 'assistant',
        text: 'Halo! Saya adalah **Fraud AI Assistant**. Saya dapat membantu Anda meneliti dan menganalisis pola kecurangan pada sistem belanja retail. Silakan pilih salah satu pertanyaan cepat di sebelah kiri atau ketik pertanyaan Anda sendiri di kolom bawah.',
        timestamp: new Date()
      }
    ]);
  }, []);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const suggestions = [
    "Mengapa akun USR00010 dicurigai?",
    "Tampilkan 10 akun dengan risiko tertinggi.",
    "Perangkat mana yang paling banyak digunakan bersama?",
    "Alamat pengiriman mana yang dipakai banyak akun palsu?",
    "Berapa banyak akun palsu yang terdeteksi?",
    "Apa pola kecurangan (fraud) yang paling umum terjadi?",
    "Tampilkan jaringan fraud untuk perangkat DVC001."
  ];

  // Auto scroll to bottom of chat
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (messageText: string) => {
    if (!messageText.trim() || loading) return;

    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}-user`,
      sender: 'user',
      text: messageText,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const response = await chatWithAgent(messageText);
      
      const assistantMsg: ChatMessage = {
        id: `msg-${Date.now()}-assistant`,
        sender: 'assistant',
        text: response.reply,
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, assistantMsg]);
    } catch (err: any) {
      console.error(err);
      
      const errorMsg: ChatMessage = {
        id: `msg-${Date.now()}-error`,
        sender: 'assistant',
        text: '⚠️ Maaf, terjadi kesalahan saat menghubungi server chatbot. Pastikan backend FastAPI berjalan.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  // Simple Markdown-like formatter for bullet points, bold text and headers
  const formatMarkdown = (text: string) => {
    return text.split('\n').map((line, idx) => {
      const trimmed = line.trim();
      const className = "text-slate-200 text-sm leading-relaxed";

      // Headers ###
      if (trimmed.startsWith('###')) {
        return (
          <h4 key={idx} className="font-bold text-white text-base mt-4 mb-2 border-b border-slate-800 pb-1">
            {trimmed.replace('###', '').trim()}
          </h4>
        );
      }
      
      // Bullet points - or *
      if (trimmed.startsWith('-') || trimmed.startsWith('*')) {
        const content = trimmed.substring(1).trim();
        return (
          <li key={idx} className="list-disc list-inside ml-2 py-0.5 text-slate-300 text-sm leading-relaxed">
            {renderInlineMarkdown(content)}
          </li>
        );
      }

      // Ordered list 1. 2.
      const ordMatch = trimmed.match(/^(\d+)\.\s(.*)/);
      if (ordMatch) {
        return (
          <div key={idx} className="ml-2 py-1 text-slate-300 text-sm leading-relaxed">
            <span className="font-bold text-red-400">{ordMatch[1]}. </span>
            {renderInlineMarkdown(ordMatch[2])}
          </div>
        );
      }

      return (
        <p key={idx} className={`${className} min-h-[1rem]`}>
          {renderInlineMarkdown(line)}
        </p>
      );
    });
  };

  const renderInlineMarkdown = (text: string) => {
    // Bold matches **text**
    const parts = text.split(/(\*\*.*?\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i} className="font-bold text-white">{part.slice(2, -2)}</strong>;
      }
      // Inline code `code`
      const codeParts = part.split(/(`.*?`)/g);
      return codeParts.map((subPart, j) => {
        if (subPart.startsWith('`') && subPart.endsWith('`')) {
          return <code key={j} className="bg-slate-950 px-1.5 py-0.5 rounded text-red-400 font-mono text-xs">{subPart.slice(1, -1)}</code>;
        }
        return subPart;
      });
    });
  };

  return (
    <div className="flex flex-col lg:flex-row min-h-[calc(100vh-8rem)] gap-6 px-4">
      {/* Sidebar Suggestions */}
      <div className="w-full lg:w-80 flex-shrink-0 flex flex-col gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
          <div>
            <h2 className="text-xl font-bold text-slate-100">Pertanyaan Cepat</h2>
            <p className="text-xs text-slate-500 mt-1">Pilih pertanyaan template di bawah untuk berkonsultasi langsung dengan data analisis.</p>
          </div>

          <div className="flex flex-col gap-2.5">
            {suggestions.map((suggestion, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(suggestion)}
                disabled={loading}
                className="text-left text-xs font-semibold text-slate-400 bg-slate-800/50 hover:bg-red-50 hover:text-red-600 border border-slate-800 hover:border-red-200 p-3 rounded-lg transition-all duration-200 active:scale-98 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                💡 {suggestion}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Chat Area Panel */}
      <div className="flex-1 bg-slate-900 border border-slate-800 rounded-xl shadow-lg flex flex-col h-[560px] lg:h-[calc(100vh-10rem)] overflow-hidden relative">
        <div className="absolute top-0 right-0 h-40 w-40 bg-slate-800 rounded-full translate-x-12 -translate-y-12 opacity-15 pointer-events-none"></div>

        {/* Chat Window Header */}
        <div className="bg-slate-950 px-6 py-4 border-b border-slate-850 flex items-center gap-3">
          <div className="h-2 w-2 rounded-full bg-emerald-500 animate-ping"></div>
          <div>
            <h3 className="font-bold text-white text-sm">Tim Pemeriksa - Asisten AI</h3>
            <p className="text-[10px] text-slate-400">LLaMA-3 Analisis Pola Kecurangan</p>
          </div>
        </div>

        {/* Messages Stream */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4 scrollbar-thin">
          {messages.map((msg) => {
            const isUser = msg.sender === 'user';
            return (
              <div key={msg.id} className={`flex ${isUser ? 'justify-end' : 'justify-start'} animate-fadeIn`}>
                <div className={`max-w-[80%] rounded-xl px-4 py-3 shadow-md ${
                  isUser
                    ? 'bg-red-600 text-white rounded-br-none'
                    : 'bg-slate-800 text-slate-200 rounded-bl-none border border-slate-700/50'
                }`}>
                  {isUser ? (
                    <p className="text-sm font-semibold leading-relaxed break-words">{msg.text}</p>
                  ) : (
                    <div className="space-y-1 break-words w-full overflow-hidden">
                      <ReactMarkdown 
                        remarkPlugins={[remarkGfm]}
                        components={{
                          table: ({node, ...props}) => <div className="overflow-x-auto my-4 w-full"><table className="min-w-full divide-y divide-slate-700/50 border border-slate-700/50 rounded-lg" {...props} /></div>,
                          thead: ({node, ...props}) => <thead className="bg-slate-800/80" {...props} />,
                          th: ({node, ...props}) => <th className="px-3 py-2 text-left text-xs font-semibold text-slate-200 uppercase tracking-wider border-b border-slate-700/50" {...props} />,
                          td: ({node, ...props}) => <td className="px-3 py-2 text-sm text-slate-300 border-b border-slate-700/50" {...props} />,
                          p: ({node, ...props}) => <p className="text-sm text-slate-200 leading-relaxed mb-2" {...props} />,
                          ul: ({node, ...props}) => <ul className="list-disc list-inside ml-2 mb-2 text-sm text-slate-300" {...props} />,
                          ol: ({node, ...props}) => <ol className="list-decimal list-inside ml-2 mb-2 text-sm text-slate-300" {...props} />,
                          li: ({node, ...props}) => <li className="mb-1" {...props} />,
                          h3: ({node, ...props}) => <h3 className="font-bold text-white text-base mt-4 mb-2 border-b border-slate-800 pb-1" {...props} />,
                          h4: ({node, ...props}) => <h4 className="font-bold text-white text-sm mt-3 mb-2" {...props} />,
                          strong: ({node, ...props}) => <strong className="font-bold text-white" {...props} />,
                          code: ({node, inline, className, ...props}: any) => {
                            const match = /language-(\w+)/.exec(className || '')
                            return inline ? (
                              <code className="bg-slate-900 border border-slate-800 px-1.5 py-0.5 rounded text-red-400 font-mono text-xs" {...props} />
                            ) : (
                              <pre className="bg-slate-950 p-3 border border-slate-800 rounded-lg text-slate-300 font-mono text-xs overflow-x-auto mb-2"><code {...props} /></pre>
                            )
                          }
                        }}
                      >
                        {msg.text}
                      </ReactMarkdown>
                    </div>
                  )}
                  <span className="block text-[9px] text-slate-400 text-right mt-1.5 font-mono">
                    {mounted ? msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
                  </span>
                </div>
              </div>
            );
          })}
          
          {loading && (
            <div className="flex justify-start animate-pulse">
              <div className="bg-slate-850 border border-slate-800 rounded-xl rounded-bl-none px-4 py-3 flex items-center gap-2">
                <div className="flex gap-1.5">
                  <span className="h-1.5 w-1.5 rounded-full bg-slate-400 animate-bounce"></span>
                  <span className="h-1.5 w-1.5 rounded-full bg-slate-400 animate-bounce delay-100"></span>
                  <span className="h-1.5 w-1.5 rounded-full bg-slate-400 animate-bounce delay-200"></span>
                </div>
                <span className="text-xs text-slate-400 font-medium">Asisten sedang mengetik...</span>
              </div>
            </div>
          )}
        </div>

        {/* Bottom Input Area */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend(input);
          }}
          className="bg-slate-950 px-6 py-4 border-t border-slate-850 flex gap-3"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
            placeholder="Tanyakan pola fraud atau cari detail akun..."
            className="flex-1 bg-slate-850 hover:bg-slate-800/80 focus:bg-slate-850 border border-slate-700 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-red-500 placeholder-slate-500 transition-all disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="bg-red-600 hover:bg-red-700 disabled:bg-slate-800 disabled:text-slate-500 text-white font-bold px-5 py-2.5 rounded-lg shadow transition-all active:scale-98 disabled:cursor-not-allowed flex items-center"
          >
            Kirim
          </button>
        </form>
      </div>
    </div>
  );
}
