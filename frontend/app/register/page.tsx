'use client';

import { useState } from 'react';
import { register } from '@/lib/api';
import { UserPlus, User, Mail, KeyRound, Loader2, ArrowRight, Phone } from 'lucide-react';
import Link from 'next/link';

export default function RegisterPage() {
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [phoneNumber, setPhoneNumber] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        try {
            await register({ 
                username, 
                email, 
                password, 
                phone_number: phoneNumber 
            });
            const { login: loginFn } = await import('@/lib/api');
            const data = await loginFn({ username, password });
            if (data.access_token) {
                localStorage.setItem('token', data.access_token);
                localStorage.setItem('username', username);
                window.location.href = '/';
            }
        } catch (err: any) {
            setError(err.message || 'Registration failed. Use a unique username.');
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
                        <UserPlus className="w-8 h-8 text-white" />
                    </div>
                    <h1 className="text-3xl font-black text-slate-900 tracking-tight">Create Identity</h1>
                    <p className="text-slate-500 font-medium mt-2">Join the next-gen news intelligence node.</p>
                </div>

                {/* Register Card */}
                <div className="bg-white border border-slate-200 rounded-[32px] p-10 shadow-2xl shadow-slate-200/50">
                    <form onSubmit={handleSubmit} className="space-y-5">
                        <div>
                            <label className="text-xs font-black text-slate-400 uppercase tracking-widest ml-1 mb-2 block">Username</label>
                            <div className="relative">
                                <User className="absolute left-4 top-3.5 w-5 h-5 text-slate-400" />
                                <input 
                                    className="w-full bg-slate-50 border-none rounded-2xl py-3.5 pl-12 pr-4 text-slate-900 placeholder-slate-400 focus:ring-2 focus:ring-blue-500/20 transition-all font-medium" 
                                    type="text" 
                                    value={username} 
                                    onChange={e => setUsername(e.target.value)} 
                                    placeholder="your_handle" 
                                    required 
                                />
                            </div>
                        </div>

                        <div>
                            <label className="text-xs font-black text-slate-400 uppercase tracking-widest ml-1 mb-2 block">Email Address</label>
                            <div className="relative">
                                <Mail className="absolute left-4 top-3.5 w-5 h-5 text-slate-400" />
                                <input 
                                    className="w-full bg-slate-50 border-none rounded-2xl py-3.5 pl-12 pr-4 text-slate-900 placeholder-slate-400 focus:ring-2 focus:ring-blue-500/20 transition-all font-medium" 
                                    type="email" 
                                    value={email} 
                                    onChange={e => setEmail(e.target.value)} 
                                    placeholder="agent@pulse.io" 
                                    required 
                                />
                            </div>
                        </div>

                        <div>
                            <label className="text-xs font-black text-slate-400 uppercase tracking-widest ml-1 mb-2 block">Access Password</label>
                            <div className="relative">
                                <KeyRound className="absolute left-4 top-3.5 w-5 h-5 text-slate-400" />
                                <input 
                                    className="w-full bg-slate-50 border-none rounded-2xl py-3.5 pl-12 pr-4 text-slate-900 placeholder-slate-400 focus:ring-2 focus:ring-blue-500/20 transition-all font-medium" 
                                    type="password" 
                                    value={password} 
                                    onChange={e => setPassword(e.target.value)} 
                                    placeholder="Min. 6 characters" 
                                    required 
                                    minLength={6}
                                />
                            </div>
                        </div>

                        <div>
                            <label className="text-xs font-black text-slate-400 uppercase tracking-widest ml-1 mb-2 block">Phone Number (for WhatsApp)</label>
                            <div className="relative">
                                <Phone className="absolute left-4 top-3.5 w-5 h-5 text-slate-400" />
                                <input 
                                    className="w-full bg-slate-50 border-none rounded-2xl py-3.5 pl-12 pr-4 text-slate-900 placeholder-slate-400 focus:ring-2 focus:ring-blue-500/20 transition-all font-medium" 
                                    type="tel" 
                                    value={phoneNumber} 
                                    onChange={e => setPhoneNumber(e.target.value)} 
                                    placeholder="+1234567890" 
                                />
                            </div>
                        </div>

                        {error && (
                            <div className="bg-rose-50 border border-rose-100 p-4 rounded-2xl text-rose-600 text-xs font-bold">
                                ⚠️ {error}
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
                                    INITIALIZE ACCOUNT
                                    <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                                </>
                            )}
                        </button>
                    </form>
                </div>

                <p className="text-center mt-8 text-slate-500 font-medium text-sm">
                    Already a member? <Link href="/login" className="text-blue-600 font-bold hover:underline">Sign in instead</Link>
                </p>
            </div>
        </div>
    );
}
