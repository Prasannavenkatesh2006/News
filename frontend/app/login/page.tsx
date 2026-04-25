'use client';

import { useState } from 'react';
import { login } from '@/lib/api';
import { KeyRound, User, Loader2, ArrowRight } from 'lucide-react';
import Link from 'next/link';

export default function LoginPage() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        try {
            const data = await login({ username, password });
            if (data.access_token) {
                localStorage.setItem('token', data.access_token);
                localStorage.setItem('username', username);
                window.location.href = '/';
            } else {
                setError(data.detail || 'The credentials you entered are incorrect.');
            }
        } catch (err: any) {
            setError(err.message || 'Connecting to auth servers failed.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-6">
            <div className="w-full max-w-[440px]">
                {/* Logo Area */}
                <div className="text-center mb-10">
                    <div className="w-16 h-16 bg-blue-600 rounded-3xl flex items-center justify-center mx-auto mb-6 shadow-xl shadow-blue-500/20">
                        <KeyRound className="w-8 h-8 text-white" />
                    </div>
                    <h1 className="text-3xl font-black text-slate-900 tracking-tight">Access Pulse</h1>
                    <p className="text-slate-500 font-medium mt-2">Intelligence platform for verified news.</p>
                </div>

                {/* Login Card */}
                <div className="bg-white border border-slate-200 rounded-[32px] p-10 shadow-2xl shadow-slate-200/50">
                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div>
                            <label className="text-xs font-black text-slate-400 uppercase tracking-widest ml-1 mb-2 block">Username</label>
                            <div className="relative">
                                <User className="absolute left-4 top-3.5 w-5 h-5 text-slate-400" />
                                <input 
                                    className="w-full bg-slate-50 border-none rounded-2xl py-3.5 pl-12 pr-4 text-slate-900 placeholder-slate-400 focus:ring-2 focus:ring-blue-500/20 transition-all font-medium" 
                                    type="text" 
                                    value={username} 
                                    onChange={e => setUsername(e.target.value)} 
                                    placeholder="Enter your username" 
                                    required 
                                />
                            </div>
                        </div>

                        <div>
                            <label className="text-xs font-black text-slate-400 uppercase tracking-widest ml-1 mb-2 block">Password</label>
                            <div className="relative">
                                <KeyRound className="absolute left-4 top-3.5 w-5 h-5 text-slate-400" />
                                <input 
                                    className="w-full bg-slate-50 border-none rounded-2xl py-3.5 pl-12 pr-4 text-slate-900 placeholder-slate-400 focus:ring-2 focus:ring-blue-500/20 transition-all font-medium" 
                                    type="password" 
                                    value={password} 
                                    onChange={e => setPassword(e.target.value)} 
                                    placeholder="••••••••" 
                                    required 
                                />
                            </div>
                        </div>

                        {error && (
                            <div className="bg-rose-50 border border-rose-100 p-4 rounded-2xl text-rose-600 text-xs font-bold flex items-center gap-2">
                                <span>⚠️ {error}</span>
                            </div>
                        )}

                        <button 
                            className="w-full bg-blue-600 text-white font-black py-4 rounded-2xl hover:bg-blue-700 transition-all shadow-xl shadow-blue-500/20 flex items-center justify-center gap-2 group disabled:opacity-50" 
                            disabled={loading}
                        >
                            {loading ? (
                                <Loader2 className="w-5 h-5 animate-spin" />
                            ) : (
                                <>
                                    LOG IN TO DASHBOARD
                                    <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                                </>
                            )}
                        </button>
                    </form>
                </div>

                <p className="text-center mt-8 text-slate-500 font-medium text-sm">
                    Unauthorized access? <Link href="/register" className="text-blue-600 font-bold hover:underline">Apply for credentials</Link>
                </p>
            </div>
        </div>
    );
}
