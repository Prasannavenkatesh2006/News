'use client';
import { useState, useEffect } from 'react';
import { getAlerts, getAlertStats, connectAlertsWS } from '@/lib/api';

function severityColor(s: string) {
    return s === 'critical' ? 'var(--danger)' : s === 'high' ? '#e67e22' : s === 'medium' ? '#f39c12' : 'var(--text-muted)';
}

function alertIcon(type: string) {
    const icons: Record<string, string> = {
        earthquake: '🌍', flood: '🌊', hurricane: '🌀', wildfire: '🔥', tsunami: '🌊',
        tornado: '🌪️', volcanic_eruption: '🌋', drought: '☀️', landslide: '⛰️', pandemic: '🦠'
    };
    return icons[type] || '⚠️';
}

export default function AlertsPage() {
    const [alerts, setAlerts] = useState<any[]>([]);
    const [stats, setStats] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<string>('all');

    useEffect(() => {
        Promise.all([
            getAlerts(true).catch(() => []),
            getAlertStats().catch(() => null),
        ]).then(([a, s]) => {
            setAlerts(a);
            setStats(s);
        }).finally(() => setLoading(false));

        const ws = connectAlertsWS(data => {
            if (data.type === 'disaster_alert') {
                setAlerts(prev => [data.data, ...prev]);
            }
        });
        return () => { ws?.close(); };
    }, []);

    const filtered = filter === 'all' ? alerts : alerts.filter(a => a.severity === filter);

    return (
        <>
            <nav className="navbar"><div className="navbar-inner"><a href="/" className="logo">⚡ ANIP Social</a><a href="/" className="btn btn-outline btn-sm">← Home</a></div></nav>
            <div style={{ maxWidth: 800, margin: '24px auto', padding: '0 20px' }}>
                <h1 style={{ fontSize: '1.4rem', fontWeight: 800, marginBottom: 8 }}>🚨 Disaster Alert Center</h1>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: 24 }}>
                    Real-time monitoring of natural disasters and emergencies worldwide. Alerts are generated from ANIP's AI-powered article analysis.
                </p>

                {/* Stats Bar */}
                {stats && (
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 24 }}>
                        {[
                            { label: 'Critical', count: stats.active_critical, color: 'var(--danger)', icon: '🔴' },
                            { label: 'High', count: stats.active_high, color: '#e67e22', icon: '🟠' },
                            { label: 'Medium', count: stats.active_medium, color: '#f39c12', icon: '🟡' },
                            { label: 'Resolved', count: stats.total_resolved, color: 'var(--sentiment-positive)', icon: '✅' },
                        ].map(s => (
                            <div key={s.label} className="card" style={{ textAlign: 'center', padding: 16 }}>
                                <div style={{ fontSize: '1.5rem' }}>{s.icon}</div>
                                <div style={{ fontSize: '1.4rem', fontWeight: 800, color: s.color }}>{s.count}</div>
                                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{s.label}</div>
                            </div>
                        ))}
                    </div>
                )}

                {/* Filter */}
                <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
                    {['all', 'critical', 'high', 'medium'].map(f => (
                        <button key={f} className={`btn btn-sm ${filter === f ? 'btn-primary' : 'btn-outline'}`}
                            onClick={() => setFilter(f)}>{f === 'all' ? '📊 All' : f.charAt(0).toUpperCase() + f.slice(1)}</button>
                    ))}
                </div>

                {/* Alert List */}
                {loading ? (
                    <div className="card" style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>Scanning global feeds...</div>
                ) : filtered.length === 0 ? (
                    <div className="card" style={{ textAlign: 'center', padding: 40 }}>
                        <div style={{ fontSize: '2.5rem', marginBottom: 12 }}>🌍</div>
                        <div style={{ fontWeight: 700, marginBottom: 4 }}>No active alerts</div>
                        <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>The AI monitoring system hasn't detected any active disasters</div>
                    </div>
                ) : (
                    filtered.map(alert => (
                        <div key={alert.id} className="card animate-in" style={{
                            marginBottom: 12, borderLeft: `4px solid ${severityColor(alert.severity)}`,
                        }}>
                            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
                                <span style={{ fontSize: '2rem' }}>{alertIcon(alert.alert_type)}</span>
                                <div style={{ flex: 1 }}>
                                    <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 4 }}>
                                        <span style={{
                                            padding: '2px 8px', borderRadius: 4, fontSize: '0.7rem', fontWeight: 700,
                                            color: 'white', background: severityColor(alert.severity), textTransform: 'uppercase',
                                        }}>{alert.severity}</span>
                                        <span className="badge badge-community">{alert.alert_type.replace('_', ' ')}</span>
                                        <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                                            {new Date(alert.created_at).toLocaleString()}
                                        </span>
                                    </div>
                                    <h3 style={{ fontSize: '1rem', fontWeight: 700, lineHeight: 1.4 }}>{alert.title}</h3>
                                    {alert.description && (
                                        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: 4, lineHeight: 1.5 }}>
                                            {alert.description?.substring(0, 300)}
                                        </p>
                                    )}
                                    <div style={{ display: 'flex', gap: 16, marginTop: 8, fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                                        {alert.location && <span>📍 {alert.location}</span>}
                                        <span>📰 {alert.source_count} source{alert.source_count > 1 ? 's' : ''}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </>
    );
}
