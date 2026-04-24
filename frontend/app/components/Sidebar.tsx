'use client';
import { useState, useEffect } from 'react';
import { usePathname } from 'next/navigation';
import { getNotificationCount } from '@/lib/api';
import { 
    Home, 
    Globe, 
    TrendingUp, 
    Users, 
    LayoutDashboard, 
    MapPin, 
    Bell, 
    Bookmark, 
    Settings, 
    LogOut,
    Search,
    ChevronDown,
    ChevronUp
} from 'lucide-react';
import Link from 'next/link';

export default function Sidebar() {
    const [notifCount, setNotifCount] = useState(0);
    const [user, setUser] = useState<string | null>(null);
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

    const statePages = [
        { name: 'Tamil Nadu', path: '/tamil-nadu' },
        { name: 'Telangana', path: '/telangana' },
        { name: 'West Bengal', path: '/west-bengal' },
        { name: 'Karnataka', path: '/karnataka' },
        { name: 'Maharashtra', path: '/maharashtra' },
        { name: 'Delhi', path: '/delhi' },
        { name: 'Gujarat', path: '/gujarat' },
    ];

    const navItems = [
        { name: 'Feed', path: '/', icon: <Home size={20} /> },
        { name: 'India', path: '/india', icon: <Globe size={20} /> },
        { name: 'World News', path: '/world-news', icon: <Globe size={20} /> },
        { name: 'Trending', path: '/trending', icon: <TrendingUp size={20} /> },
        { name: 'Communities', path: '/communities', icon: <Users size={20} /> },
        { name: 'Dashboard', path: '/dashboard', icon: <LayoutDashboard size={20} /> },
    ];

    return (
        <aside className="sidebar">
            <div className="sidebar-logo">
                <Link href="/" className="bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600 font-extrabold">
                    🫀 PULSE
                </Link>
            </div>

            <form onSubmit={handleSearch} className="search-container">
                <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
                    <input
                        type="search"
                        className="search-input pl-10"
                        placeholder="Search news..."
                        value={searchQuery}
                        onChange={e => setSearchQuery(e.target.value)}
                    />
                </div>
            </form>

            <nav className="sidebar-nav">
                {navItems.map((item) => (
                    <Link
                        key={item.path}
                        href={item.path}
                        className={`sidebar-link ${path === item.path ? 'active' : ''}`}
                    >
                        {item.icon}
                        <span>{item.name}</span>
                    </Link>
                ))}

                {/* States Dropdown */}
                <div className="mt-2">
                    <button
                        onClick={() => setStatesOpen(!statesOpen)}
                        className={`sidebar-link w-full justify-between ${['tamil-nadu', 'telangana', 'west-bengal', 'karnataka', 'maharashtra', 'delhi', 'gujarat'].some(s => path.includes(s)) ? 'active' : ''}`}
                    >
                        <div className="flex items-center gap-3">
                            <MapPin size={20} />
                            <span>States</span>
                        </div>
                        {statesOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </button>
                    {statesOpen && (
                        <div className="ml-9 mt-1 flex flex-col gap-1">
                            {statePages.map(state => (
                                <Link
                                    key={state.path}
                                    href={state.path}
                                    className={`sidebar-link !py-1.5 !text-[0.88rem] ${path === state.path ? 'active' : ''}`}
                                >
                                    {state.name}
                                </Link>
                            ))}
                        </div>
                    )}
                </div>
            </nav>

            <div className="sidebar-footer">
                {user ? (
                    <div className="flex flex-col gap-1">
                        <Link href="/notifications" className={`sidebar-link !px-3 ${path === '/notifications' ? 'active' : ''}`}>
                            <div className="relative">
                                <Bell size={20} />
                                {notifCount > 0 && (
                                    <span className="absolute -top-1 -right-1 bg-red-500 text-white text-[10px] w-4 h-4 rounded-full flex items-center justify-center font-bold">
                                        {notifCount > 9 ? '9+' : notifCount}
                                    </span>
                                )}
                            </div>
                            <span>Notifications</span>
                        </Link>
                        <Link href={`/users/${user}`} className={`sidebar-link !px-3 ${path.includes(`/users/${user}`) ? 'active' : ''}`}>
                            <div className="w-6 h-6 rounded-full bg-blue-600 text-white flex items-center justify-center text-[10px] font-bold">
                                {user[0].toUpperCase()}
                            </div>
                            <span>My Profile</span>
                        </Link>
                        <Link href="/bookmarks" className={`sidebar-link !px-3 ${path === '/bookmarks' ? 'active' : ''}`}>
                            <Bookmark size={20} />
                            <span>Bookmarks</span>
                        </Link>
                        <Link href="/settings" className={`sidebar-link !px-3 ${path === '/settings' ? 'active' : ''}`}>
                            <Settings size={20} />
                            <span>Settings</span>
                        </Link>
                        <button onClick={handleLogout} className="sidebar-link !px-3 !text-red-500 hover:bg-red-50">
                            <LogOut size={20} />
                            <span>Logout</span>
                        </button>
                    </div>
                ) : (
                    <div className="flex flex-col gap-2">
                        <Link href="/login" className="btn btn-outline w-full !py-2">Log in</Link>
                        <Link href="/register" className="btn btn-primary w-full !py-2">Sign up</Link>
                    </div>
                )}
            </div>
        </aside>
    );
}
