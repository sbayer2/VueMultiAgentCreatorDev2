"""WebSocket connection manager"""
from typing import Dict, List
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.conversation_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, conversation_id: int = None):
        try:
            await websocket.accept()
            self.active_connections.append(websocket)
            
            if conversation_id:
                if conversation_id not in self.conversation_connections:
                    self.conversation_connections[conversation_id] = []
                self.conversation_connections[conversation_id].append(websocket)
                
            logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
        except Exception as e:
            logger.error(f"Error connecting WebSocket: {e}")

    def disconnect(self, websocket: WebSocket, conversation_id: int = None):
        try:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
            
            if conversation_id and conversation_id in self.conversation_connections:
                if websocket in self.conversation_connections[conversation_id]:
                    self.conversation_connections[conversation_id].remove(websocket)
                
                # Clean up empty conversation lists
                if not self.conversation_connections[conversation_id]:
                    del self.conversation_connections[conversation_id]
                    
            logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
        except Exception as e:
            logger.error(f"Error disconnecting WebSocket: {e}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")

    async def send_json_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending JSON message: {e}")

    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)

    async def broadcast_to_conversation(self, conversation_id: int, message: dict):
        if conversation_id not in self.conversation_connections:
            return
        
        disconnected = []
        for connection in self.conversation_connections[conversation_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to conversation {conversation_id}: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection, conversation_id)