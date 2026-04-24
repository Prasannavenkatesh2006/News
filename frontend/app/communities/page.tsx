'use client';

import { useState, useEffect } from 'react';
import { getCommunities } from '@/lib/api';
import Sidebar from '../components/Sidebar';
import { Users, Hash, Loader2, ChevronRight } from 'lucide-react';
import Link from 'next/link';

interface Community {
    id: number;
    name: string;
    slug: string;
    description?: string;
    member_count: number;
}

export default function CommunitiesPage() {
    const [communities, setCommunities] = useState<Community[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        getCommunities()
            .then(setCommunities)
            .catch(() => { })
            .finally(() => setLoading(false));
    }, []);

    const getIcon = (slug: string) => {
        switch (slug) {
            case 'technology': return '💻';
            case 'economy': return '📈';
            case 'politics': return '🏛️';
            case 'climate': return '🌍';
            case 'health': return '🏥';
            case 'natural-disasters': return '⚠️';
            case 'science': return '🔬';
            case 'sports': return '🏏';
            case 'entertainment': return '🎬';
            default: return '🌐';
        }
    };

    return (
        <div className="main-with-sidebar">
            <Sidebar />
            
            <div className="max-w-[1000px] mx-auto px-6 py-12">
                <div className="mb-12">
                    <div className="flex items-center gap-4 mb-4">
                        <div className="w-12 h-12 rounded-2xl bg-indigo-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
                            <Users className="w-6 h-6 text-white" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-black text-slate-900 tracking-tight">Active Communities</h1>
                            <p className="text-slate-500 font-medium">Topic-based news verification & community discussion</p>
                        </div>
                    </div>
                    <div className="bg-slate-100 p-4 rounded-2xl border border-slate-200/50 text-slate-600 text-sm font-medium">
                        Each community is powered by PULSE's AI classification. Articles are auto-routed based on semantic analysis of incoming news feeds.
                    </div>
                </div>

                {loading ? (
                    <div className="py-20 flex flex-col items-center gap-4">
                        <Loader2 className="w-10 h-10 animate-spin text-indigo-600" />
                        <span className="text-slate-400 font-bold uppercase tracking-widest text-xs">Fetching networks...</span>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {communities.map(c => (
                            <Link key={c.id} href={`/?community=${c.slug}`} className="group">
                                <div className="bg-white border border-slate-100 rounded-3xl p-6 hover:border-indigo-400 hover:shadow-xl hover:shadow-indigo-500/5 transition-all h-full flex flex-col">
                                    <div className="flex items-center gap-4 mb-4">
                                        <div className="w-14 h-14 rounded-2xl bg-slate-50 border border-slate-100 flex items-center justify-center text-2xl group-hover:bg-indigo-50 group-hover:border-indigo-100 transition-colors">
                                            {getIcon(c.slug)}
                                        </div>
                                        <div className="flex-1">
                                            <h2 className="text-xl font-black text-slate-900 group-hover:text-indigo-600 transition-colors flex items-center gap-2">
                                                {c.name}
                                                <ChevronRight className="w-4 h-4 opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition-all" />
                                            </h2>
                                            <div className="flex items-center gap-2">
                                                <span className="text-[10px] font-black text-indigo-500 uppercase tracking-widest bg-indigo-50 px-2 py-0.5 rounded-md">
                                                    #{c.slug}
                                                </span>
                                                <span className="text-[11px] text-slate-400 font-bold">
                                                    {c.member_count} Members
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                    {c.description && (
                                        <p className="text-slate-600 text-sm leading-relaxed mb-6 flex-1">
                                            {c.description}
                                        </p>
                                    )}
                                    <div className="flex items-center justify-between mt-auto pt-4 border-t border-slate-50">
                                        <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Auto-moderated Feed</span>
                                        <div className="flex -space-x-2">
                                            {[1, 2, 3].map(i => (
                                                <div key={i} className="w-6 h-6 rounded-full border-2 border-white bg-slate-200 flex items-center justify-center text-[8px] font-bold text-slate-400">
                                                    U{i}
                                                </div>
                                            ))}
                                            <div className="w-6 h-6 rounded-full border-2 border-white bg-indigo-600 flex items-center justify-center text-[8px] font-bold text-white">
                                                +
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </Link>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
