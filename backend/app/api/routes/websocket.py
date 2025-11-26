"""WebSocket routes for real-time updates"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import List, Dict, Optional
import json
import asyncio

from app.core.dependencies import get_optional_user
from app.models.user import User

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: Optional[str] = None):
        """Accept a WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = []
            self.user_connections[user_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, user_id: Optional[str] = None):
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        if user_id and user_id in self.user_connections:
            if websocket in self.user_connections[user_id]:
                self.user_connections[user_id].remove(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send message to a specific connection"""
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        """Broadcast message to all connections"""
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Connection closed, remove it
                if connection in self.active_connections:
                    self.active_connections.remove(connection)
    
    async def send_to_user(self, user_id: str, message: str):
        """Send message to all connections for a specific user"""
        if user_id in self.user_connections:
            for connection in self.user_connections[user_id]:
                try:
                    await connection.send_text(message)
                except:
                    # Connection closed, remove it
                    if connection in self.user_connections[user_id]:
                        self.user_connections[user_id].remove(connection)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            # Parse message
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "ping":
                    # Respond to ping
                    await manager.send_personal_message(
                        json.dumps({"type": "pong"}),
                        websocket
                    )
                elif message_type == "subscribe":
                    # Subscribe to updates (can be extended)
                    await manager.send_personal_message(
                        json.dumps({"type": "subscribed", "channel": message.get("channel")}),
                        websocket
                    )
                else:
                    # Echo back (for testing)
                    await manager.send_personal_message(
                        json.dumps({"type": "echo", "data": message}),
                        websocket
                    )
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    json.dumps({"type": "error", "message": "Invalid JSON"}),
                    websocket
                )
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.websocket("/ws/user")
async def websocket_user_endpoint(websocket: WebSocket, user_id: Optional[str] = None):
    """WebSocket endpoint for authenticated users"""
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                # Handle user-specific messages
                await manager.send_personal_message(
                    json.dumps({"type": "ack", "data": message}),
                    websocket
                )
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    json.dumps({"type": "error", "message": "Invalid JSON"}),
                    websocket
                )
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)


# Helper function to broadcast parlay updates
async def broadcast_parlay_update(parlay_data: Dict):
    """Broadcast parlay update to all connected clients"""
    message = json.dumps({
        "type": "parlay_update",
        "data": parlay_data
    })
    await manager.broadcast(message)


# Helper function to send user-specific notification
async def send_user_notification(user_id: str, notification: Dict):
    """Send notification to specific user"""
    message = json.dumps({
        "type": "notification",
        "data": notification
    })
    await manager.send_to_user(user_id, message)

