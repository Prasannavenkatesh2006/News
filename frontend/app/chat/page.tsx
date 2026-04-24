'use client';
import { useState, useEffect, useRef } from 'react';
import { apiFetch } from '@/lib/api';

interface Message {
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
}

const SUGGESTED_PROMPTS = [
    "What are the latest trends in AI technology?",
    "Summarize the most recent economic news",
    "What natural disasters have been reported recently?",
    "What's happening in global politics?",
    "Show me recent climate and environment news",
    "What are the top health and medicine developments?",
];

function TypingIndicator() {
    return (
        <div style={{ display: 'flex', gap: 4, alignItems: 'center', padding: '12px 16px' }}>
            {[0, 1, 2].map(i => (
                <div key={i} style={{
                    width: 8, height: 8, borderRadius: '50%',
                    background: 'var(--accent)',
                    animation: `bounce 1.2s ease-in-out ${i * 0.2}s infinite`,
                }} />
            ))}
            <style>{`
        @keyframes bounce {
          0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
          40% { transform: scale(1); opacity: 1; }
        }
      `}</style>
        </div>
    );
}

function MessageBubble({ message }: { message: Message }) {
    const isUser = message.role === 'user';
    return (
        <div style={{
            display: 'flex',
            justifyContent: isUser ? 'flex-end' : 'flex-start',
            marginBottom: 16,
            gap: 10,
            alignItems: 'flex-end',
        }}>
            {!isUser && (
                <div style={{
                    width: 32, height: 32, borderRadius: '50%', flexShrink: 0,
                    background: 'linear-gradient(135deg, var(--accent), var(--accent-secondary))',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: '0.9rem',
                }}>🤖</div>
            )}
            <div style={{
                maxWidth: '75%',
                padding: '12px 16px',
                borderRadius: isUser ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
                background: isUser
                    ? 'linear-gradient(135deg, var(--accent), #5a4bd1)'
                    : 'var(--bg-card)',
                border: isUser ? 'none' : '1px solid var(--border)',
                color: isUser ? 'white' : 'var(--text-primary)',
                fontSize: '0.9rem',
                lineHeight: 1.6,
                boxShadow: isUser ? '0 4px 12px var(--accent-glow)' : 'none',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
            }}>
                {message.content}
                <div style={{
                    fontSize: '0.7rem',
                    color: isUser ? 'rgba(255,255,255,0.6)' : 'var(--text-muted)',
                    marginTop: 4,
                    textAlign: 'right',
                }}>
                    {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
            </div>
            {isUser && (
                <div style={{
                    width: 32, height: 32, borderRadius: '50%', flexShrink: 0,
                    background: 'var(--surface-2)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: '0.9rem',
                }}>👤</div>
            )}
        </div>
    );
}

export default function ChatPage() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [error, setError] = useState('');
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const sendMessage = async (text?: string) => {
        const content = text || input.trim();
        if (!content) return;
        setInput('');
        setError('');

        const userMsg: Message = { role: 'user', content, timestamp: new Date().toISOString() };
        setMessages(prev => [...prev, userMsg]);
        setLoading(true);

        try {
            const payload: any = { query: content };
            if (sessionId) payload.session_id = sessionId;

            const res = await apiFetch('/api/conversations/chat', {
                method: 'POST',
                body: JSON.stringify(payload),
            });

            if (res.session_id && !sessionId) {
                setSessionId(res.session_id);
            }

            const assistantMsg: Message = {
                role: 'assistant',
                content: res.response || res.answer || 'I could not generate a response.',
                timestamp: new Date().toISOString(),
            };
            setMessages(prev => [...prev, assistantMsg]);
        } catch (e: any) {
            setError(e.message || 'Chat is temporarily unavailable.');
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: '⚠️ I\'m having trouble connecting right now. The AI service may be starting up. Please try again in a moment.',
                timestamp: new Date().toISOString(),
            }]);
        } finally {
            setLoading(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    const clearChat = () => {
        setMessages([]);
        setSessionId(null);
        setError('');
    };

    return (
        <>
            <nav className="navbar">
                <div className="navbar-inner">
                    <a href="/" className="logo">⚡ ANIP Social</a>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                        <span style={{
                            padding: '3px 10px', borderRadius: 20, fontSize: '0.72rem', fontWeight: 700,
                            background: 'rgba(0, 184, 148, 0.15)', color: 'var(--sentiment-positive)',
                            border: '1px solid rgba(0, 184, 148, 0.3)',
                        }}>🟢 AI Online</span>
                        {messages.length > 0 && (
                            <button className="btn btn-outline btn-sm" onClick={clearChat}>🗑 Clear</button>
                        )}
                        <a href="/" className="btn btn-outline btn-sm">← Feed</a>
                    </div>
                </div>
            </nav>

            <div style={{
                maxWidth: 800, margin: '0 auto', height: 'calc(100vh - 64px)',
                display: 'flex', flexDirection: 'column', padding: '0 20px',
            }}>
                {/* Header */}
                <div style={{ padding: '20px 0 12px', borderBottom: '1px solid var(--border)' }}>
                    <h1 style={{ fontSize: '1.3rem', fontWeight: 800, marginBottom: 4 }}>
                        🤖 ANIP Intelligence Chat
                    </h1>
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                        Ask anything about news, events, or analysis. Powered by RAG over ANIP's article database.
                    </p>
                </div>

                {/* Messages Area */}
                <div style={{ flex: 1, overflowY: 'auto', padding: '20px 0', scrollbarWidth: 'thin' }}>
                    {messages.length === 0 && (
                        <div style={{ textAlign: 'center', padding: '40px 0' }}>
                            <div style={{ fontSize: '3rem', marginBottom: 16 }}>🤖</div>
                            <h2 style={{ fontWeight: 700, marginBottom: 8 }}>Ask ANIP anything</h2>
                            <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', marginBottom: 24, maxWidth: 400, margin: '0 auto 24px' }}>
                                I have access to all articles processed by ANIP's AI pipeline. Ask about news, trends, or specific events.
                            </p>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, justifyContent: 'center', maxWidth: 600, margin: '0 auto' }}>
                                {SUGGESTED_PROMPTS.map((prompt, i) => (
                                    <button
                                        key={i}
                                        onClick={() => sendMessage(prompt)}
                                        style={{
                                            background: 'var(--bg-card)', border: '1px solid var(--border)',
                                            borderRadius: 20, padding: '8px 14px', cursor: 'pointer',
                                            color: 'var(--text-secondary)', fontSize: '0.83rem',
                                            transition: 'all 0.2s',
                                        }}
                                        onMouseEnter={e => {
                                            (e.target as HTMLElement).style.borderColor = 'var(--accent)';
                                            (e.target as HTMLElement).style.color = 'var(--accent)';
                                        }}
                                        onMouseLeave={e => {
                                            (e.target as HTMLElement).style.borderColor = 'var(--border)';
                                            (e.target as HTMLElement).style.color = 'var(--text-secondary)';
                                        }}
                                    >
                                        {prompt}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    {messages.map((msg, i) => (
                        <MessageBubble key={i} message={msg} />
                    ))}

                    {loading && (
                        <div style={{ display: 'flex', alignItems: 'flex-end', gap: 10, marginBottom: 16 }}>
                            <div style={{
                                width: 32, height: 32, borderRadius: '50%',
                                background: 'linear-gradient(135deg, var(--accent), var(--accent-secondary))',
                                display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.9rem',
                            }}>🤖</div>
                            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '16px 16px 16px 4px' }}>
                                <TypingIndicator />
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* Input Area */}
                <div style={{ padding: '12px 0 20px', borderTop: '1px solid var(--border)' }}>
                    {error && (
                        <div style={{ color: 'var(--danger)', fontSize: '0.82rem', marginBottom: 8 }}>⚠️ {error}</div>
                    )}
                    <div style={{ display: 'flex', gap: 10 }}>
                        <textarea
                            className="input"
                            style={{
                                flex: 1, minHeight: 48, maxHeight: 120, resize: 'none',
                                fontFamily: 'inherit', lineHeight: 1.5, paddingTop: 12,
                            }}
                            placeholder="Ask about news, events, trends... (Enter to send, Shift+Enter for newline)"
                            value={input}
                            onChange={e => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            disabled={loading}
                        />
                        <button
                            className="btn btn-primary"
                            onClick={() => sendMessage()}
                            disabled={loading || !input.trim()}
                            style={{ alignSelf: 'flex-end', minWidth: 64, position: 'relative' }}
                        >
                            {loading ? '...' : '➤'}
                        </button>
                    </div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 6 }}>
                        Powered by ANIP RAG pipeline · {messages.length} messages
                        {sessionId && ` · Session: ${sessionId.substring(0, 8)}...`}
                    </div>
                </div>
            </div>
        </>
    );
}
