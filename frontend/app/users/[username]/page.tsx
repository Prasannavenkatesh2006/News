'use client';

import { useState, useEffect } from 'react';
import { getUserProfile, getPosts } from '@/lib/api';
import Sidebar from '../../components/Sidebar';
import { 
    Calendar, 
    Award, 
    FileText, 
    MessageSquare, 
    Bookmark, 
    ChevronRight,
    Loader2
} from 'lucide-react';
import Link from 'next/link';

function timeAgo(dateStr: string) {
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    return `${Math.floor(hrs / 24)}d ago`;
}

export default function UserProfilePage({ params }: { params: { username: string } }) {
    const [profile, setProfile] = useState<any>(null);
    const [posts, setPosts] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        Promise.all([
            getUserProfile(params.username),
            getPosts(undefined, 20),
        ]).then(([p, allPosts]) => {
            setProfile(p);
            setPosts(allPosts.filter((post: any) => post.author_username === params.username));
        }).catch(() => { }).finally(() => setLoading(false));
    }, [params.username]);

    if (loading) return (
        <div className="main-with-sidebar justify-center items-center h-screen flex">
            <Loader2 className="w-10 h-10 animate-spin text-blue-600" />
        </div>
    );

    if (!profile) return (
        <div className="main-with-sidebar justify-center items-center h-screen flex">
            <div className="text-center">
                <h1 className="text-2xl font-black text-slate-900 mb-2">User not found</h1>
                <Link href="/" className="text-blue-600 font-bold hover:underline">Back to intelligence feed</Link>
            </div>
        </div>
    );

    const joinDate = new Date(profile.created_at).toLocaleDateString('en-US', { month: 'long', year: 'numeric' });

    return (
        <div className="main-with-sidebar">
            <Sidebar />
            
            <div className="max-w-[1000px] mx-auto px-6 py-10">
                {/* Profile Identity Card */}
                <div className="bg-white border border-slate-100 rounded-[40px] p-10 shadow-2xl shadow-slate-200/50 mb-10 overflow-hidden relative">
                    <div className="absolute top-0 right-0 w-64 h-64 bg-blue-50 rounded-full -mr-32 -mt-32 opacity-50 contrast-125" />
                    
                    <div className="flex flex-col md:flex-row gap-10 items-start relative z-10">
                        {/* Avatar */}
                        <div className="w-32 h-32 rounded-[40px] bg-blue-600 flex items-center justify-center text-5xl font-black text-white shadow-2xl shadow-blue-500/20 shrink-0">
                            {profile.username[0].toUpperCase()}
                        </div>
                        
                        <div className="flex-1">
                            <div className="flex items-center gap-4 mb-4">
                                <h1 className="text-4xl font-black text-slate-900 tracking-tight">u/{profile.username}</h1>
                                <span className="bg-emerald-50 text-emerald-600 text-[10px] font-black uppercase tracking-widest px-3 py-1.5 rounded-xl border border-emerald-100">Verified Intelligence Agent</span>
                            </div>
                            
                            {profile.bio ? (
                                <p className="text-slate-600 text-lg leading-relaxed mb-8 max-w-2xl font-medium">
                                    {profile.bio}
                                </p>
                            ) : (
                                <p className="text-slate-400 italic mb-8 font-medium">No intelligence biography recorded yet.</p>
                            )}

                            <div className="flex flex-wrap gap-8">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-xl bg-orange-50 flex items-center justify-center text-orange-600 border border-orange-100">
                                        <Award size={20} />
                                    </div>
                                    <div>
                                        <div className="text-xl font-black text-slate-900">{profile.karma}</div>
                                        <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Karma Score</div>
                                    </div>
                                </div>
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center text-blue-600 border border-blue-100">
                                        <FileText size={20} />
                                    </div>
                                    <div>
                                        <div className="text-xl font-black text-slate-900">{profile.post_count}</div>
                                        <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Intelligence Blocks</div>
                                    </div>
                                </div>
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-xl bg-emerald-50 flex items-center justify-center text-emerald-600 border border-emerald-100">
                                        <Calendar size={20} />
                                    </div>
                                    <div>
                                        <div className="text-lg font-black text-slate-900">{joinDate}</div>
                                        <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Deployment Date</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="flex flex-col lg:flex-row gap-10">
                    <div className="flex-1">
                        <h2 className="text-xl font-black text-slate-900 mb-6 flex items-center gap-3">
                            Recent Contributions <span className="text-slate-400 text-sm font-bold bg-slate-50 px-3 py-1 rounded-full">{posts.length}</span>
                        </h2>
                        
                        <div className="space-y-4">
                            {posts.length === 0 ? (
                                <div className="py-20 text-center bg-slate-50/50 rounded-3xl border-2 border-dashed border-slate-100 italic text-slate-400 font-medium">
                                    No public intelligence blocks recorded.
                                </div>
                            ) : (
                                posts.map(p => (
                                    <Link key={p.id} href={`/posts/${p.id}`} className="block group">
                                        <div className="bg-white border border-slate-100 rounded-3xl p-6 hover:shadow-xl hover:shadow-blue-500/5 transition-all group-hover:border-blue-200">
                                            <div className="flex items-center gap-3 mb-4">
                                                {p.community_name && (
                                                    <span className="text-[10px] font-black text-blue-600 bg-blue-50 px-2.5 py-1.5 rounded-lg border border-blue-100 uppercase tracking-widest">
                                                        c/{p.community_name}
                                                    </span>
                                                )}
                                                <span className="text-[10px] font-bold text-slate-400 ml-auto">{timeAgo(p.created_at)}</span>
                                            </div>
                                            <h3 className="text-lg font-black text-slate-900 group-hover:text-blue-600 transition-colors mb-3 leading-tight">{p.title}</h3>
                                            {p.content && (
                                                <p className="text-slate-500 text-sm line-clamp-2 leading-relaxed mb-4">{p.content}</p>
                                            )}
                                            <div className="flex items-center justify-between pt-4 border-t border-slate-50">
                                                <div className="flex items-center gap-4 text-[11px] font-black text-slate-400">
                                                    <span className="flex items-center gap-1"><Award size={14} className="text-orange-400" /> {p.upvotes} UPVOTES</span>
                                                    <span className="flex items-center gap-1"><MessageSquare size={14} className="text-blue-400" /> {p.comment_count} NODES</span>
                                                </div>
                                                <div className="text-blue-600 text-[10px] font-black flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                                    ANALYZE <ChevronRight size={14} />
                                                </div>
                                            </div>
                                        </div>
                                    </Link>
                                ))
                            )}
                        </div>
                    </div>

                    <aside className="w-full lg:w-80">
                        <div className="bg-slate-50 border border-slate-100 rounded-[32px] p-8 sticky top-10">
                            <h3 className="text-[11px] font-black text-slate-400 uppercase tracking-widest mb-6">User Statistics</h3>
                            <div className="space-y-6">
                                <div className="flex justify-between items-center">
                                    <span className="text-sm font-bold text-slate-600">Post Karma</span>
                                    <span className="text-sm font-black text-slate-900">{profile.karma}</span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-sm font-bold text-slate-600">Total Comments</span>
                                    <span className="text-sm font-black text-slate-900">{profile.comment_count}</span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-sm font-bold text-slate-600">Account Level</span>
                                    <span className="text-xs font-black text-blue-600 bg-white border border-blue-100 px-2.5 py-1 rounded-lg">Senior Agent</span>
                                </div>
                            </div>

                            <div className="mt-10 pt-8 border-t border-slate-200">
                                <button className="w-full bg-white border border-slate-200 text-slate-900 font-black py-3 rounded-2xl text-xs uppercase tracking-widest hover:bg-slate-100 transition-all flex items-center justify-center gap-2">
                                    <Bookmark size={14} /> Save Profile
                                </button>
                            </div>
                        </div>
                    </aside>
                </div>
            </div>
        </div>
    );
}
