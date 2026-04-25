/**
 * ANIP Frontend API Client
 * This file handles all communication with the FastAPI backend.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8010';

/**
 * Core fetch wrapper that handles Auth headers and error responses.
 */
export async function apiFetch(path: string, options: RequestInit = {}) {
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    
    const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        ...(options.headers as Record<string, string>),
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    // Handle relative paths vs full URLs
    const url = path.startsWith('http') ? path : `${API_URL}${path.startsWith('/') ? '' : '/'}${path}`;

    const response = await fetch(url, {
        ...options,
        headers,
    });

    if (!response.ok) {
        let errorData;
        try {
            errorData = await response.json();
        } catch (e) {
            errorData = { detail: 'An unexpected error occurred' };
        }
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    if (response.status === 204) return null;
    return response.json();
}

// ========== AUTH ==========

export async function login(formData: any) {
    // FastAPI OAuth2 expects form-url-encoded for the login endpoint
    const body = new URLSearchParams();
    body.append('username', formData.username);
    body.append('password', formData.password);

    const res = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: body.toString(),
    });

    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Login failed');
    }
    return res.json();
}

export async function register(userData: any) {
    return apiFetch('/auth/register', {
        method: 'POST',
        body: JSON.stringify(userData),
    });
}

// ========== SOCIAL & NEWS ==========

export async function getCommunities() {
    return apiFetch('/api/v1/social/communities');
}

export async function getPosts(communitySlug?: string, offset = 0, limit = 20) {
    let path = '/api/v1/social/posts';
    const params = new URLSearchParams({ offset: offset.toString(), limit: limit.toString() });
    if (communitySlug) params.append('community_slug', communitySlug);
    return apiFetch(`${path}?${params.toString()}`);
}

export async function getFeed(options: { sort?: string; limit?: number; offset?: number; country?: string; state?: string } = {}) {
    const params = new URLSearchParams();
    if (options.sort) params.append('sort', options.sort);
    if (options.limit) params.append('limit', options.limit.toString());
    if (options.offset) params.append('offset', options.offset.toString());
    if (options.country) params.append('country', options.country);
    if (options.state) params.append('state', options.state);
    
    return apiFetch(`/api/v1/social/feed?${params.toString()}`);
}

export async function getPost(postId: string) {
    return apiFetch(`/api/v1/social/posts/${postId}`);
}

export async function createPost(postData: any) {
    return apiFetch('/api/v1/social/posts', {
        method: 'POST',
        body: JSON.stringify(postData),
    });
}

export async function getComments(postId: string) {
    return apiFetch(`/api/v1/social/posts/${postId}/comments`);
}

export async function createComment(postId: string, commentData: any) {
    return apiFetch(`/api/v1/social/posts/${postId}/comments`, {
        method: 'POST',
        body: JSON.stringify(commentData),
    });
}

export async function votePost(postId: string, voteData: { vote_type: number }) {
    return apiFetch(`/api/v1/social/posts/${postId}/vote`, {
        method: 'POST',
        body: JSON.stringify(voteData),
    });
}

export async function voteComment(commentId: string, voteData: { vote_type: number }) {
    return apiFetch(`/api/v1/social/comments/${commentId}/vote`, {
        method: 'POST',
        body: JSON.stringify(voteData),
    });
}

export async function getTrending(period = 'day', limit = 30) {
    return apiFetch(`/api/social/trending?period=${period}&limit=${limit}`);
}

export async function getUserProfile(username: string) {
    return apiFetch(`/api/v1/social/users/${username}`);
}

export async function getMyProfile() {
    return apiFetch('/api/v1/social/me');
}

// ========== BOOKMARKS ==========

export async function getBookmarks(targetType?: string) {
    const path = targetType ? `/api/social/bookmarks?target_type=${targetType}` : '/api/social/bookmarks';
    return apiFetch(path);
}

export async function toggleBookmark(targetType: string, targetId: string) {
    return apiFetch(`/api/social/bookmarks/${targetType}/${targetId}`, {
        method: 'POST'
    });
}

// ========== NOTIFICATIONS ==========

export async function getNotifications(limit = 30, unreadOnly = false) {
    return apiFetch(`/api/notifications?limit=${limit}&unread_only=${unreadOnly}`);
}

export async function getNotificationCount() {
    const res = await apiFetch('/api/notifications/count');
    // Map backend 'unread' to frontend 'unread_count' if necessary, 
    // but the Topbar expects .unread_count based on earlier logs.
    return { unread_count: res.unread, total: res.total };
}

export async function markNotificationRead(id: string) {
    return apiFetch(`/api/notifications/${id}/read`, { method: 'POST' });
}

export async function markAllNotificationsRead() {
    return apiFetch('/api/notifications/read-all', { method: 'POST' });
}

// ========== DISASTER ALERTS ==========

export async function getAlerts(activeOnly = true) {
    return apiFetch(`/api/alerts?active_only=${activeOnly}`);
}

export async function getAlertStats() {
    return apiFetch('/api/alerts/stats');
}

export function connectAlertsWS(onMessage: (data: any) => void) {
    if (typeof window === 'undefined') return null;
    const wsUrl = API_URL.replace('http', 'ws').replace('https', 'wss') + '/ws/alerts';
    const ws = new WebSocket(wsUrl);
    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            onMessage(data);
        } catch (e) {
            console.error('Failed to parse WS message', e);
        }
    };
    return ws;
}

// ========== SETTINGS & i18n ==========

export async function getSettings() {
    return apiFetch('/api/social/settings');
}

export async function updateSettings(settings: any) {
    return apiFetch('/api/social/settings', {
        method: 'PUT',
        body: JSON.stringify(settings),
    });
}

export async function updateProfile(profile: any) {
    return apiFetch('/api/social/profile', {
        method: 'PUT',
        body: JSON.stringify(profile),
    });
}

export async function getLanguages() {
    return apiFetch('/api/i18n/languages');
}
