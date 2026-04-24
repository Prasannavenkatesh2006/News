'use client';

import { useState, useEffect } from 'react';
import { getTrending } from '@/lib/api';
import Sidebar from '../components/Sidebar';
import { TrendingUp, Clock, Calendar, Hash, MessageSquare, ArrowUp, Loader2 } from 'lucide-react';
import Link from 'next/link';

function timeAgo(dateStr: string) {
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    return `${Math.floor(hrs / 24)}d ago`;
}

export default function TrendingPage() {
    const [items, setItems] = useState<any[]>([]);
    const [period, setPeriod] = useState('day');
    const [loading, setLoading] = useState(true);

    useEffect(() => { load(); }, [period]);

    const load = async () => {
        setLoading(true);
        try {
            const data = await getTrending(period, 30);
            setItems(data);
        } catch { } finally { setLoading(false); }
    };

    return (
        <div className="main-with-sidebar">
            <Sidebar />

            <div className="max-w-[800px] mx-auto px-6 py-12">
                <div className="mb-10">
                    <div className="flex items-center gap-4 mb-4">
                        <div className="w-12 h-12 rounded-2xl bg-orange-500 flex items-center justify-center shadow-lg shadow-orange-500/20">
                            <TrendingUp className="w-6 h-6 text-white" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-black text-slate-900 tracking-tight">Trending News</h1>
                            <p className="text-slate-500 font-medium font-sans">Top stories ranked by PULSE importance algorithms.</p>
                        </div>
                    </div>

                    <div className="flex items-center gap-1.5 bg-slate-100 p-1.5 rounded-2xl w-fit">
                        {[
                            { val: 'hour', label: 'Last Hour', icon: <Clock size={14} /> },
                            { val: 'day', label: 'Today', icon: <Calendar size={14} /> },
                            { val: 'week', label: 'Week', icon: <Calendar size={14} /> },
                            { val: 'month', label: 'Month', icon: <Calendar size={14} /> },
                        ].map(p => (
                            <button 
                                key={p.val} 
                                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-black transition-all ${
                                    period === p.val 
                                        ? 'bg-white text-orange-600 shadow-sm' 
                                        : 'text-slate-500 hover:text-slate-900'
                                }`}
                                onClick={() => setPeriod(p.val)}
                            >
                                {p.icon}
                                {p.label.toUpperCase()}
                            </button>
                        ))}
                    </div>
                </div>

                {loading ? (
                    <div className="py-20 flex flex-col items-center gap-4">
                        <Loader2 className="w-10 h-10 animate-spin text-orange-500" />
                        <span className="text-slate-400 font-bold uppercase tracking-widest text-xs">Ranking headlines...</span>
                    </div>
                ) : items.length === 0 ? (
                    <div className="py-20 bg-slate-50 rounded-3xl border-2 border-dashed border-slate-200 text-center">
                        <div className="text-4xl mb-4">📉</div>
                        <h3 className="text-slate-900 font-bold">No trending items yet</h3>
                        <p className="text-slate-500">Try selecting a wider time range.</p>
                    </div>
                ) : (
                    <div className="space-y-3">
                        {items.map((item, i) => (
                            <div key={item.id} className="bg-white border border-slate-100 rounded-3xl p-5 hover:border-orange-200 hover:shadow-xl hover:shadow-orange-500/5 transition-all group">
                                <div className="flex gap-5">
                                    <div className="flex flex-col items-center gap-3">
                                        <div className={`w-10 h-10 rounded-2xl flex items-center justify-center font-black text-sm shadow-sm ${
                                            i === 0 ? 'bg-orange-500 text-white' : 
                                            i === 1 ? 'bg-orange-400 text-white' : 
                                            i === 2 ? 'bg-orange-300 text-white' : 
                                            'bg-slate-100 text-slate-500 border border-slate-200'
                                        }`}>
                                            {i + 1}
                                        </div>
                                        {item.score && (
                                            <div className="flex items-center gap-1 text-[10px] font-black text-orange-600 bg-orange-50 px-2 py-1 rounded-lg">
                                                🔥{item.score.toFixed(0)}
                                            </div>
                                        )}
                                    </div>
                                    
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-3 mb-2 flex-wrap">
                                            {item.community && (
                                                <Link href={`/communities/${item.community}`} className="text-[10px] font-black text-blue-600 uppercase tracking-wider bg-blue-50 px-2 py-1 rounded-md flex items-center gap-1 border border-blue-100">
                                                    <Hash size={10} /> {item.community}
                                                </Link>
                                            )}
                                            <span className="text-[11px] text-slate-400 font-bold uppercase tracking-tighter flex items-center gap-1">
                                                <Clock size={12} /> {timeAgo(item.created_at)}
                                            </span>
                                        </div>
                                        
                                        <Link href={`/posts/${item.id}`}>
                                            <h2 className="text-xl font-black text-slate-900 group-hover:text-orange-600 transition-colors line-clamp-2 leading-tight mb-4">
                                                {item.title}
                                            </h2>
                                        </Link>
                                        
                                        <div className="flex items-center gap-6">
                                            <div className="flex items-center gap-1.5 text-slate-400 font-black text-xs uppercase tracking-wider">
                                                <ArrowUp size={14} className="text-emerald-500" />
                                                {item.upvotes} UPVOTES
                                            </div>
                                            <Link href={`/posts/${item.id}#comments`} className="flex items-center gap-1.5 text-slate-400 font-black text-xs uppercase tracking-wider hover:text-slate-900 transition-colors">
                                                <MessageSquare size={14} className="text-blue-500" />
                                                {item.comment_count} COMMENTS
                                            </Link>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
