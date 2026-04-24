'use client';

import { useState, useEffect, useMemo } from 'react';
import Sidebar from '../components/Sidebar';
import { MapPin, TrendingUp, Filter, Loader2, ChevronRight, Share2, Bookmark } from 'lucide-react';
import Link from 'next/link';

interface Article {
    id: number;
    title: string;
    content?: string;
    source?: string;
    url: string;
    published_at?: string;
    state?: string;
    topic?: string;
    sentiment?: string;
    importance_score?: number;
    created_at: string;
}

const TOPIC_ICON: Record<string, string> = {
    Technology: '💻', Economy: '📈', Politics: '🏛️', Health: '🏥',
    Sports: '🏏', Entertainment: '🎬', Climate: '🌍', Science: '🔬',
    Education: '📚', Business: '💼',
};

function timeAgo(d: string) {
    try {
        const s = Math.floor((Date.now() - new Date(d).getTime()) / 1000);
        if (s < 60) return `${s}s`;
        if (s < 3600) return `${Math.floor(s / 60)}m`;
        if (s < 86400) return `${Math.floor(s / 3600)}h`;
        if (s < 604800) return `${Math.floor(s / 86400)}d`;
        return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    } catch {
        return 'recently';
    }
}

const STATE_PAGES = [
    { name: 'Tamil Nadu', path: '/tamil-nadu' },
    { name: 'Telangana', path: '/telangana' },
    { name: 'West Bengal', path: '/west-bengal' },
    { name: 'Karnataka', path: '/karnataka' },
    { name: 'Maharashtra', path: '/maharashtra' },
    { name: 'Delhi', path: '/delhi' },
    { name: 'Gujarat', path: '/gujarat' },
];

export default function KarnatakaPage() {
    const [articles, setArticles] = useState<Article[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedTopic, setSelectedTopic] = useState('');
    const [minImportance, setMinImportance] = useState(0);
    const [error, setError] = useState<string | null>(null);

    const fetchNews = async () => {
        try {
            setError(null);
            const url = `/api/v1/social/feed?state=Karnataka&country=India&limit=80`;
            const res = await fetch(url);
            if (!res.ok) throw new Error('Failed to fetch');
            const data: Article[] = await res.json();
            setArticles(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Could not load articles');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        setLoading(true);
        fetchNews();
        const interval = setInterval(fetchNews, 30000);
        return () => clearInterval(interval);
    }, []);

    const topics = useMemo(() => {
        const t: Record<string, number> = {};
        articles.forEach(a => { if (a.topic) t[a.topic] = (t[a.topic] || 0) + 1; });
        return Object.entries(t).sort((a, b) => b[1] - a[1]).slice(0, 8);
    }, [articles]);

    const filteredArticles = useMemo(() =>
        articles.filter(a => 
            (selectedTopic ? a.topic === selectedTopic : true) &&
            ((a.importance_score || 0) >= minImportance)
        ),
        [articles, selectedTopic, minImportance]
    );

    return (
        <div className="main-with-sidebar">
            <Sidebar />
            
            <div className="max-w-[1200px] mx-auto px-6 py-10">
                <div className="flex flex-col lg:flex-row gap-10">
                    
                    {/* Main Content */}
                    <div className="flex-1 min-w-0">
                        <div className="mb-8">
                            <div className="flex items-center gap-4 mb-4">
                                <div className="w-14 h-14 rounded-3xl bg-blue-600 flex items-center justify-center shadow-xl shadow-blue-500/20">
                                    <MapPin className="w-7 h-7 text-white" />
                                </div>
                                <div>
                                    <h1 className="text-4xl font-black text-slate-900 tracking-tight">Karnataka</h1>
                                    <p className="text-slate-500 font-bold uppercase tracking-widest text-[10px]">Real-time state intelligence</p>
                                </div>
                            </div>
                            
                            {/* Regional Select Mini-Nav */}
                            <div className="flex gap-2 overflow-x-auto pb-4 scrollbar-none">
                                {STATE_PAGES.map(state => (
                                    <Link 
                                        key={state.path} 
                                        href={state.path}
                                        className={`px-4 py-2 rounded-xl text-xs font-black transition-all border whitespace-nowrap ${
                                            state.path === '/karnataka' 
                                                ? 'bg-blue-600 text-white border-blue-600 shadow-md shadow-blue-500/10' 
                                                : 'bg-white text-slate-500 border-slate-100 hover:border-blue-400'
                                        }`}
                                    >
                                        {state.name.toUpperCase()}
                                    </Link>
                                ))}
                            </div>
                        </div>

                        {error && (
                            <div className="bg-rose-50 border border-rose-100 p-4 rounded-2xl text-rose-600 font-bold mb-6">
                                ⚠️ {error}
                            </div>
                        )}

                        <div className="space-y-4">
                            {loading ? (
                                Array.from({ length: 5 }).map((_, i) => (
                                    <div key={i} className="h-40 bg-slate-50 border border-slate-100 rounded-3xl animate-pulse" />
                                ))
                            ) : filteredArticles.length === 0 ? (
                                <div className="py-20 text-center bg-slate-50 rounded-3xl border-2 border-dashed border-slate-200">
                                    <p className="text-slate-400 font-bold">No articles found matching filters</p>
                                </div>
                            ) : (
                                filteredArticles.map(article => {
                                    const importance = article.importance_score || 0;
                                    const badge = importance >= 80 ? '🔥 BREAKING' : importance >= 60 ? '⚡ IMPORTANT' : importance >= 40 ? '📌 NOTABLE' : null;
                                    const badgeColor = importance >= 80 ? 'text-rose-600 bg-rose-50 border-rose-100' : importance >= 60 ? 'text-orange-600 bg-orange-50 border-orange-100' : 'text-blue-600 bg-blue-50 border-blue-100';

                                    return (
                                        <article key={article.id} className="bg-white border border-slate-100 rounded-3xl p-6 hover:shadow-xl hover:shadow-blue-500/5 transition-all group">
                                            <div className="flex items-center gap-3 mb-4 text-[11px] font-black uppercase tracking-wider">
                                                <span className="px-2.5 py-1.5 bg-slate-100 text-slate-700 rounded-lg border border-slate-200">{article.source || 'KARNATAKA'}</span>
                                                {badge && <span className={`px-2.5 py-1.5 rounded-lg border ${badgeColor}`}>{badge}</span>}
                                                <span className="ml-auto text-slate-400">{timeAgo(article.published_at || article.created_at)}</span>
                                            </div>
                                            <a href={article.url} target="_blank" rel="noopener noreferrer" className="block group/title">
                                                <h2 className="text-xl font-black text-slate-900 group-hover/title:text-blue-600 transition-colors leading-tight mb-3">
                                                    {article.title}
                                                </h2>
                                            </a>
                                            <p className="text-slate-600 text-sm line-clamp-2 leading-relaxed mb-6">
                                                {article.content?.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1').replace(/\*\*([^*]+)\*\*/g, '$1')}
                                            </p>
                                            <div className="flex items-center justify-between pt-4 border-t border-slate-50">
                                                <div className="flex items-center gap-3">
                                                    <button className="text-slate-400 hover:text-blue-600 transition-colors"><Share2 size={16} /></button>
                                                    <button className="text-slate-400 hover:text-blue-600 transition-colors"><Bookmark size={16} /></button>
                                                </div>
                                                <a href={article.url} target="_blank" rel="noopener noreferrer" className="text-[11px] font-black text-blue-600 flex items-center gap-1 group-hover:translate-x-1 transition-transform uppercase tracking-widest">
                                                    Read Full Story <ChevronRight size={14} />
                                                </a>
                                            </div>
                                        </article>
                                    );
                                })
                            )}
                        </div>
                    </div>

                    {/* Filters Sidebar */}
                    <aside className="w-full lg:w-80 flex flex-col gap-6">
                        <div className="bg-slate-50 border border-slate-100 rounded-3xl p-6 sticky top-10">
                            <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-6 flex items-center gap-2">
                                <Filter size={14} /> Intelligence Filters
                            </h3>

                            {/* Importance Slider */}
                            <div className="mb-10">
                                <div className="flex justify-between items-center mb-4">
                                    <span className="text-xs font-bold text-slate-700">Min. Importance</span>
                                    <span className="text-xs font-black text-blue-600 bg-blue-50 px-2 py-0.5 rounded-md">{minImportance}+</span>
                                </div>
                                <input
                                    type="range"
                                    min="0"
                                    max="90"
                                    step="10"
                                    value={minImportance}
                                    onChange={(e) => setMinImportance(parseInt(e.target.value))}
                                    className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                                />
                                <div className="flex justify-between mt-2 text-[9px] font-black text-slate-400 uppercase tracking-tighter">
                                    <span>All</span>
                                    <span>Notable</span>
                                    <span>Breaking</span>
                                </div>
                            </div>

                            <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-4">Topics</h3>
                            <div className="flex flex-col gap-1.5">
                                <button 
                                    onClick={() => setSelectedTopic('')}
                                    className={`px-4 py-2.5 rounded-xl text-xs font-black text-left transition-all ${
                                        selectedTopic === '' ? 'bg-blue-600 text-white shadow-md shadow-blue-500/10' : 'bg-white border border-slate-100 text-slate-600 hover:border-blue-400'
                                    }`}
                                >
                                    ALL TOPICS
                                </button>
                                {topics.map(([topic, count]) => (
                                    <button 
                                        key={topic}
                                        onClick={() => setSelectedTopic(topic)}
                                        className={`px-4 py-2.5 rounded-xl text-xs font-black text-left flex items-center justify-between transition-all ${
                                            selectedTopic === topic ? 'bg-blue-600 text-white shadow-md shadow-blue-500/10' : 'bg-white border border-slate-100 text-slate-600 hover:border-blue-400'
                                        }`}
                                    >
                                        <span>{TOPIC_ICON[topic] || '📰'} {topic.toUpperCase()}</span>
                                        <span className="opacity-50">{count}</span>
                                    </button>
                                ))}
                            </div>
                        </div>
                    </aside>
                </div>
            </div>
        </div>
    );
}
