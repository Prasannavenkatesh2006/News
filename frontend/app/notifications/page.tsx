'use client';

import { useState, useEffect } from 'react';
import { getNotifications, markNotificationRead, markAllNotificationsRead } from '@/lib/api';
import Sidebar from '../components/Sidebar';
import { 
    Bell, 
    CheckCheck, 
    MessageSquare, 
    AtSign, 
    AlertCircle, 
    Settings, 
    ThumbsUp,
    Loader2
} from 'lucide-react';
import Link from 'next/link';

export default function NotificationsPage() {
    const [notifs, setNotifs] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        getNotifications(50).then(setNotifs).catch(() => { }).finally(() => setLoading(false));
    }, []);

    const handleRead = async (id: string) => {
        await markNotificationRead(id).catch(() => { });
        setNotifs(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
    };

    const handleReadAll = async () => {
        await markAllNotificationsRead().catch(() => { });
        setNotifs(prev => prev.map(n => ({ ...n, is_read: true })));
    };

    const icons: Record<string, React.ReactNode> = {
        vote: <ThumbsUp size={18} className="text-blue-500" />,
        comment: <MessageSquare size={18} className="text-emerald-500" />,
        reply: <MessageSquare size={18} className="text-purple-500" />,
        mention: <AtSign size={18} className="text-orange-500" />,
        alert: <AlertCircle size={18} className="text-rose-500" />,
        system: <Settings size={18} className="text-slate-500" />,
    };

    return (
        <div className="main-with-sidebar">
            <Sidebar />
            
            <div className="max-w-[800px] mx-auto px-6 py-12">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-10">
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-2xl bg-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
                            <Bell className="w-6 h-6 text-white" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-black text-slate-900 tracking-tight">Intelligence Alerts</h1>
                            <p className="text-slate-500 font-medium">Real-time updates on your contributions.</p>
                        </div>
                    </div>
                    <button 
                        onClick={handleReadAll}
                        className="flex items-center gap-2 px-6 py-3 rounded-2xl bg-white border border-slate-200 text-slate-900 font-black text-xs uppercase tracking-widest hover:bg-slate-50 transition-all shadow-sm"
                    >
                        <CheckCheck size={16} /> Mark all as read
                    </button>
                </div>

                {loading ? (
                    <div className="flex items-center justify-center py-20">
                        <Loader2 className="w-10 h-10 animate-spin text-blue-600" />
                    </div>
                ) : notifs.length === 0 ? (
                    <div className="py-24 text-center bg-white border border-slate-100 rounded-[40px] shadow-2xl shadow-slate-200/50">
                        <div className="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-6 text-slate-300">
                            <Bell size={40} />
                        </div>
                        <h2 className="text-xl font-black text-slate-900 mb-2">Clear Frequency</h2>
                        <p className="text-slate-500 font-medium">No new intelligence alerts for your profile.</p>
                    </div>
                ) : (
                    <div className="bg-white border border-slate-100 rounded-[40px] shadow-2xl shadow-slate-200/50 overflow-hidden divide-y divide-slate-50">
                        {notifs.map(n => (
                            <div 
                                key={n.id} 
                                onClick={() => handleRead(n.id)} 
                                className={`group p-8 flex items-start gap-6 cursor-pointer transition-all ${n.is_read ? 'opacity-70 grayscale-[0.5]' : 'bg-blue-50/10'}`}
                            >
                                <div className={`p-4 rounded-2xl border transition-all ${
                                    n.is_read ? 'bg-slate-50 border-slate-100' : 'bg-white border-blue-100 shadow-lg shadow-blue-500/5 group-hover:scale-110'
                                }`}>
                                    {icons[n.type] || <Bell size={18} className="text-slate-400" />}
                                </div>
                                <div className="flex-1">
                                    <div className="flex items-center justify-between gap-4 mb-1">
                                        <h3 className={`text-sm tracking-tight ${n.is_read ? 'font-bold text-slate-600' : 'font-black text-slate-900'}`}>
                                            {n.title}
                                        </h3>
                                        <span className="text-[10px] font-bold text-slate-400 uppercase">
                                            {new Date(n.created_at).toLocaleDateString()}
                                        </span>
                                    </div>
                                    {n.message && <p className="text-sm text-slate-500 font-medium leading-relaxed">{n.message}</p>}
                                    <div className="mt-3 flex items-center gap-2">
                                        {n.actor_username && (
                                            <span className="text-[10px] font-black text-blue-600 uppercase tracking-widest bg-blue-50 px-2 py-0.5 rounded-md">
                                                From @{n.actor_username}
                                            </span>
                                        )}
                                    </div>
                                </div>
                                {!n.is_read && (
                                    <div className="w-2.5 h-2.5 rounded-full bg-blue-600 mt-2 shrink-0 animate-pulse shadow-lg shadow-blue-500/50" />
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
