'use client';

import { useState, useEffect } from 'react';
import { getPost, getComments, createComment, votePost, voteComment, toggleBookmark } from '@/lib/api';
import Sidebar from '../../components/Sidebar';
import { 
    ArrowUp, 
    ArrowDown, 
    MessageSquare, 
    Bookmark, 
    Share2, 
    User, 
    Clock, 
    Hash, 
    ChevronLeft,
    Send,
    Loader2
} from 'lucide-react';
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

function CommentNode({ comment, postId, depth = 0, onReply }: {
    comment: any; postId: string; depth?: number; onReply: (parentId: string, username: string) => void;
}) {
    const [votes, setVotes] = useState({ up: comment.upvotes, down: comment.downvotes });
    const [voted, setVoted] = useState<null | 1 | -1>(null);
    const score = votes.up - votes.down;

    const handleVote = async (type: 1 | -1) => {
        try {
            const r = await voteComment(comment.id, type);
            setVotes({ up: r.upvotes, down: r.downvotes });
            setVoted(voted === type ? null : type);
        } catch { }
    };

    return (
        <div className={`mt-4 ${depth > 0 ? 'ml-6 pl-6 border-l-2 border-slate-100' : ''}`}>
            <div className="bg-white border border-slate-100 rounded-[20px] p-5 shadow-sm">
                <div className="flex items-center gap-3 mb-3">
                    <div className="w-6 h-6 rounded-lg bg-blue-600 flex items-center justify-center text-[10px] font-black text-white">
                        {comment.author_username?.[0]?.toUpperCase() || '?'}
                    </div>
                    <span className="text-xs font-black text-slate-900">u/{comment.author_username}</span>
                    <span className="text-[10px] font-bold text-slate-400 flex items-center gap-1">
                        <Clock size={10} /> {timeAgo(comment.created_at)}
                    </span>
                </div>
                <p className="text-sm text-slate-600 leading-relaxed mb-4">
                    {comment.content}
                </p>
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-1 bg-slate-50 px-2.5 py-1 rounded-xl border border-slate-100">
                        <button onClick={() => handleVote(1)} className={`p-1 transition-colors ${voted === 1 ? 'text-emerald-500' : 'text-slate-400 hover:text-emerald-500'}`}>
                            <ArrowUp size={14} />
                        </button>
                        <span className="text-xs font-black text-slate-700 min-w-[20px] text-center">{score}</span>
                        <button onClick={() => handleVote(-1)} className={`p-1 transition-colors ${voted === -1 ? 'text-rose-500' : 'text-slate-400 hover:text-rose-500'}`}>
                            <ArrowDown size={14} />
                        </button>
                    </div>
                    {depth < 3 && (
                        <button
                            onClick={() => onReply(comment.id, comment.author_username)}
                            className="text-[11px] font-black text-slate-400 hover:text-blue-600 uppercase tracking-widest transition-colors"
                        >Reply</button>
                    )}
                </div>
            </div>
            {comment.replies?.map((reply: any) => (
                <CommentNode key={reply.id} comment={reply} postId={postId} depth={depth + 1} onReply={onReply} />
            ))}
        </div>
    );
}

export default function PostDetailPage({ params }: { params: { id: string } }) {
    const [post, setPost] = useState<any>(null);
    const [comments, setComments] = useState<any[]>([]);
    const [newComment, setNewComment] = useState('');
    const [replyTo, setReplyTo] = useState<{ id: string; username: string } | null>(null);
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [votes, setVotes] = useState({ up: 0, down: 0 });
    const [voted, setVoted] = useState<null | 1 | -1>(null);
    const [bookmarked, setBookmarked] = useState(false);

    useEffect(() => {
        Promise.all([
            getPost(params.id),
            getComments(params.id),
        ]).then(([p, c]) => {
            setPost(p);
            setVotes({ up: p.upvotes, down: p.downvotes });
            setComments(c);
        }).catch(() => { }).finally(() => setLoading(false));
    }, [params.id]);

    const handleVote = async (type: 1 | -1) => {
        try {
            const r = await votePost(params.id, type);
            setVotes({ up: r.upvotes, down: r.downvotes });
            setVoted(voted === type ? null : type);
        } catch { }
    };

    const handleBookmark = async () => {
        try {
            await toggleBookmark('post', params.id);
            setBookmarked(!bookmarked);
        } catch { }
    };

    const handleComment = async () => {
        if (!newComment.trim()) return;
        setSubmitting(true);
        try {
            const c = await createComment(params.id, newComment, replyTo?.id);
            setNewComment('');
            setReplyTo(null);
            const fresh = await getComments(params.id);
            setComments(fresh);
        } catch (e: any) {
            alert(e.message || 'Please log in to comment');
        } finally {
            setSubmitting(false);
        }
    };

    const handleReply = (parentId: string, username: string) => {
        setReplyTo({ id: parentId, username });
        setNewComment(`@${username} `);
        const box = document.getElementById('comment-box') as HTMLTextAreaElement;
        box?.focus();
        box?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    };

    if (loading) return (
        <div className="main-with-sidebar justify-center items-center h-screen flex">
            <Loader2 className="w-10 h-10 animate-spin text-blue-600" />
        </div>
    );

    if (!post) return (
        <div className="main-with-sidebar justify-center items-center h-screen flex">
            <div className="text-center">
                <h1 className="text-2xl font-black text-slate-900 mb-2">Post not found</h1>
                <Link href="/" className="text-blue-600 font-bold hover:underline">Back to intelligence feed</Link>
            </div>
        </div>
    );

    const score = votes.up - votes.down;

    return (
        <div className="main-with-sidebar">
            <Sidebar />
            
            <div className="max-w-[840px] mx-auto px-6 py-10">
                <Link href="/" className="flex items-center gap-2 text-xs font-black text-slate-400 hover:text-slate-900 transition-all uppercase tracking-[0.2em] mb-8 group">
                    <ChevronLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" /> Back to Intelligence Feed
                </Link>

                {/* Primary Intelligence Block */}
                <div className="bg-white border border-slate-100 rounded-[40px] p-10 shadow-2xl shadow-slate-200/50 relative overflow-hidden mb-10">
                    <div className="absolute top-0 right-0 p-8">
                        <div className="flex flex-col items-center gap-2 bg-slate-50 rounded-2xl p-2 border border-slate-100">
                            <button onClick={() => handleVote(1)} className={`p-2 rounded-xl transition-all ${voted === 1 ? 'bg-emerald-500 text-white shadow-lg shadow-emerald-500/20' : 'text-slate-400 hover:bg-emerald-50'}`}>
                                <ArrowUp size={20} />
                            </button>
                            <span className={`text-lg font-black ${score > 0 ? 'text-emerald-600' : score < 0 ? 'text-rose-600' : 'text-slate-900'}`}>{score}</span>
                            <button onClick={() => handleVote(-1)} className={`p-2 rounded-xl transition-all ${voted === -1 ? 'bg-rose-500 text-white shadow-lg shadow-rose-500/20' : 'text-slate-400 hover:bg-rose-50'}`}>
                                <ArrowDown size={20} />
                            </button>
                        </div>
                    </div>

                    <div className="max-w-[calc(100%-80px)]">
                        <div className="flex items-center gap-3 mb-6 text-[11px] font-black uppercase tracking-widest">
                            {post.community_name && (
                                <Link href={`/communities/${post.community_name}`} className="bg-blue-600 text-white px-3 py-1.5 rounded-xl shadow-lg shadow-blue-500/20 flex items-center gap-1">
                                    <Hash size={12} /> {post.community_name}
                                </Link>
                            )}
                            <span className="text-slate-400">By <u className="text-slate-900 no-underline">u/{post.author_username}</u></span>
                            <span className="text-slate-400">· {timeAgo(post.created_at)}</span>
                        </div>

                        <h1 className="text-4xl font-black text-slate-900 leading-tight mb-8">
                            {post.title}
                        </h1>

                        {post.content && (
                            <div className="text-lg text-slate-600 leading-relaxed font-medium mb-10 bg-slate-50/50 p-8 rounded-[32px] border border-slate-100">
                                {post.content}
                            </div>
                        )}

                        <div className="flex items-center gap-8 pt-8 border-t border-slate-50">
                            <div className="flex items-center gap-2 text-slate-400 font-bold text-xs uppercase tracking-widest">
                                <MessageSquare size={18} className="text-blue-500" /> {comments.length} Discussion Nodes
                            </div>
                            <button onClick={handleBookmark} className={`flex items-center gap-2 font-bold text-xs uppercase tracking-widest transition-all ${bookmarked ? 'text-orange-500' : 'text-slate-400 hover:text-orange-500'}`}>
                                <Bookmark size={18} fill={bookmarked ? "currentColor" : "none"} /> {bookmarked ? 'SAVED' : 'SAVE INTEL'}
                            </button>
                            <button className="flex items-center gap-2 text-slate-400 hover:text-blue-600 font-bold text-xs uppercase tracking-widest transition-all" onClick={() => navigator.clipboard?.writeText(window.location.href)}>
                                <Share2 size={18} /> EXPORT
                            </button>
                        </div>
                    </div>
                </div>

                {/* Discussion Section */}
                <div className="space-y-8">
                    <div className="bg-white border border-slate-100 rounded-[32px] p-8 shadow-xl shadow-slate-200/30">
                        {replyTo && (
                            <div className="flex justify-between items-center bg-blue-50 border border-blue-100 p-3 rounded-xl mb-4">
                                <span className="text-xs font-bold text-blue-600">Replying to <Link href={`/users/${replyTo.username}`} className="font-black">u/{replyTo.username}</Link></span>
                                <button onClick={() => { setReplyTo(null); setNewComment(''); }} className="text-blue-400 hover:text-rose-500"><X size={16} /></button>
                            </div>
                        )}
                        <textarea
                            id="comment-box"
                            className="w-full min-h-[120px] bg-slate-50 border-none rounded-2xl p-5 text-slate-900 placeholder-slate-400 focus:ring-2 focus:ring-blue-500/10 transition-all font-medium text-sm resize-none mb-4"
                            placeholder="Initialize your contribution to this intelligence node..."
                            value={newComment}
                            onChange={e => setNewComment(e.target.value)}
                        />
                        <div className="flex justify-end">
                            <button
                                onClick={handleComment}
                                disabled={submitting || !newComment.trim()}
                                className="bg-blue-600 text-white font-black py-3 px-8 rounded-2xl hover:bg-blue-700 transition-all shadow-xl shadow-blue-500/20 disabled:opacity-50 flex items-center gap-2"
                            >
                                {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <><Send size={14} /> PUBLISH NODE</>}
                            </button>
                        </div>
                    </div>

                    <div className="space-y-6">
                        <h3 className="text-xl font-black text-slate-900 flex items-center gap-3">
                            Analysis Nodes <span className="text-slate-400 text-sm font-bold bg-slate-100 px-3 py-1 rounded-full">{comments.length}</span>
                        </h3>
                        
                        {comments.length === 0 ? (
                            <div className="py-20 text-center bg-slate-50/50 rounded-3xl border-2 border-dashed border-slate-100 italic text-slate-400 font-medium">
                                No discussion nodes recorded for this intelligence block yet.
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {comments.map(c => (
                                    <CommentNode key={c.id} comment={c} postId={params.id} onReply={handleReply} />
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
