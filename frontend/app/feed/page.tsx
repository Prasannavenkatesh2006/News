'use client';

import { ArticleCard } from '@/components/ArticleCard';
import { useInfiniteQuery } from '@tanstack/react-query';
import { Loader2, TrendingUp, Clock, Filter } from 'lucide-react';
import { useState } from 'react';
import Sidebar from '../components/Sidebar';

export default function FeedPage() {
  const [sortBy, setSortBy] = useState<'importance' | 'new' | 'hot'>('importance');

  const { data, fetchNextPage, hasNextPage, isFetchingNextPage, isLoading } = useInfiniteQuery({
    queryKey: ['feed', sortBy],
    queryFn: async ({ pageParam = 0 }) => {
      const res = await fetch(`/api/v1/social/feed?sort=${sortBy}&offset=${pageParam}&limit=20`);
      if (!res.ok) throw new Error('Network response was not ok');
      return res.json();
    },
    initialPageParam: 0,
    getNextPageParam: (lastPage, pages) => {
      return lastPage.length === 20 ? pages.length * 20 : undefined;
    },
    refetchInterval: 30000,
  });

  const posts = data?.pages.flat() || [];

  return (
    <div className="main-with-sidebar">
      <Sidebar />
      
      {/* Header */}
      <div className="sticky top-0 z-10 bg-white/90 backdrop-blur-md border-b border-slate-100">
        <div className="max-w-4xl mx-auto px-6 py-5">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
              <span className="text-blue-600">💓</span> PULSE Live Feed
            </h1>

            {/* Sort Tabs */}
            <div className="flex items-center gap-1 bg-slate-100/80 p-1 rounded-xl">
              <button
                onClick={() => setSortBy('importance')}
                className={`flex items-center px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                  sortBy === 'importance'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-slate-500 hover:text-slate-900'
                }`}
              >
                <TrendingUp className="w-4 h-4 mr-1.5" />
                Important
              </button>
              <button
                onClick={() => setSortBy('new')}
                className={`flex items-center px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                  sortBy === 'new'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-slate-500 hover:text-slate-900'
                }`}
              >
                <Clock className="w-4 h-4 mr-1.5" />
                New
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Feed */}
      <div className="max-w-4xl mx-auto px-6 py-8">
        <div className="space-y-4">
          {posts.map((post: any) => (
            <ArticleCard key={post.id} post={post} />
          ))}
          {isLoading && (
            <div className="py-12 flex justify-center">
               <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
            </div>
          )}
        </div>

        {/* Infinite Scroll Loader */}
        {hasNextPage && (
          <div className="py-12 flex justify-center">
            <button
              onClick={() => fetchNextPage()}
              disabled={isFetchingNextPage}
              className="flex items-center gap-2 px-8 py-3 bg-white hover:bg-slate-50 rounded-xl border border-slate-200 text-slate-700 font-bold transition-all shadow-sm"
            >
              {isFetchingNextPage ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
                  Loading more...
                </>
              ) : (
                'Load More Articles'
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
