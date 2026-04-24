'use client';

import { useState, useEffect, useRef } from 'react';
import { useLiveFeed, getScraperStats, AutoPost } from '@/lib/websocket';
import Sidebar from '../components/Sidebar';
import { 
    Zap, 
    Robot, 
    CheckCircle, 
    Activity, 
    TrendingUp, 
    Globe, 
    Cpu, 
    Database, 
    LayoutDashboard,
    Loader2,
    Search,
    ChevronRight,
    ArrowUpRight
} from 'lucide-react';
import Link from 'next/link';

// ── Platform metadata ────────────────────────────────────────────
const PLATFORMS: Record<string, { icon: string; color: string; label: string }> = {
    hackernews: { icon: '🔥', color: '#FF6600', label: 'Hacker News' },
    reddit: { icon: '📰', color: '#FF4500', label: 'Reddit' },
    reddit_post: { icon: '📰', color: '#FF4500', label: 'Reddit' },
    github: { icon: '📦', color: '#24292e', label: 'GitHub' },
    github_trending: { icon: '📦', color: '#24292e', label: 'GitHub' },
    google_trends: { icon: '🔍', color: '#4285F4', label: 'Google Trends' },
    wikipedia: { icon: '📚', color: '#636e72', label: 'Wikipedia' },
    product_hunt: { icon: '🚀', color: '#DA552F', label: 'Product Hunt' },
    newsapi: { icon: '📡', color: '#0984e3', label: 'NewsAPI' },
    gdelt: { icon: '🌍', color: '#6c5ce7', label: 'GDELT' },
    x: { icon: '🐦', color: '#000000', label: 'X (Twitter)' },
    x_trending: { icon: '🐦', color: '#000000', label: 'X (Twitter)' },
    youtube: { icon: '📹', color: '#d63031', label: 'YouTube' },
    linkedin: { icon: '💼', color: '#0077b5', label: 'LinkedIn' },
};

const ALL_SCRAPERS = [
    { key: 'hackernews', label: 'Hacker News', interval: '1 min', cost: 'Free ✓' },
    { key: 'reddit', label: 'Reddit', interval: '1 min', cost: 'Free ✓' },
    { key: 'github', label: 'GitHub Trending', interval: '5 min', cost: 'Free ✓' },
    { key: 'wikipedia', label: 'Wikipedia', interval: '1 min', cost: 'Free ✓' },
    { key: 'google_trends', label: 'Google Trends', interval: '2 min', cost: 'Free ✓' },
    { key: 'product_hunt', label: 'Product Hunt', interval: '10 min', cost: 'Free ✓' },
    { key: 'newsapi', label: 'NewsAPI + GDELT', interval: '1 min', cost: 'Dev Plan' },
    { key: 'youtube', label: 'YouTube', interval: '5 min', cost: 'Free ✓' },
    { key: 'x', label: 'X (Twitter)', interval: '2 min', cost: '$100/mo' },
    { key: 'linkedin', label: 'LinkedIn', interval: '10 min', cost: 'Limited' },
];

function timeAgo(d: string) {
    const s = Math.floor((Date.now() - new Date(d).getTime()) / 1000);
    if (s < 60) return `${s}s`;
    if (s < 3600) return `${Math.floor(s / 60)}m`;
    return `${Math.floor(s / 3600)}h`;
}

function StatCard({
    label, value, sub, icon, accent,
}: { label: string; value: string | number; sub?: string; icon: React.ReactNode; accent?: string }) {
    return (
        <div className="bg-white border border-slate-100 rounded-2xl p-6 shadow-sm hover:shadow-md transition-all duration-300">
            <div className="flex justify-between items-start mb-4">
                <div style={{ color: accent }} className="w-10 h-10 rounded-xl bg-slate-50 flex items-center justify-center">
                    {icon}
                </div>
            </div>
            <div>
                <div className="text-2xl font-black text-slate-900 tracking-tight">{value}</div>
                <div className="text-xs font-bold text-slate-400 uppercase tracking-widest mt-1">{label}</div>
                {sub && <div className="text-[10px] text-slate-400 mt-2 font-medium">{sub}</div>}
            </div>
        </div>
    );
}

function PostCard({ post, isNew }: { post: AutoPost; isNew: boolean }) {
    const p = PLATFORMS[post.platform] || { icon: '🤖', color: '#6C63FF', label: post.platform };
    const impScore = (post as any).importance_score || 0;
    const impColor = impScore >= 80 ? '#ef4444' : impScore >= 60 ? '#f59e0b' : impScore >= 40 ? '#3b82f6' : 'transparent';
    const impLabel = impScore >= 80 ? 'BREAKING' : impScore >= 60 ? 'IMPORTANT' : impScore >= 40 ? 'Notable' : '';

    return (
        <article className={`p-4 border-b border-slate-50 hover:bg-slate-50/50 transition-all ${isNew ? 'bg-blue-50/10' : ''}`}>
            <div className="flex gap-3 items-center mb-2">
                <span className="text-[10px] font-black uppercase tracking-tighter px-2 py-0.5 rounded-md border" style={{ color: p.color, background: `${p.color}08`, borderColor: `${p.color}15` }}>
                    {p.icon} {p.label}
                </span>
                {impScore >= 40 && (
                    <span className="text-[10px] font-black uppercase tracking-tighter px-2 py-0.5 rounded-md" style={{ color: impColor, background: `${impColor}10` }}>
                        {impLabel} · {impScore}
                    </span>
                )}
                <span className="ml-auto text-[10px] font-bold text-slate-400">{timeAgo(post.created_at)}</span>
            </div>
            <h3 className="text-sm font-bold text-slate-900 leading-snug line-clamp-2">
                {post.title}
            </h3>
            {post.url && (
                <div className="mt-2">
                    <a href={post.url} target="_blank" rel="noopener noreferrer" className="text-[10px] font-bold text-blue-600 flex items-center gap-1 hover:underline">
                        VERIFY SOURCE <ArrowUpRight className="w-3 h-3" />
                    </a>
                </div>
            )}
        </article>
    );
}

export default function DashboardPage() {
    const { posts, newPostsCount, connectionStatus, clearNewCount } = useLiveFeed();
    const [stats, setStats] = useState<any>(null);
    const [tab, setTab] = useState<'feed' | 'scrapers' | 'analytics'>('feed');

    useEffect(() => {
        const load = () => getScraperStats().then(setStats).catch(() => { });
        load();
        const id = setInterval(load, 8000);
        return () => clearInterval(id);
    }, []);

    const ppm = stats?.posts_per_minute || 0;
    const totalPosts = stats?.total_auto_posts || 0;
    const activeScrapers = stats?.active_scrapers || 0;
    const breakdown = stats?.platform_breakdown || {};
    const health = stats?.scraper_health || {};
    const timeline = stats?.timeline || [];

    return (
        <div className="main-with-sidebar">
            <Sidebar />
            
            <div className="max-w-[1400px] mx-auto px-6 py-10">
                {/* Header */}
                <div className="flex justify-between items-end mb-8">
                    <div>
                        <div className="flex items-center gap-3 mb-2">
                            <div className="w-12 h-12 rounded-2xl bg-slate-900 flex items-center justify-center shadow-lg shadow-slate-900/10">
                                <Activity className="w-6 h-6 text-white" />
                            </div>
                            <h1 className="text-3xl font-black text-slate-900 tracking-tight">AI Command Center</h1>
                        </div>
                        <p className="text-slate-500 font-medium">Monitoring 12 autonomous AI agents in real-time</p>
                    </div>
                    {newPostsCount > 0 && (
                        <button onClick={clearNewCount} className="btn btn-primary shadow-xl shadow-blue-500/20 px-6 py-3 rounded-2xl flex items-center gap-2">
                            <span className="w-2 h-2 rounded-full bg-white animate-pulse"></span>
                            {newPostsCount} NEW UPDATES
                        </button>
                    )}
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
                    <StatCard label="Posts / Min" value={ppm.toFixed(1)} sub="Real-time scraping rate" icon={<Zap className="w-5 h-5" />} accent="#f59e0b" />
                    <StatCard label="Autonomous Posts" value={totalPosts.toLocaleString()} sub="Verified by AI pipeline" icon={<Cpu className="w-5 h-5" />} accent="#3b82f6" />
                    <StatCard label="Active Agents" value={`${activeScrapers}/12`} sub="Scraper swarm health" icon={<Globe className="w-5 h-5" />} accent="#10b981" />
                    <StatCard label="Connection" value={connectionStatus === 'connected' ? 'Live' : 'Syncing'} icon={<Activity className="w-5 h-5" />} accent={connectionStatus === 'connected' ? '#10b981' : '#f59e0b'} />
                </div>

                {/* Tabs */}
                <div className="flex items-center gap-1.5 bg-slate-100 p-1.5 rounded-2xl w-fit mb-8">
                    {[
                        { id: 'feed', label: 'Live Content', icon: <TrendingUp size={14} /> },
                        { id: 'scrapers', label: 'Scraper Registry', icon: <Database size={14} /> },
                        { id: 'analytics', label: 'System Analytics', icon: <Activity size={14} /> },
                    ].map(t => (
                        <button 
                            key={t.id} 
                            onClick={() => setTab(t.id as any)}
                            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-black transition-all ${tab === t.id ? 'bg-white text-blue-600 shadow-sm' : 'text-slate-500 hover:text-slate-900'}`}
                        >
                            {t.icon} {t.label.toUpperCase()}
                        </button>
                    ))}
                </div>

                {/* Content */}
                {tab === 'feed' && (
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                        <div className="lg:col-span-2 bg-white border border-slate-100 rounded-3xl overflow-hidden shadow-sm">
                            <div className="px-6 py-5 border-b border-slate-50 flex justify-between items-center bg-slate-50/30">
                                <div className="flex items-center gap-2">
                                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                                    <h2 className="text-sm font-black text-slate-900 uppercase tracking-widest">Autonomous Stream</h2>
                                </div>
                                <span className="text-[10px] font-bold text-slate-400">{posts.length} BUFFERED</span>
                            </div>
                            <div className="max-h-[600px] overflow-y-auto">
                                {posts.length === 0 ? (
                                    <div className="py-20 flex flex-col items-center gap-4">
                                        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
                                        <p className="text-xs font-bold text-slate-400">INITIALIZING AI PIPELINE...</p>
                                    </div>
                                ) : (
                                    posts.map((post, i) => <PostCard key={post.id} post={post} isNew={i < newPostsCount} />)
                                )}
                            </div>
                        </div>

                        <div className="space-y-6">
                            <div className="bg-white border border-slate-100 rounded-3xl p-6 shadow-sm">
                                <h3 className="text-xs font-black text-slate-400 uppercase tracking-widest mb-6">AI Pipeline Tasks</h3>
                                <div className="space-y-4">
                                    {[
                                        { name: 'Quality Guard', status: 'Active', color: 'text-emerald-500' },
                                        { name: 'Entity Extraction', status: 'Processing', color: 'text-blue-500' },
                                        { name: 'Topic Classifier', status: 'Active', color: 'text-emerald-500' },
                                        { name: 'Semantic Dedup', status: 'Active', color: 'text-emerald-500' },
                                    ].map(task => (
                                        <div key={task.name} className="flex justify-between items-center">
                                            <span className="text-xs font-bold text-slate-700">{task.name}</span>
                                            <span className={`text-[10px] font-black uppercase tracking-widest ${task.color}`}>{task.status}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <div className="bg-slate-900 rounded-3xl p-6 text-white shadow-xl shadow-slate-900/20">
                                <h3 className="text-xs font-black text-slate-400 uppercase tracking-widest mb-4">Node Health</h3>
                                <div className="flex items-center gap-4 mb-6">
                                    <div className="text-4xl font-black">99.8<span className="text-xl text-emerald-400">%</span></div>
                                    <div className="text-[10px] font-bold text-slate-400 uppercase leading-snug">Average<br/>Uptime</div>
                                </div>
                                <div className="space-y-3">
                                    <div className="h-1 bg-slate-800 rounded-full overflow-hidden">
                                        <div className="h-full bg-emerald-500 w-[99%]"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {tab === 'scrapers' && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                        {ALL_SCRAPERS.map(s => {
                            const p = PLATFORMS[s.key] || { icon: '🤖', color: '#636e72', label: s.label };
                            return (
                                <div key={s.key} className="bg-white border border-slate-100 rounded-2xl p-5 hover:border-blue-400 transition-all group shadow-sm">
                                    <div className="flex justify-between items-start mb-4">
                                        <div className="text-2xl">{p.icon}</div>
                                        <span className="text-[10px] font-black text-emerald-500 uppercase tracking-widest bg-emerald-50 px-2 py-0.5 rounded-md">Online</span>
                                    </div>
                                    <h3 className="text-sm font-black text-slate-900 mb-1">{s.label}</h3>
                                    <div className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mb-4">Interval: {s.interval}</div>
                                    <div className="flex items-center justify-between mt-4 pt-4 border-t border-slate-50">
                                        <span className="text-[10px] font-bold text-slate-400">{s.cost}</span>
                                        <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-blue-500 transition-colors" />
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}

                {tab === 'analytics' && (
                    <div className="bg-white border border-slate-100 rounded-3xl p-10 shadow-sm text-center">
                        <div className="w-16 h-16 rounded-full bg-blue-50 flex items-center justify-center mx-auto mb-6">
                            <Activity className="w-8 h-8 text-blue-600" />
                        </div>
                        <h3 className="text-xl font-black text-slate-900 mb-2">Detailed Analytics Locked</h3>
                        <p className="text-slate-500 max-w-md mx-auto mb-8">Full historical analysis and predictive trending metrics are currently being indexed by the AI cluster.</p>
                        <button className="btn btn-outline px-8 rounded-xl opacity-50 cursor-not-allowed">EXPORT LOGS</button>
                    </div>
                )}
            </div>
        </div>
    );
}

