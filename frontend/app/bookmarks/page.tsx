'use client';

import { useState, useEffect } from 'react';
import { getBookmarks, toggleBookmark } from '@/lib/api';
import Sidebar from '../components/Sidebar';
import { 
    Bookmark, 
    Trash2, 
    FileText, 
    Globe, 
    Filter,
    ChevronRight,
    Loader2
} from 'lucide-react';
import Link from 'next/link';

export default function BookmarksPage() {
    const [bookmarks, setBookmarks] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<string>('');

    useEffect(() => { load(); }, [filter]);

    const load = async () => {
        setLoading(true);
        try {
            const data = await getBookmarks(filter || undefined);
            setBookmarks(data);
        } catch { } finally { setLoading(false); }
    };

    const handleRemove = async (type: string, id: string) => {
        await toggleBookmark(type, id).catch(() => { });
        setBookmarks(prev => prev.filter(b => b.target_id !== id));
    };

    return (
        <div className="main-with-sidebar">
            <Sidebar />
            
            <div className="max-w-[1000px] mx-auto px-6 py-12">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-10">
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-2xl bg-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
                            <Bookmark className="w-6 h-6 text-white" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-black text-slate-900 tracking-tight">Intelligence Vault</h1>
                            <p className="text-slate-500 font-medium">Secured local storage for critical information.</p>
                        </div>
                    </div>

                    <div className="flex bg-slate-100 p-1.5 rounded-2xl gap-1">
                        <button 
                            className={`px-6 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${filter === '' ? 'bg-white text-blue-600 shadow-sm' : 'text-slate-400 hover:text-slate-600'}`} 
                            onClick={() => setFilter('')}
                        >
                            All Logs
                        </button>
                        <button 
                            className={`px-6 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${filter === 'post' ? 'bg-white text-blue-600 shadow-sm' : 'text-slate-400 hover:text-slate-600'}`} 
                            onClick={() => setFilter('post')}
                        >
                            Posts
                        </button>
                        <button 
                            className={`px-6 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${filter === 'article' ? 'bg-white text-blue-600 shadow-sm' : 'text-slate-400 hover:text-slate-600'}`} 
                            onClick={() => setFilter('article')}
                        >
                            Articles
                        </button>
                    </div>
                </div>

                {loading ? (
                    <div className="flex items-center justify-center py-20">
                        <Loader2 className="w-10 h-10 animate-spin text-blue-600" />
                    </div>
                ) : bookmarks.length === 0 ? (
                    <div className="py-24 text-center bg-white border border-slate-100 rounded-[40px] shadow-2xl shadow-slate-200/50">
                        <div className="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-6 text-slate-300">
                            <Bookmark size={40} />
                        </div>
                        <h2 className="text-xl font-black text-slate-900 mb-2">Vault is Empty</h2>
                        <p className="text-slate-500 font-medium max-w-xs mx-auto">No intelligence has been flagged for archival in your profile.</p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {bookmarks.map(b => (
                            <div key={b.id} className="group bg-white border border-slate-100 rounded-[32px] p-8 hover:shadow-2xl hover:shadow-slate-200/50 transition-all flex flex-col relative overflow-hidden">
                                <div className="absolute top-0 right-0 w-32 h-32 bg-slate-50 rounded-full -mr-16 -mt-16 opacity-30 group-hover:scale-150 transition-transform duration-500" />
                                
                                <div className="flex items-center justify-between gap-4 mb-6 relative z-10">
                                    <span className={`px-3 py-1.5 rounded-xl text-[10px] font-black uppercase tracking-widest border ${
                                        b.target_type === 'article' ? 'bg-emerald-50 text-emerald-600 border-emerald-100' : 'bg-blue-50 text-blue-600 border-blue-100'
                                    }`}>
                                        {b.target_type === 'article' ? 'External Intel' : 'Social Feed'}
                                    </span>
                                    <button 
                                        onClick={() => handleRemove(b.target_type, b.target_id)}
                                        className="p-2 text-slate-300 hover:text-rose-500 hover:bg-rose-50 rounded-xl transition-all"
                                    >
                                        <Trash2 size={16} />
                                    </button>
                                </div>
                                
                                <Link href={b.target_type === 'article' ? b.url || '#' : `/posts/${b.target_id}`} className="relative z-10 flex-1">
                                    <h3 className="text-lg font-black text-slate-900 leading-tight mb-4 group-hover:text-blue-600 transition-colors">
                                        {b.title}
                                    </h3>
                                    {b.preview && (
                                        <p className="text-sm text-slate-500 font-medium leading-relaxed mb-6 line-clamp-3">
                                            {b.preview}
                                        </p>
                                    )}
                                </Link>

                                <div className="flex items-center justify-between mt-auto pt-6 border-t border-slate-50 relative z-10">
                                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                                        Vaulted {new Date(b.created_at).toLocaleDateString()}
                                    </span>
                                    <div className="text-blue-600 text-[10px] font-black flex items-center gap-1 group-hover:translate-x-1 transition-transform">
                                        ACCESS DATA <ChevronRight size={14} />
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
