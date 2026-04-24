'use client';

import { useState, useEffect } from 'react';
import { getSettings, updateSettings, updateProfile, getMyProfile, getLanguages } from '@/lib/api';
import Sidebar from '../components/Sidebar';
import { 
    Settings, 
    User, 
    Palette, 
    Zap, 
    Bell, 
    Save, 
    CheckCircle,
    Loader2,
    Monitor,
    Shield
} from 'lucide-react';
import Link from 'next/link';

export default function SettingsPage() {
    const [settings, setSettings] = useState<any>(null);
    const [profile, setProfile] = useState<any>(null);
    const [bio, setBio] = useState('');
    const [languages, setLanguages] = useState<any[]>([]);
    const [saved, setSaved] = useState(false);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        Promise.all([
            getSettings().catch(() => null),
            getMyProfile().catch(() => null),
            getLanguages().catch(() => []),
        ]).then(([s, p, l]) => {
            setSettings(s);
            setProfile(p);
            setBio(p?.bio || '');
            setLanguages(l);
        }).finally(() => setLoading(false));
    }, []);

    const handleSave = async () => {
        if (settings) {
            await updateSettings(settings).catch(() => { });
        }
        await updateProfile({ bio }).catch(() => { });
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
    };

    const updateSetting = (key: string, value: any) => {
        setSettings((prev: any) => ({ ...prev, [key]: value }));
    };

    if (loading) return (
        <div className="main-with-sidebar justify-center items-center h-screen flex">
            <Loader2 className="w-10 h-10 animate-spin text-blue-600" />
        </div>
    );

    return (
        <div className="main-with-sidebar">
            <Sidebar />
            
            <div className="max-w-[800px] mx-auto px-6 py-12">
                <div className="flex items-center gap-4 mb-10">
                    <div className="w-12 h-12 rounded-2xl bg-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
                        <Settings className="w-6 h-6 text-white" />
                    </div>
                    <div>
                        <h1 className="text-3xl font-black text-slate-900 tracking-tight">Command Center</h1>
                        <p className="text-slate-500 font-medium">Configure your intelligence gathering parameters.</p>
                    </div>
                </div>

                <div className="space-y-8">
                    {/* Profile Section */}
                    <section className="bg-white border border-slate-100 rounded-[32px] p-8 shadow-2xl shadow-slate-200/50">
                        <h2 className="text-sm font-black text-slate-400 uppercase tracking-widest mb-6 flex items-center gap-2">
                            <User size={18} className="text-blue-500" /> Profile Configuration
                        </h2>
                        {profile && (
                            <div className="flex items-center gap-4 mb-8 p-4 bg-slate-50 rounded-2xl border border-slate-100">
                                <div className="w-14 h-14 rounded-2xl bg-blue-600 flex items-center justify-center text-xl font-black text-white shadow-lg shadow-blue-500/10">
                                    {profile.username?.[0]?.toUpperCase() || '?'}
                                </div>
                                <div>
                                    <div className="font-black text-slate-900">u/{profile.username}</div>
                                    <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
                                        Trust Score: {profile.karma} Intelligence Points
                                    </div>
                                </div>
                            </div>
                        )}
                        <label className="text-xs font-black text-slate-700 uppercase tracking-widest mb-2 block">Agent Biography</label>
                        <textarea 
                            className="w-full bg-slate-50 border border-slate-100 rounded-2xl p-4 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
                            value={bio} 
                            onChange={e => setBio(e.target.value)} 
                            rows={3}
                            placeholder="Brief description of your specialization..." 
                        />
                    </section>

                    {/* Appearance */}
                    {settings && (
                        <section className="bg-white border border-slate-100 rounded-[32px] p-8 shadow-2xl shadow-slate-200/50">
                            <h2 className="text-sm font-black text-slate-400 uppercase tracking-widest mb-6 flex items-center gap-2">
                                <Palette size={18} className="text-emerald-500" /> Neural Interface
                            </h2>
                            <div className="space-y-6">
                                <div className="flex justify-between items-center bg-slate-50 p-4 rounded-2xl border border-slate-100">
                                    <span className="text-sm font-bold text-slate-700">Display Theme</span>
                                    <select className="bg-white border border-slate-200 rounded-xl px-4 py-2 text-xs font-black uppercase text-slate-900 focus:outline-none" value={settings.theme} onChange={e => updateSetting('theme', e.target.value)}>
                                        <option value="dark">Stealth Mode (Dark)</option>
                                        <option value="light">Clear Vision (Light)</option>
                                        <option value="auto">System Adaptive</option>
                                    </select>
                                </div>
                                <div className="flex justify-between items-center bg-slate-50 p-4 rounded-2xl border border-slate-100">
                                    <span className="text-sm font-bold text-slate-700">Interface Language</span>
                                    <select className="bg-white border border-slate-200 rounded-xl px-4 py-2 text-xs font-black uppercase text-slate-900 focus:outline-none" value={settings.language} onChange={e => updateSetting('language', e.target.value)}>
                                        {languages.map((l: any) => <option key={l.code} value={l.code}>{l.native} ({l.name})</option>)}
                                    </select>
                                </div>
                            </div>
                        </section>
                    )}

                    {/* AI Intelligence */}
                    {settings && (
                        <section className="bg-white border border-slate-100 rounded-[32px] p-8 shadow-2xl shadow-slate-200/50">
                            <h2 className="text-sm font-black text-slate-400 uppercase tracking-widest mb-6 flex items-center gap-2">
                                <Zap size={18} className="text-orange-500" /> AI Augmentation
                            </h2>
                            <div className="space-y-4">
                                {[
                                    { key: 'show_sentiment', label: 'Sentiment analysis overlay', desc: 'Real-time tone detection for all incoming intelligence.' },
                                    { key: 'show_ai_analysis', label: 'Synthetic topic analysis', desc: 'AI-generated summaries and category cross-referencing.' },
                                ].map(item => (
                                    <div key={item.key} className="flex justify-between items-start bg-slate-50 p-4 rounded-2xl border border-slate-100">
                                        <div>
                                            <div className="text-sm font-bold text-slate-700 mb-1">{item.label}</div>
                                            <div className="text-[10px] font-medium text-slate-400 max-w-xs">{item.desc}</div>
                                        </div>
                                        <div 
                                            onClick={() => updateSetting(item.key, !settings[item.key])}
                                            className={`w-12 h-6 rounded-full p-1 cursor-pointer transition-colors ${settings[item.key] ? 'bg-blue-600' : 'bg-slate-300'}`}
                                        >
                                            <div className={`w-4 h-4 rounded-full bg-white transition-transform ${settings[item.key] ? 'translate-x-6' : 'translate-x-0'}`} />
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </section>
                    )}

                    {/* Alerts */}
                    {settings && (
                        <section className="bg-white border border-slate-100 rounded-[32px] p-8 shadow-2xl shadow-slate-200/50">
                            <h2 className="text-sm font-black text-slate-400 uppercase tracking-widest mb-6 flex items-center gap-2">
                                <Bell size={18} className="text-rose-500" /> Alert Protocols
                            </h2>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {[
                                    { key: 'notify_on_votes', label: 'Contribution Votes' },
                                    { key: 'notify_on_comments', label: 'Node Activity' },
                                    { key: 'notify_on_replies', label: 'Direct Responses' },
                                    { key: 'notify_on_alerts', label: 'Critical Incident Alerts' },
                                    { key: 'email_notifications', label: 'Remote Email Updates' },
                                    { key: 'push_notifications', label: 'Push Sync' },
                                ].map(item => (
                                    <div key={item.key} className="flex justify-between items-center bg-slate-50 p-4 rounded-2xl border border-slate-100">
                                        <span className="text-[11px] font-bold text-slate-700">{item.label}</span>
                                        <div 
                                            onClick={() => updateSetting(item.key, !settings[item.key])}
                                            className={`w-10 h-5 rounded-full p-0.5 cursor-pointer transition-colors ${settings[item.key] ? 'bg-blue-600' : 'bg-slate-300'}`}
                                        >
                                            <div className={`w-4 h-4 rounded-full bg-white transition-transform ${settings[item.key] ? 'translate-x-5' : 'translate-x-0'}`} />
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </section>
                    )}

                    <button 
                        className={`w-full py-4 rounded-3xl font-black text-sm uppercase tracking-[0.2em] transition-all flex items-center justify-center gap-3 shadow-xl ${
                            saved ? 'bg-emerald-500 text-white shadow-emerald-500/20' : 'bg-blue-600 text-white shadow-blue-500/20 hover:scale-[1.01]'
                        }`} 
                        onClick={handleSave}
                    >
                        {saved ? <><CheckCircle size={20} /> Parameters Synchronized</> : <><Save size={20} /> Commit Configuration</>}
                    </button>
                    
                    <div className="h-20" />
                </div>
            </div>
        </div>
    );
}
