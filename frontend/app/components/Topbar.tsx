'use client';
import { useState, useEffect } from 'react';
import { usePathname } from 'next/navigation';
import { getNotificationCount } from '@/lib/api';

export default function Topbar() {
    const [notifCount, setNotifCount] = useState(0);
    const [user, setUser] = useState<string | null>(null);
    const [menuOpen, setMenuOpen] = useState(false);
    const [statesOpen, setStatesOpen] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const pathname = usePathname();

    useEffect(() => {
        // Check auth
        const token = localStorage.getItem('token');
        const username = localStorage.getItem('username');
        if (token && username) setUser(username);

        // Fetch notification count
        if (token) {
            getNotificationCount()
                .then((d: any) => setNotifCount(d.unread_count || 0))
                .catch(() => { });
        }
    }, []);

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        if (searchQuery.trim()) {
            window.location.href = `/?q=${encodeURIComponent(searchQuery.trim())}`;
        }
    };

    const handleLogout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('username');
        window.location.href = '/login';
    };

    const path = pathname || '';

    // State pages mapping
    const statePages = [
        { name: '🏛️ Tamil Nadu', path: '/tamil-nadu' },
        { name: '🌮 Telangana', path: '/telangana' },
        { name: '🏮 West Bengal', path: '/west-bengal' },
        { name: '🎭 Karnataka', path: '/karnataka' },
        { name: '🎪 Maharashtra', path: '/maharashtra' },
        { name: '🏛️ Delhi', path: '/delhi' },
        { name: '🌸 Gujarat', path: '/gujarat' },
    ];

    return (
        <header className="topbar">
            <div className="topbar-inner">
                {/* Logo */}
                <a href="/" className="topbar-logo" style={{backgroundImage: 'linear-gradient(135deg, #06B6D4 0%, #3B82F6 50%, #A855F7 100%)', backgroundClip: 'text', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', fontWeight: '800', fontSize: '1.3rem'}}>
                    🫀 PULSE
                </a>

                {/* Nav links */}
                <nav className="topbar-nav" role="navigation">
                    <a href="/"           className={`topbar-link ${path === '/' ? 'active' : ''}`}>🏠 Feed</a>
                    <a href="/india"      className={`topbar-link ${path === '/india' ? 'active' : ''}`}>🇮🇳 India</a>
                    
                    {/* States Dropdown */}
                    <div style={{ position: 'relative' }}>
                        <button
                            onClick={() => setStatesOpen(!statesOpen)}
                            className={`topbar-link ${['tamil-nadu', 'telangana', 'west-bengal', 'karnataka', 'maharashtra', 'delhi', 'gujarat'].some(s => path.includes(s)) ? 'active' : ''}`}
                            style={{ display: 'flex', alignItems: 'center', gap: 4, background: 'none', border: 'none', cursor: 'pointer', color: 'inherit' }}
                        >
                            📍 States <span style={{ fontSize: '0.7rem', marginLeft: 2 }}>▼</span>
                        </button>
                        {statesOpen && (
                            <div style={{
                                position: 'absolute', left: 0, top: '110%', zIndex: 200,
                                background: 'rgba(20, 30, 50, 0.95)', backdropFilter: 'blur(10px)',
                                border: '1px solid rgba(255,255,255,0.1)',
                                borderRadius: 10, minWidth: 200, padding: 8,
                                boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
                            }}>
                                {statePages.map(state => (
                                    <a
                                        key={state.path}
                                        href={state.path}
                                        style={{
                                            display: 'block', padding: '10px 12px', borderRadius: 6,
                                            fontSize: '0.88rem', color: 'inherit', textDecoration: 'none',
                                            transition: 'all 0.15s'
                                        }}
                                        onMouseEnter={e => (e.currentTarget.style.background = 'rgba(255,255,255,0.08)')}
                                        onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                                    >
                                        {state.name}
                                    </a>
                                ))}
                            </div>
                        )}
                    </div>

                    <a href="/world-news" className={`topbar-link ${path === '/world-news' ? 'active' : ''}`}>🌎 World</a>
                    <a href="/trending"   className={`topbar-link ${path === '/trending' ? 'active' : ''}`}>🔥 Trending</a>
                    <a href="/communities" className={`topbar-link ${path.startsWith('/communities') ? 'active' : ''}`}>🌍 Communities</a>
                    <a href="/dashboard"  className={`topbar-link ${path === '/dashboard' ? 'active' : ''}`}>📊 Dashboard</a>
                </nav>

                {/* Search */}
                <form onSubmit={handleSearch} style={{ flex: 1, maxWidth: 280, margin: '0 12px' }}>
                    <input
                        type="search"
                        className="input"
                        placeholder="Search news..."
                        value={searchQuery}
                        onChange={e => setSearchQuery(e.target.value)}
                        style={{ height: 34, fontSize: '0.85rem', padding: '0 12px' }}
                    />
                </form>

                {/* Actions */}
                <div className="topbar-actions">
                    {user ? (
                        <>
                            <a href="/notifications" className="btn btn-ghost btn-sm" style={{ position: 'relative' }}>
                                🔔
                                {notifCount > 0 && (
                                    <span style={{
                                        position: 'absolute', top: -4, right: -4,
                                        background: 'var(--accent)', color: 'white',
                                        borderRadius: '50%', width: 16, height: 16,
                                        fontSize: '0.65rem', fontWeight: 800,
                                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                                    }}>
                                        {notifCount > 9 ? '9+' : notifCount}
                                    </span>
                                )}
                            </a>
                            <div style={{ position: 'relative' }}>
                                <button
                                    onClick={() => setMenuOpen(!menuOpen)}
                                    className="btn btn-ghost btn-sm"
                                    style={{ display: 'flex', alignItems: 'center', gap: 6 }}
                                >
                                    <span style={{
                                        width: 26, height: 26, borderRadius: '50%',
                                        background: 'linear-gradient(135deg, var(--accent), var(--accent-secondary))',
                                        display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                                        fontSize: '0.75rem', fontWeight: 800, color: 'white',
                                    }}>
                                        {user[0].toUpperCase()}
                                    </span>
                                    <span style={{ fontSize: '0.82rem' }}>u/{user}</span>
                                </button>
                                {menuOpen && (
                                    <div style={{
                                        position: 'absolute', right: 0, top: '110%', zIndex: 200,
                                        background: 'var(--bg-card)', border: '1px solid var(--border)',
                                        borderRadius: 10, minWidth: 180, padding: 8,
                                        boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
                                    }}>
                                        <a href={`/users/${user}`} style={{ display: 'block', padding: '8px 12px', borderRadius: 6, fontSize: '0.88rem', color: 'var(--text-primary)', textDecoration: 'none' }}
                                            onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-secondary)')}
                                            onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}>
                                            👤 My Profile
                                        </a>
                                        <a href="/bookmarks" style={{ display: 'block', padding: '8px 12px', borderRadius: 6, fontSize: '0.88rem', color: 'var(--text-primary)', textDecoration: 'none' }}
                                            onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-secondary)')}
                                            onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}>
                                            🔖 Bookmarks
                                        </a>
                                        <a href="/settings" style={{ display: 'block', padding: '8px 12px', borderRadius: 6, fontSize: '0.88rem', color: 'var(--text-primary)', textDecoration: 'none' }}
                                            onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-secondary)')}
                                            onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}>
                                            ⚙️ Settings
                                        </a>
                                        <hr style={{ border: 'none', borderTop: '1px solid var(--border)', margin: '4px 0' }} />
                                        <button onClick={handleLogout} style={{
                                            display: 'block', width: '100%', textAlign: 'left',
                                            padding: '8px 12px', borderRadius: 6, fontSize: '0.88rem',
                                            color: 'var(--danger)', background: 'none', border: 'none', cursor: 'pointer',
                                        }}
                                            onMouseEnter={e => (e.currentTarget.style.background = 'rgba(255,71,87,0.1)')}
                                            onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}>
                                            🚪 Logout
                                        </button>
                                    </div>
                                )}
                            </div>
                        </>
                    ) : (
                        <>
                            <a href="/login"    className="btn btn-outline btn-sm">Log in</a>
                            <a href="/register" className="btn btn-primary btn-sm">Sign up</a>
                        </>
                    )}
                </div>
            </div>
        </header>
    );
}
