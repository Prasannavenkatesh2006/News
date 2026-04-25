'use client';

import { useState, useEffect } from 'react';
import { getCommunities, getPosts, votePost, toggleBookmark } from '@/lib/api';
import Sidebar from '../../components/Sidebar';
import { 
    ArrowUp, 
    ArrowDown, 
    MessageSquare, 
    Bookmark, 
    Share2, 
    Users, 
    Activity, 
    ChevronRight,
    Loader2,
    Hash
} from 'lucide-react';
import Link from 'next/link';

interface Post {
    id: string;
    title: string;
    content?: string;
    author_username: string;
    community_name?: string;
    upvotes: number;
    downvotes: number;
    comment_count: number;
    created_at: string;
    user_vote?: 1 | -1 | null;
}

interface Community {
    id: number;
    name: string;
    slug: string;
    description?: string;
    member_count: number;
}

const COMMUNITY_ICON: Record<string, string> = {
    technology: '💻', economy: '📈', politics: '🏛️', climate: '🌍',
    health: '🏥', sports: '🏏', entertainment: '🎬', 'tamil-nadu': '🏛️',
    india: '🇮🇳', science: '🔬', education: '📚', 'natural-disasters': '⚠️',
};

function timeAgo(d: string) {
    const s = Math.floor((Date.now() - new Date(d).getTime()) / 1000);
    if (s < 60) return `${s}s`;
    if (s < 3600) return `${Math.floor(s / 60)}m`;
    if (s < 86400) return `${Math.floor(s / 3600)}h`;
    return `${Math.floor(s / 86400)}d`;
}

function PostCard({ post }: { post: Post }) {
    const [votes, setVotes] = useState({ up: post.upvotes, down: post.downvotes });
    const [voted, setVoted] = useState<null | 1 | -1>(post.user_vote ?? null);
    const [bookmarked, setBookmarked] = useState(false);
    const score = votes.up - votes.down;

    const handleVote = async (e: React.MouseEvent, type: 1 | -1) => {
        e.preventDefault();
        try {
            const r = await votePost(post.id, { vote_type: type });
            setVotes({ up: r.upvotes, down: r.downvotes });
            setVoted(voted === type ? null : type);
        } catch { }
    };

    const handleBookmark = async (e: React.MouseEvent) => {
        e.preventDefault();
        try { await toggleBookmark('post', post.id); setBookmarked(!bookmarked); } catch { }
    };

    return (
        <article className="bg-white border border-slate-100 rounded-3xl p-6 hover:shadow-xl hover:shadow-blue-500/5 transition-all group">
            <div className="flex gap-6">
                {/* Vote Column */}
                <div className="flex flex-col items-center gap-1 bg-slate-50 rounded-2xl p-2 h-fit border border-slate-100">
                    <button onClick={e => handleVote(e, 1)} className={`p-1.5 rounded-lg transition-all ${voted === 1 ? 'bg-emerald-500 text-white shadow-lg shadow-emerald-500/20' : 'text-slate-400 hover:bg-emerald-50 hover:text-emerald-500'}`}>
                        <ArrowUp size={18} />
                    </button>
                    <span className={`text-sm font-black ${score > 0 ? 'text-emerald-600' : score < 0 ? 'text-rose-600' : 'text-slate-900'}`}>{score}</span>
                    <button onClick={e => handleVote(e, -1)} className={`p-1.5 rounded-lg transition-all ${voted === -1 ? 'bg-rose-500 text-white shadow-lg shadow-rose-500/20' : 'text-slate-400 hover:bg-rose-50 hover:text-rose-500'}`}>
                        <ArrowDown size={18} />
                    </button>
                </div>

                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-3 text-[10px] font-black uppercase tracking-widest text-slate-400">
                        <Link href={`/users/${post.author_username}`} className="text-blue-600 hover:underline">u/{post.author_username}</Link>
                        <span>·</span>
                        <span>{timeAgo(post.created_at)} AGO</span>
                    </div>

                    <Link href={`/posts/${post.id}`} className="block">
                        <h2 className="text-xl font-black text-slate-900 leading-tight mb-3 group-hover:text-blue-600 transition-colors">
                            {post.title}
                        </h2>
                    </Link>

                    {post.content && (
                        <p className="text-slate-500 text-sm line-clamp-2 leading-relaxed mb-6 font-medium">
                            {post.content}
                        </p>
                    )}

                    <div className="flex items-center justify-between pt-4 border-t border-slate-50">
                        <div className="flex items-center gap-6">
                            <Link href={`/posts/${post.id}`} className="flex items-center gap-2 text-[11px] font-black text-slate-400 hover:text-blue-600 transition-colors">
                                <MessageSquare size={16} /> {post.comment_count} NODES
                            </Link>
                            <button onClick={handleBookmark} className={`flex items-center gap-2 text-[11px] font-black transition-colors ${bookmarked ? 'text-orange-500' : 'text-slate-400 hover:text-orange-500'}`}>
                                <Bookmark size={16} fill={bookmarked ? "currentColor" : "none"} /> {bookmarked ? 'SAVED' : 'SAVE'}
                            </button>
                        </div>
                        <div className="text-blue-600 text-[10px] font-black flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            ANALYZE <ChevronRight size={14} />
                        </div>
                    </div>
                </div>
            </div>
        </article>
    );
}

export default function CommunityPage({ params }: { params: { slug: string } }) {
    const slug = params.slug;
    const [posts, setPosts] = useState<Post[]>([]);
    const [community, setCommunity] = useState<Community | null>(null);
    const [allCommunities, setAllCommunities] = useState<Community[]>([]);
    const [loading, setLoading] = useState(true);
    const [sortBy, setSortBy] = useState<'hot' | 'new' | 'top'>('hot');

    useEffect(() => {
        const load = async () => {
            try {
                const [communityPosts, communities] = await Promise.all([
                    getPosts(slug, 40),
                    getCommunities(),
                ]);
                setPosts(communityPosts);
                setAllCommunities(communities);
                const found = communities.find((c: Community) => c.slug === slug);
                setCommunity(found || null);
            } catch { } finally {
                setLoading(false);
            }
        };
        load();
    }, [slug]);

    const sortedPosts = [...posts].sort((a, b) => {
        if (sortBy === 'new') return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        if (sortBy === 'top') return (b.upvotes - b.downvotes) - (a.upvotes - a.downvotes);
        const age = (h: string) => (Date.now() - new Date(h).getTime()) / 3600000;
        return ((b.upvotes - b.downvotes) / (age(b.created_at) + 2)) - ((a.upvotes - a.downvotes) / (age(a.created_at) + 2));
    });

    if (loading) return (
        <div className="main-with-sidebar justify-center items-center h-screen flex">
            <Loader2 className="w-10 h-10 animate-spin text-blue-600" />
        </div>
    );

    return (
        <div className="main-with-sidebar">
            <Sidebar />
            
            <div className="max-w-[1200px] mx-auto px-6 py-10">
                {/* Hero Header */}
                <div className="bg-white border border-slate-100 rounded-[40px] p-10 shadow-2xl shadow-slate-200/50 mb-10 overflow-hidden relative">
                    <div className="absolute top-0 right-0 w-64 h-64 bg-slate-50 rounded-full -mr-32 -mt-32 opacity-50" />
                    
                    <div className="flex flex-col md:flex-row gap-8 items-center relative z-10">
                        <div className="w-24 h-24 rounded-[32px] bg-blue-600 flex items-center justify-center text-4xl shadow-2xl shadow-blue-500/20 shrink-0">
                            {COMMUNITY_ICON[slug] || '🌐'}
                        </div>
                        <div className="flex-1 text-center md:text-left">
                            <h1 className="text-4xl font-black text-slate-900 tracking-tight mb-2">c/{community?.name || slug}</h1>
                            <p className="text-slate-500 font-medium text-lg max-w-2xl mb-4">
                                {community?.description || `Intelligence gathering and critical analysis for the ${slug} sector.`}
                            </p>
                            <div className="flex justify-center md:justify-start gap-6">
                                <div className="flex items-center gap-2 text-xs font-black text-slate-400 uppercase tracking-widest">
                                    <Users size={16} className="text-blue-500" /> {community?.member_count ?? 0} Agents
                                </div>
                                <div className="flex items-center gap-2 text-xs font-black text-slate-400 uppercase tracking-widest">
                                    <Activity size={16} className="text-emerald-500" /> {posts.length} Active Nodes
                                </div>
                            </div>
                        </div>
                        <Link href="/communities" className="px-6 py-3 rounded-2xl bg-slate-100 text-slate-600 font-black text-[10px] uppercase tracking-widest hover:bg-slate-200 transition-all shrink-0">
                            View All Communities
                        </Link>
                    </div>
                </div>

                <div className="flex flex-col lg:flex-row gap-10">
                    <div className="flex-1 min-w-0">
                        {/* Sort Controls */}
                        <div className="flex gap-2 mb-8 bg-slate-100 p-1.5 rounded-2xl w-fit">
                            {(['hot', 'new', 'top'] as const).map(s => (
                                <button 
                                    key={s} 
                                    onClick={() => setSortBy(s)} 
                                    className={`px-6 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${
                                        sortBy === s ? 'bg-white text-blue-600 shadow-sm' : 'text-slate-400 hover:text-slate-600'
                                    }`}
                                >
                                    {s}
                                </button>
                            ))}
                        </div>

                        <div className="space-y-4">
                            {sortedPosts.length === 0 ? (
                                <div className="py-20 text-center bg-slate-50 rounded-[32px] border-2 border-dashed border-slate-100">
                                    <div className="text-4xl mb-4 opacity-20">📡</div>
                                    <p className="text-slate-400 font-bold uppercase tracking-widest text-xs">No active intelligence in this hub yet</p>
                                </div>
                            ) : (
                                sortedPosts.map(post => <PostCard key={post.id} post={post} />)
                            )}
                        </div>
                    </div>

                    <aside className="w-full lg:w-80 space-y-6">
                        <div className="bg-slate-50 border border-slate-100 rounded-[32px] p-8">
                            <h3 className="text-[11px] font-black text-slate-400 uppercase tracking-widest mb-6">Cluster Info</h3>
                            <p className="text-sm text-slate-600 font-medium leading-relaxed mb-6">
                                {community?.description || `Auto-curated intelligence stream for ${slug}. Monitoring global sources 24/7.`}
                            </p>
                            <div className="space-y-4 pt-6 border-t border-slate-200">
                                <div className="flex justify-between">
                                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Privacy</span>
                                    <span className="text-[10px] font-black text-emerald-600 uppercase tracking-widest">Public Feed</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Throughput</span>
                                    <span className="text-[10px] font-black text-blue-600 uppercase tracking-widest">High Speed</span>
                                </div>
                            </div>
                        </div>

                        <div className="bg-white border border-slate-100 rounded-[32px] p-8">
                            <h3 className="text-[11px] font-black text-slate-400 uppercase tracking-widest mb-6">Adjacent Hubs</h3>
                            <div className="flex flex-col gap-2">
                                {allCommunities.filter(c => c.slug !== slug).slice(0, 6).map(c => (
                                    <Link key={c.id} href={`/communities/${c.slug}`} className="flex items-center gap-3 p-3 rounded-2xl hover:bg-slate-50 transition-all group">
                                        <div className="w-8 h-8 rounded-xl bg-slate-100 flex items-center justify-center text-sm group-hover:bg-blue-600 group-hover:text-white transition-all">
                                            {COMMUNITY_ICON[c.slug] || '🌐'}
                                        </div>
                                        <span className="text-xs font-black text-slate-600 group-hover:text-slate-900 uppercase tracking-widest">c/{c.slug}</span>
                                    </Link>
                                ))}
                            </div>
                        </div>
                    </aside>
                </div>
            </div>
        </div>
    );
}
