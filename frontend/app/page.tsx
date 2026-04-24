'use client';

import Link from 'next/link';
import { ArrowRight, Zap, Users, TrendingUp, Shield } from 'lucide-react';
import Sidebar from './components/Sidebar';
import { motion } from 'framer-motion';

export default function Home() {
  return (
    <div className="main-with-sidebar">
      <Sidebar />
      
      <main className="content-container !max-w-none !p-0">
        {/* Hero Section */}
        <section className="relative px-4 py-16 md:py-32 bg-gradient-to-b from-white via-slate-50 to-white overflow-hidden border-b border-slate-100">
          
          {/* Animated background gradient */}
          <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 via-indigo-500/5 to-purple-500/5 animate-pulse opacity-50 pointer-events-none" />
          
          <div className="max-w-6xl mx-auto relative z-10">
            {/* Main Headline */}
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8 }}
              className="text-center mb-12"
            >
              <div className="flex items-center justify-center mb-6">
                <span className="text-5xl md:text-7xl font-black bg-clip-text text-transparent bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600">
                  🫀 PULSE
                </span>
              </div>
              
              <h1 className="text-3xl md:text-5xl font-bold text-slate-900 mb-4 leading-tight">
                The Heartbeat of <br /> Global Intelligence
              </h1>
              
              <p className="text-lg md:text-xl text-slate-600 max-w-3xl mx-auto mb-8 leading-relaxed">
                PULSE is a next-generation AI-driven social intelligence platform that transforms global news 
                into real-time, interactive, community-driven insights. Combines multi-source data ingestion, 
                machine learning, and social engagement to detect and surface important events as they happen.
              </p>

              {/* CTA Buttons */}
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link 
                  href="/feed"
                  className="group inline-flex items-center gap-3 px-8 py-4 bg-blue-600 rounded-xl font-bold text-white hover:bg-blue-700 hover:shadow-lg hover:shadow-blue-500/20 transition-all font-sans"
                >
                  Explore Live Feed
                  <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </Link>
                
                <Link 
                  href="/communities"
                  className="inline-flex items-center gap-3 px-8 py-4 bg-white border border-slate-200 rounded-xl font-bold text-slate-700 hover:border-blue-500/50 transition-all font-sans"
                >
                  Join Communities
                </Link>
              </div>
            </motion.div>
          </div>
        </section>

        {/* Features Section */}
        <section className="py-20 px-4 max-w-6xl mx-auto">
          <motion.h2 
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            transition={{ duration: 0.6 }}
            className="text-3xl md:text-4xl font-bold text-slate-900 text-center mb-16"
          >
            Why PULSE?
          </motion.h2>

          <div className="grid md:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="p-8 bg-white border border-slate-100 rounded-2xl shadow-sm hover:shadow-md hover:border-blue-200 transition-all"
            >
              <div className="w-12 h-12 bg-blue-50 rounded-xl flex items-center justify-center mb-6">
                <Zap className="w-6 h-6 text-blue-600" />
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-3">Real-Time Intelligence</h3>
              <p className="text-slate-600">
                12+ autonomous scrapers continuously monitor 100+ news sources worldwide, posting updates every minute.
              </p>
            </motion.div>

            {/* Feature 2 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
              className="p-8 bg-white border border-slate-100 rounded-2xl shadow-sm hover:shadow-md hover:border-blue-200 transition-all"
            >
              <div className="w-12 h-12 bg-indigo-50 rounded-xl flex items-center justify-center mb-6">
                <TrendingUp className="w-6 h-6 text-indigo-600" />
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-3">AI-Powered Ranking</h3>
              <p className="text-slate-600">
                Machine learning algorithms automatically detect breaking news, trending topics, and importance scores.
              </p>
            </motion.div>

            {/* Feature 3 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="p-8 bg-white border border-slate-100 rounded-2xl shadow-sm hover:shadow-md hover:border-blue-200 transition-all"
            >
              <div className="w-12 h-12 bg-purple-50 rounded-xl flex items-center justify-center mb-6">
                <Users className="w-6 h-6 text-purple-600" />
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-3">Community Driven</h3>
              <p className="text-slate-600">
                Discuss, vote, and share insights with like-minded communities. Shape the conversation in real-time.
              </p>
            </motion.div>
          </div>
        </section>

        {/* Stats Section */}
        <section className="py-20 px-4 bg-slate-50 border-y border-slate-100">
          <div className="max-w-6xl mx-auto">
            <div className="grid md:grid-cols-4 gap-8 text-center">
              <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} transition={{ duration: 0.6 }}>
                <div className="text-3xl md:text-4xl font-bold text-blue-600 mb-2">12+</div>
                <p className="text-slate-500 font-medium">Active Scrapers</p>
              </motion.div>

              <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} transition={{ duration: 0.6, delay: 0.1 }}>
                <div className="text-3xl md:text-4xl font-bold text-indigo-600 mb-2">100+</div>
                <p className="text-slate-500 font-medium">News Sources</p>
              </motion.div>

              <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} transition={{ duration: 0.6, delay: 0.2 }}>
                <div className="text-3xl md:text-4xl font-bold text-purple-600 mb-2">Real-Time</div>
                <p className="text-slate-500 font-medium">Updates</p>
              </motion.div>

              <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} transition={{ duration: 0.6, delay: 0.3 }}>
                <div className="text-3xl md:text-4xl font-bold text-pink-600 mb-2">AI-Powered</div>
                <p className="text-slate-500 font-medium">Ranking</p>
              </motion.div>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-24 px-4 bg-white">
          <div className="max-w-4xl mx-auto text-center">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              <h2 className="text-3xl md:text-5xl font-bold text-slate-900 mb-6">
                Ready to Stay Ahead of the News?
              </h2>
              <p className="text-lg text-slate-600 mb-10 max-w-2xl mx-auto">
                Join thousands of users discovering breaking news and emerging trends before anyone else.
              </p>
              
              <Link 
                href="/feed"
                className="group inline-flex items-center gap-3 px-10 py-5 bg-blue-600 rounded-2xl font-bold text-white hover:bg-blue-700 hover:shadow-xl hover:shadow-blue-500/20 transition-all text-lg"
              >
                Start Exploring
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </Link>
            </motion.div>
          </div>
        </section>

        {/* Footer */}
        <footer className="border-t border-slate-100 bg-white py-12 px-4">
          <div className="max-w-6xl mx-auto text-center">
            <p className="text-slate-400 font-medium">
              © 2024 PULSE — The Heartbeat of Global Information. Powered by AI.
            </p>
          </div>
        </footer>
      </main>
    </div>
  );
}
