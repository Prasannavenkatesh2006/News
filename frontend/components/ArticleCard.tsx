import { MessageSquare, Share2, Bookmark, ExternalLink, Clock, TrendingUp } from 'lucide-react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { VoteButtons } from './VoteButtons';
import Image from 'next/image';

interface ArticleCardProps {
  post: {
    id: string | number;
    title: string;
    content?: string;
    summary?: string;
    image_url?: string;
    image?: string;
    source_name?: string;
    source?: string;
    url?: string;
    source_url?: string;
    importance_score?: number;
    upvotes?: number;
    downvotes?: number;
    comment_count?: number;
    created_at: string;
    published_at?: string;
    state?: string;
    city?: string;
    country?: string;
    metadata?: {
      original_engagement?: number;
      entities?: string[];
      image_url?: string;
    };
  };
  onVote?: (id: string | number, dir: 1 | -1) => void;
}

// Format timestamp properly
function formatTimestamp(dateString: string): string {
  try {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);
    
    if (seconds < 60) return 'just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
    
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined });
  } catch {
    return 'recently';
  }
}

export function ArticleCard({ post, onVote }: ArticleCardProps) {
  const score = post.importance_score || 50;

  // Normalize source name/url
  const sourceName = post.source_name || post.source || 'News Source';
  const sourceUrl = post.source_url || post.url;
  
  // Get summary
  let summary = post.summary || post.content || '';
  
  // Clean markdown artifacts and trim
  summary = summary
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/[🔗📌⬆️🌟💬☆][^\n]*/g, '')
    .replace(/\n+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();

  // Ensure 200-word summary
  const words = summary.split(' ');
  if (words.length > 200) {
    summary = words.slice(0, 200).join(' ') + '...';
  }

  // Get image
  const imageUrl = post.image_url || post.image || post.metadata?.image_url;

  // Importance styling
  const getImportanceBadge = () => {
    if (score >= 80) {
      return { icon: '🔥', label: 'BREAKING', className: 'bg-red-50 text-red-600 border-red-100' };
    }
    if (score >= 60) {
      return { icon: '⚡', label: 'IMPORTANT', className: 'bg-orange-50 text-orange-600 border-orange-100' };
    }
    if (score >= 40) {
      return { icon: '📌', label: 'NOTABLE', className: 'bg-blue-50 text-blue-600 border-blue-100' };
    }
    return null;
  };

  const badge = getImportanceBadge();
  const sourceColor = getSourceColor(sourceName);

  return (
    <motion.article
      initial={{ opacity: 0, y: 15 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.3 }}
      className="group"
    >
      <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden hover:border-blue-400 hover:shadow-xl hover:shadow-blue-500/5 transition-all duration-300">
        
        <div className="flex gap-1 p-0">
          {/* Voting Column (Left) - Reddit Style */}
          <div className="bg-slate-50/50 border-r border-slate-100 px-2 py-4">
            <VoteButtons 
              postId={post.id} 
              initialUpvotes={post.upvotes || 0} 
              initialDownvotes={post.downvotes || 0}
              onVote={onVote}
            />
          </div>

          {/* Content Column */}
          <div className="flex-1 min-w-0 p-5">
            
            {/* Meta Row: Source + Time + Importance */}
            <div className="flex items-center gap-3 mb-4 flex-wrap text-[11px]">
              {/* Source Badge */}
              <div className="flex items-center gap-2 px-2.5 py-1.5 bg-slate-100 rounded-lg border border-slate-200">
                <div className={`w-2 h-2 rounded-full ${sourceColor}`} />
                <span className="font-bold text-slate-700 uppercase tracking-tighter">
                  {sourceName}
                </span>
              </div>

              {/* Time */}
              <div className="flex items-center gap-1.5 text-slate-500 font-medium">
                <Clock className="w-3.5 h-3.5" />
                <span>{formatTimestamp(post.published_at || post.created_at)}</span>
              </div>

              {/* Importance Badge */}
              {badge && (
                <div className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border font-bold uppercase tracking-wide ${badge.className}`}>
                  <span>{badge.icon}</span>
                  {badge.label}
                </div>
              )}
            </div>

            {/* Headline - Large and Bold */}
            <Link href={`/posts/${post.id}`}>
              <h2 className="text-xl md:text-2xl font-black text-slate-900 mb-3 leading-tight hover:text-blue-600 transition-colors cursor-pointer line-clamp-2">
                {post.title}
              </h2>
            </Link>

            {/* Summary */}
            {summary && (
              <p className="text-[15px] text-slate-600 mb-5 leading-relaxed line-clamp-3">
                {summary}
              </p>
            )}

            {/* Content Context & Actions */}
            <div className="flex flex-col md:flex-row gap-5">
              
              {/* Image (if available) */}
              {imageUrl && (
                <div className="md:w-48 flex-shrink-0">
                  <div className="rounded-xl overflow-hidden bg-slate-100 border border-slate-200 aspect-[16/10]">
                    <Image 
                      src={imageUrl} 
                      alt={post.title}
                      width={300}
                      height={180}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                      unoptimized={true}
                    />
                  </div>
                </div>
              )}

              {/* Action Bar */}
              <div className="flex flex-1 items-end justify-between">
                <div className="flex items-center gap-1 sm:gap-3 flex-wrap">
                  {/* Comments */}
                  <Link 
                    href={`/posts/${post.id}#comments`}
                    className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-500 hover:text-slate-900 transition-all border border-slate-100"
                  >
                    <MessageSquare className="w-4 h-4" />
                    <span className="text-sm font-bold">{post.comment_count || 0}</span>
                  </Link>

                  {/* Share */}
                  <button className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-500 hover:text-slate-900 transition-all border border-slate-100">
                    <Share2 className="w-4 h-4" />
                    <span className="text-sm font-bold">Share</span>
                  </button>

                  {/* Bookmark */}
                  <button className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-500 hover:text-slate-900 transition-all border border-slate-100">
                    <Bookmark className="w-4 h-4" />
                    <span className="text-sm font-bold">Save</span>
                  </button>
                </div>

                {/* External Link */}
                {sourceUrl && (
                  <a 
                    href={sourceUrl} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-50 hover:bg-blue-600 text-blue-700 hover:text-white transition-all font-bold text-sm border border-blue-100/50 shadow-sm"
                  >
                    <ExternalLink className="w-4 h-4" />
                    <span>View Full News</span>
                  </a>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </motion.article>
  );
}

// Source color helper
function getSourceColor(sourceName: string): string {
  const colors: Record<string, string> = {
    'hackernews': 'bg-orange-500',
    'reddit': 'bg-orange-600',
    'github': 'bg-slate-900',
    'wikipedia': 'bg-blue-600',
    'twitter': 'bg-sky-500',
    'x': 'bg-slate-900',
    'linkedin': 'bg-blue-700',
    'producthunt': 'bg-orange-500',
    'youtube': 'bg-red-600',
    'google trends': 'bg-blue-500',
    'newsapi': 'bg-cyan-500',
  };
  
  const key = sourceName.toLowerCase();
  return colors[key] || 'bg-blue-600';
}
