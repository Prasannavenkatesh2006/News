"""
WebSocket connection manager for real-time updates.
Handles live feed, notifications, and disaster alerts.
"""
import json
import logging
from typing import Dict, Set, List, Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time features."""
    
    def __init__(self):
        # General feed connections
        self.feed_connections: List[WebSocket] = []
        # Per-user notification connections: user_id -> set of websockets
        self.user_connections: Dict[str, Set[WebSocket]] = {}
        # Per-community connections: community_slug -> set of websockets
        self.community_connections: Dict[str, Set[WebSocket]] = {}
        # Disaster alert subscribers
        self.alert_connections: List[WebSocket] = []
    
    async def connect_feed(self, websocket: WebSocket):
        await websocket.accept()
        self.feed_connections.append(websocket)
        logger.info(f"Feed WS connected. Total: {len(self.feed_connections)}")
    
    async def connect_user(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(websocket)
        logger.info(f"User WS connected: {user_id}")
    
    async def connect_community(self, websocket: WebSocket, community_slug: str):
        await websocket.accept()
        if community_slug not in self.community_connections:
            self.community_connections[community_slug] = set()
        self.community_connections[community_slug].add(websocket)
    
    async def connect_alerts(self, websocket: WebSocket):
        await websocket.accept()
        self.alert_connections.append(websocket)
    
    def disconnect_feed(self, websocket: WebSocket):
        if websocket in self.feed_connections:
            self.feed_connections.remove(websocket)
    
    def disconnect_user(self, websocket: WebSocket, user_id: str):
        if user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
    
    def disconnect_community(self, websocket: WebSocket, community_slug: str):
        if community_slug in self.community_connections:
            self.community_connections[community_slug].discard(websocket)
    
    def disconnect_alerts(self, websocket: WebSocket):
        if websocket in self.alert_connections:
            self.alert_connections.remove(websocket)
    
    async def broadcast_to_feed(self, message: dict):
        """Broadcast to all feed subscribers."""
        dead = []
        for ws in self.feed_connections:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.feed_connections.remove(ws)
    
    async def send_to_user(self, user_id: str, message: dict):
        """Send a notification to a specific user."""
        if user_id not in self.user_connections:
            return
        dead = set()
        for ws in self.user_connections[user_id]:
            try:
                await ws.send_json(message)
            except Exception:
                dead.add(ws)
        self.user_connections[user_id] -= dead
    
    async def broadcast_to_community(self, community_slug: str, message: dict):
        """Broadcast to all subscribers of a community."""
        if community_slug not in self.community_connections:
            return
        dead = set()
        for ws in self.community_connections[community_slug]:
            try:
                await ws.send_json(message)
            except Exception:
                dead.add(ws)
        self.community_connections[community_slug] -= dead
    
    async def broadcast_alert(self, message: dict):
        """Broadcast disaster alert to all alert subscribers."""
        dead = []
        for ws in self.alert_connections:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.alert_connections.remove(ws)


# Singleton instance
manager = ConnectionManager()
