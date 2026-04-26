import { useState, useEffect, useCallback, useRef } from 'react';
import { apiFetch } from './api';

export interface AutoPost {
  id: string;
  title: string;
  url?: string;
  content: string;
  platform: string;
  community: string;
  upvotes: number;
  created_at: string;
  importance_score?: number;
}

export function useLiveFeed() {
  const [posts, setPosts] = useState<AutoPost[]>([]);
  const [newPostsCount, setNewPostsCount] = useState(0);
  const [postsPerMinute, setPostsPerMinute] = useState(0);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected'>('disconnected');
  const bufferRef = useRef<AutoPost[]>([]);

  useEffect(() => {
    const apiUrl = 'https://anip-api-giq5.onrender.com';
    const wsUrl = apiUrl.replace('http', 'ws') + '/ws/live-feed';
    
    let ws: WebSocket;
    let keepAliveId: NodeJS.Timeout;
    let rateId: NodeJS.Timeout;
    
    const connect = () => {
      try {
        ws = new WebSocket(wsUrl);
      } catch (e) {
        console.error("WebSocket connection error:", e);
        return;
      }
      
      ws.onopen = () => {
        setConnectionStatus('connected');
        keepAliveId = setInterval(() => ws.send('keepalive'), 30000);
      };
      
      ws.onmessage = (event) => {
        try {
          const rawData = JSON.parse(event.data);
          // Backend uses `type: 'new_auto_post'` with `post` payload
          const data = rawData.post ? rawData.post : rawData;
          if (data && data.title) {
            setPosts(prev => {
              const prevIds = new Set(prev.map(p => p.id));
              if (prevIds.has(data.id)) return prev;
              return [data, ...prev].slice(0, 500);
            });
            bufferRef.current.push(data);
            setNewPostsCount(c => c + 1);
          }
        } catch (e) {
          console.error("WebSocket message parse error:", e);
        }
      };
      
      ws.onclose = () => {
        setConnectionStatus('disconnected');
        clearInterval(keepAliveId);
        setTimeout(connect, 3000); // Reconnect after 3s
      };
      
      ws.onerror = (err) => {
        console.error("WebSocket error", err);
        ws.close();
      };
    };
    
    connect();
    
    // Calculates ppm
    rateId = setInterval(() => {
        const now = Date.now();
        const oneMinAgo = now - 60000;
        const recentCount = bufferRef.current.filter(p => new Date(p.created_at).getTime() >= oneMinAgo).length;
        bufferRef.current = bufferRef.current.filter(p => new Date(p.created_at).getTime() >= oneMinAgo);
        setPostsPerMinute(recentCount);
    }, 5000);

    return () => {
      clearInterval(keepAliveId);
      clearInterval(rateId);
      if (ws) ws.close();
    };
  }, []);

  const clearNewCount = useCallback(() => setNewPostsCount(0), []);

  return { posts, newPostsCount, postsPerMinute, connectionStatus, clearNewCount };
}

export async function getScraperStats() {
  return apiFetch('/api/v1/scraper/stats').catch(() => ({}));
}
