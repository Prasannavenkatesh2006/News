'use client';

import { useState, useEffect } from 'react';
import { createPost, getCommunities } from '@/lib/api';
import Sidebar from '../components/Sidebar';
import { Send, FileText, Hash, Loader2, X } from 'lucide-react';
import Link from 'next/link';

interface Community {
    id: number;
    name: string;
    slug: string;
}

export default function SubmitPage() {
    const [title, setTitle] = useState('');
    const [content, setContent] = useState('');
    const [communityId, setCommunityId] = useState<number | undefined>();
    const [communities, setCommunities] = useState<Community[]>([]);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        getCommunities().then(setCommunities).catch(() => { });
    }, []);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!title.trim()) return;
        setLoading(true);
        setError('');
        try {
            await createPost(title, content || undefined, communityId);
            window.location.href = '/';
        } catch (err: any) {
            setError(err.message || 'Failed to create post. Please ensure you are logged in.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="main-with-sidebar">
            <Sidebar />
            
            <div className="max-w-[720px] mx-auto px-6 py-12">
                <div className="mb-10">
                    <div className="flex items-center gap-4 mb-4">
                        <div className="w-12 h-12 rounded-2xl bg-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
                            <FileText className="w-6 h-6 text-white" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-black text-slate-900 tracking-tight">Create Publication</h1>
                            <p className="text-slate-500 font-medium">Broadcast your intelligence to the Pulse network.</p>
                        </div>
                    </div>
                </div>

                <div className="bg-white border border-slate-100 rounded-[32px] p-8 shadow-2xl shadow-slate-200/50">
                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div className="space-y-2">
                            <label className="text-xs font-black text-slate-400 uppercase tracking-widest ml-1 flex items-center gap-2">
                                <Hash size={14} /> Intelligence Cluster
                            </label>
                            <select 
                                className="w-full bg-slate-50 border-none rounded-2xl py-3.5 px-4 text-slate-900 font-medium focus:ring-2 focus:ring-blue-500/20 transition-all appearance-none cursor-pointer"
                                value={communityId || ''} 
                                onChange={e => setCommunityId(e.target.value ? Number(e.target.value) : undefined)}
                            >
                                <option value="">Global Broadcast (No specific area)</option>
                                {communities.map(c => (
                                    <option key={c.id} value={c.id}>{c.name}</option>
                                ))}
                            </select>
                        </div>

                        <div className="space-y-2">
                            <label className="text-xs font-black text-slate-400 uppercase tracking-widest ml-1">Title / Headline</label>
                            <input 
                                className="w-full bg-slate-50 border-none rounded-2xl py-3.5 px-4 text-slate-900 placeholder-slate-400 focus:ring-2 focus:ring-blue-500/20 transition-all font-bold text-lg" 
                                type="text" 
                                value={title} 
                                onChange={e => setTitle(e.target.value)} 
                                placeholder="What's happening?" 
                                required 
                            />
                        </div>

                        <div className="space-y-2">
                            <label className="text-xs font-black text-slate-400 uppercase tracking-widest ml-1">Content / Analysis</label>
                            <textarea 
                                className="w-full bg-slate-50 border-none rounded-3xl py-4 px-4 text-slate-900 placeholder-slate-400 focus:ring-2 focus:ring-blue-500/20 transition-all font-medium min-h-[200px] resize-none" 
                                value={content} 
                                onChange={e => setContent(e.target.value)} 
                                placeholder="Provide supporting data, analysis, or external links..." 
                            />
                        </div>

                        {error && (
                            <div className="bg-rose-50 border border-rose-100 p-4 rounded-2xl text-rose-600 text-xs font-bold">
                                ⚠️ {error}
                            </div>
                        )}

                        <div className="flex items-center gap-4 pt-4">
                            <button 
                                className="flex-1 bg-blue-600 text-white font-black py-4 rounded-2xl hover:bg-blue-700 transition-all shadow-xl shadow-blue-500/20 flex items-center justify-center gap-2 group disabled:opacity-50" 
                                type="submit" 
                                disabled={loading}
                            >
                                {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <>PUBLISH TO FEED <Send className="w-4 h-4" /></>}
                            </button>
                            <Link 
                                href="/" 
                                className="px-6 py-4 rounded-2xl bg-slate-100 text-slate-600 font-black text-xs uppercase tracking-widest hover:bg-slate-200 transition-all"
                            >
                                DISCARD
                            </Link>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
}
