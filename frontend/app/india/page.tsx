'use client';

import { ArticleCard } from '@/components/ArticleCard';
import { useQuery } from '@tanstack/react-query';
import { MapPin, Loader2 } from 'lucide-react';
import { useState } from 'react';
import Sidebar from '../components/Sidebar';

const INDIAN_STATES = [
  'All India',
  'Tamil Nadu',
  'Karnataka',
  'Maharashtra',
  'Delhi',
  'Gujarat',
  'West Bengal',
  'Telangana'
];

export default function IndiaPage() {
  const [selectedState, setSelectedState] = useState('All India');

  const { data: posts, isLoading } = useQuery({
    queryKey: ['india-news', selectedState],
    queryFn: async () => {
      const stateParam = selectedState === 'All India' ? '' : `&state=${encodeURIComponent(selectedState)}`;
      const res = await fetch(`/api/v1/social/feed?country=India${stateParam}&limit=100`);
      if (!res.ok) throw new Error('Network response was not ok');
      return res.json();
    },
    refetchInterval: 30000
  });

  const stats = {
    total: posts?.length || 0,
    topics: new Set(posts?.map((p: any) => p.topic)).size || 0,
    positive: posts?.filter((p: any) => p.sentiment === 'positive').length || 0
  };

  return (
    <div className="main-with-sidebar">
      <Sidebar />
      
      {/* Hero Header */}
      <div className="bg-white border-b border-slate-100">
        <div className="max-w-6xl mx-auto px-6 py-12">
          <div className="flex items-center gap-4 mb-5">
            <span className="text-6xl drop-shadow-sm">🇮🇳</span>
            <div>
              <h1 className="text-4xl font-black text-slate-900 tracking-tight">
                India News Hub
              </h1>
              <p className="text-lg text-slate-500 font-medium mt-1">
                Real-time national and state-level intelligence
              </p>
            </div>
          </div>

          {/* Stats Bar */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
            <div className="bg-orange-50/50 rounded-2xl p-6 border border-orange-100">
              <div className="text-3xl font-black text-orange-600 mb-1">
                {stats.total}
              </div>
              <div className="text-xs text-orange-400 font-bold uppercase tracking-widest">Articles Found</div>
            </div>
            <div className="bg-blue-50/50 rounded-2xl p-6 border border-blue-100">
              <div className="text-3xl font-black text-blue-600 mb-1">
                {stats.topics}
              </div>
              <div className="text-xs text-blue-400 font-bold uppercase tracking-widest">Active Topics</div>
            </div>
            <div className="bg-emerald-50/50 rounded-2xl p-6 border border-emerald-100">
              <div className="text-3xl font-black text-emerald-600 mb-1">
                {stats.positive}
              </div>
              <div className="text-xs text-emerald-400 font-bold uppercase tracking-widest">Positive Sentiments</div>
            </div>
          </div>
        </div>
      </div>

      {/* State Filters */}
      <div className="sticky top-0 z-10 bg-white/90 backdrop-blur-md border-b border-slate-100">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex items-center gap-3 overflow-x-auto pb-1 scrollbar-none">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center">
              <MapPin className="w-4 h-4 text-slate-500" />
            </div>
            {INDIAN_STATES.map((state) => (
              <button
                key={state}
                onClick={() => setSelectedState(state)}
                className={`px-5 py-2 rounded-xl text-sm font-bold whitespace-nowrap transition-all border ${
                  selectedState === state
                    ? 'bg-blue-600 text-white border-blue-600 shadow-md shadow-blue-500/20'
                    : 'bg-white text-slate-500 border-slate-200 hover:border-blue-400 hover:text-blue-600'
                }`}
              >
                {state}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Articles */}
      <div className="max-w-4xl mx-auto px-6 py-10">
        <div className="space-y-6">
          {isLoading ? (
            <div className="py-20 flex justify-center">
              <Loader2 className="w-10 h-10 animate-spin text-blue-600" />
            </div>
          ) : posts?.length === 0 ? (
            <div className="text-center py-20 bg-slate-50 rounded-3xl border-2 border-dashed border-slate-200">
              <div className="text-4xl mb-4">🔍</div>
              <h3 className="text-lg font-bold text-slate-900">No articles found</h3>
              <p className="text-slate-500">There are no recent updates for {selectedState} at the moment.</p>
            </div>
          ) : (
            posts?.map((post: any) => (
              <ArticleCard key={post.id} post={post} />
            ))
          )}
        </div>
      </div>
    </div>
  );
}
