'use client';

import { useState, useEffect, useMemo } from 'react';
import { getFeed } from '@/lib/api';
import Sidebar from '../components/Sidebar';
import { Globe, TrendingUp, Loader2, Filter } from 'lucide-react';

interface Article {
    id: number;
    title: string;
    content?: string;
    source?: string;
    url: string;
    published_at?: string;
    state?: string;
    country?: string;
    topic?: string;
    sentiment?: string;
    created_at: string;
}

const TOPIC_ICON: Record<string, string> = {
    Technology: '💻', Economy: '📈', Politics: '🏛️', Health: '🏥',
    Sports: '🏏', Entertainment: '🎬', Climate: '🌍', Science: '🔬',
    Education: '📚', Business: '💼',
};

function timeAgo(d: string) {
    const s = Math.floor((Date.now() - new Date(d).getTime()) / 1000);
    if (s < 60) return `${s}s`;
    if (s < 3600) return `${Math.floor(s / 60)}m`;
    if (s < 86400) return `${Math.floor(s / 3600)}h`;
    return `${Math.floor(s / 86400)}d`;
}

export default function WorldNewsPage() {
    const [articles, setArticles] = useState<Article[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedTopic, setSelectedTopic] = useState('');
    const [selectedCountry, setSelectedCountry] = useState('');
    const [error, setError] = useState<string | null>(null);

    const fetchNews = async () => {
        try {
            setError(null);
            const data = await getFeed({ limit: 100 });
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

    const countries = useMemo(() => {
        const c: Record<string, number> = {};
        articles.forEach(a => { 
            const country = a.country || a.state || 'Unknown';
            if (country) c[country] = (c[country] || 0) + 1; 
        });
        return Object.entries(c).sort((a, b) => b[1] - a[1]).slice(0, 8);
    }, [articles]);

    const filteredArticles = useMemo(() => {
        let filtered = articles;
        if (selectedTopic) filtered = filtered.filter(a => a.topic === selectedTopic);
        if (selectedCountry) filtered = filtered.filter(a => (a.country || a.state) === selectedCountry);
        return filtered;
    }, [articles, selectedTopic, selectedCountry]);

    return (
        <div className="main-with-sidebar">
            <Sidebar />
            
            <div className="max-w-[1200px] mx-auto px-6 py-10">
                <div className="flex flex-col md:flex-row justify-between items-start gap-8">
                    
                    {/* Main Feed Content */}
                    <div className="flex-1 min-w-0">
                        <div className="mb-10">
                            <div className="flex items-center gap-3 mb-2">
                                <div className="w-12 h-12 rounded-2xl bg-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
                                    <Globe className="w-6 h-6 text-white" />
                                </div>
                                <div>
                                    <h1 className="text-3xl font-black text-slate-900 tracking-tight">World Intelligence</h1>
                                    <p className="text-slate-500 font-medium">Real-time global headlines & emerging trends</p>
                                </div>
                            </div>
                        </div>

                        {error && (
                            <div className="bg-rose-50 border border-rose-100 p-4 rounded-2xl text-rose-600 font-bold mb-6 flex items-center gap-3">
                                <span>⚠️ {error}</span>
                            </div>
                        )}

                        <div className="space-y-4">
                            {loading ? (
                                Array.from({ length: 6 }).map((_, i) => (
                                    <div key={i} className="h-40 bg-slate-50 border border-slate-100 rounded-2xl animate-pulse" />
                                ))
                            ) : filteredArticles.length === 0 ? (
                                <div className="text-center py-20 bg-slate-50 rounded-3xl border-2 border-dashed border-slate-200">
                                    <p className="text-slate-400 font-bold">No global articles matching your filters</p>
                                </div>
                            ) : (
                                filteredArticles.map(article => (
                                    <a key={article.id} href={article.url} target="_blank" rel="noopener noreferrer" className="block group">
                                        <article className="bg-white border border-slate-100 hover:border-blue-400 p-6 rounded-2xl transition-all duration-300 hover:shadow-xl hover:shadow-blue-500/5">
                                            <div className="flex items-center gap-3 mb-4 text-[11px] font-bold uppercase tracking-wider">
                                                <span className="px-2.5 py-1.5 bg-blue-50 text-blue-600 rounded-lg border border-blue-100">{article.source || 'WORLD'}</span>
                                                <span className="text-slate-400 flex items-center gap-1">
                                                    <Globe className="w-3 h-3" /> {article.country || 'Global'}
                                                </span>
                                                <span className="ml-auto text-slate-400">{timeAgo(article.created_at)} ago</span>
                                            </div>
                                            <h2 className="text-xl font-black text-slate-900 group-hover:text-blue-600 transition-colors line-clamp-2 leading-tight mb-3">
                                                {article.title}
                                            </h2>
                                            {article.content && (
                                                <p className="text-slate-600 text-[14px] line-clamp-2 leading-relaxed">
                                                    {article.content.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1').replace(/\*\*([^*]+)\*\*/g, '$1')}
                                                </p>
                                            )}
                                        </article>
                                    </a>
                                ))
                            )}
                        </div>
                    </div>

                    {/* Filters Sidebar */}
                    <aside className="w-full md:w-80 flex flex-col gap-6 sticky top-10">
                        <div className="bg-slate-50 border border-slate-100 rounded-3xl p-6">
                            <h3 className="text-xs font-black text-slate-400 uppercase tracking-widest mb-6 flex items-center gap-2">
                                <TrendingUp className="w-4 h-4" /> Global Activity
                            </h3>
                            <div className="grid grid-cols-2 gap-4 mb-8">
                                <div className="bg-white p-4 rounded-2xl border border-slate-100 shadow-sm">
                                    <div className="text-2xl font-black text-blue-600">{articles.length}</div>
                                    <div className="text-[10px] text-slate-400 font-bold uppercase">Feed Items</div>
                                </div>
                                <div className="bg-white p-4 rounded-2xl border border-slate-100 shadow-sm">
                                    <div className="text-2xl font-black text-emerald-600">{countries.length}</div>
                                    <div className="text-[10px] text-slate-400 font-bold uppercase">Regions</div>
                                </div>
                            </div>

                            <h3 className="text-xs font-black text-slate-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                                <Filter className="w-4 h-4" /> Regions
                            </h3>
                            <div className="flex flex-col gap-2">
                                <button 
                                    onClick={() => setSelectedCountry('')} 
                                    className={`px-4 py-2.5 rounded-xl text-sm font-bold transition-all text-left ${selectedCountry === '' ? 'bg-blue-600 text-white shadow-md shadow-blue-500/10' : 'bg-white border border-slate-100 text-slate-600 hover:border-blue-400'}`}
                                >
                                    All Regions
                                </button>
                                {countries.map(([country, count]) => (
                                    <button 
                                        key={country} 
                                        onClick={() => setSelectedCountry(country === selectedCountry ? '' : country)}
                                        className={`px-4 py-2.5 rounded-xl text-sm font-bold transition-all flex items-center justify-between ${selectedCountry === country ? 'bg-blue-600 text-white shadow-md shadow-blue-500/10' : 'bg-white border border-slate-100 text-slate-600 hover:border-blue-400'}`}
                                    >
                                        <span>🌍 {country}</span>
                                        <span className="opacity-60 text-[11px]">{count}</span>
                                    </button>
                                ))}
                            </div>

                            <h3 className="text-xs font-black text-slate-400 uppercase tracking-widest mb-4 mt-8 flex items-center gap-2">
                                <Filter className="w-4 h-4" /> Topics
                            </h3>
                            <div className="flex flex-col gap-2">
                                <button 
                                    onClick={() => setSelectedTopic('')} 
                                    className={`px-4 py-2.5 rounded-xl text-sm font-bold transition-all text-left ${selectedTopic === '' ? 'bg-blue-600 text-white shadow-md shadow-blue-500/10' : 'bg-white border border-slate-100 text-slate-600 hover:border-blue-400'}`}
                                >
                                    All Topics
                                </button>
                                {topics.map(([topic, count]) => (
                                    <button 
                                        key={topic} 
                                        onClick={() => setSelectedTopic(topic === selectedTopic ? '' : topic)}
                                        className={`px-4 py-2.5 rounded-xl text-sm font-bold transition-all flex items-center justify-between ${selectedTopic === topic ? 'bg-blue-600 text-white shadow-md shadow-blue-500/10' : 'bg-white border border-slate-100 text-slate-600 hover:border-blue-400'}`}
                                    >
                                        <span>{TOPIC_ICON[topic] || '📰'} {topic}</span>
                                        <span className="opacity-60 text-[11px]">{count}</span>
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
