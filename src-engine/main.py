"""
Shinra Defense Engine - Main FastAPI Application
Control Plane & Intelligence for Active Defense Platform
"""
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel

from database import (
    get_db, init_db, create_honeypot, create_ebpf_event, create_artifact,
    get_active_honeypots, get_recent_events, get_artifacts_by_type,
    Honeypot, EbpfEvent, Artifact
)

# Lifespan context manager (remplace @app.on_event déprécié)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup, cleanup on shutdown"""
    init_db()
    print("Shinra Defense Engine started successfully")
    yield
    print("Shinra Defense Engine shutting down")


# Initialize FastAPI app
app = FastAPI(
    title="Shinra Defense Engine",
    description="Control Plane & Intelligence for Active Defense Platform",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

# Pydantic models for API
class HoneypotCreate(BaseModel):
    type: str
    endpoint: str
    container_id: Optional[str] = None

class HoneypotResponse(BaseModel):
    id: int
    type: str
    status: str
    endpoint: str
    container_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class EbpfEventCreate(BaseModel):
    pid: int
    uid: int
    comm: str
    syscall: str
    target: str
    syscall_type: int
    honeypot_id: Optional[int] = None

class EbpfEventResponse(BaseModel):
    id: int
    timestamp: datetime
    pid: int
    uid: int
    comm: str
    syscall: str
    target: str
    syscall_type: int
    honeypot_id: Optional[int]

    class Config:
        from_attributes = True

class ArtifactCreate(BaseModel):
    event_id: int
    artifact_type: str
    value: str
    confidence: float

class ArtifactResponse(BaseModel):
    id: int
    event_id: int
    artifact_type: str
    value: str
    confidence: float
    extracted_at: datetime

    class Config:
        from_attributes = True

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "operational",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "shinra-defense-engine"
    }

# Honeypot endpoints
@app.post("/api/honeypots", response_model=HoneypotResponse)
async def create_honeypot_endpoint(honeypot: HoneypotCreate, db: Session = Depends(get_db)):
    """Create a new honeypot"""
    try:
        db_honeypot = create_honeypot(
            db,
            honeypot.type,
            honeypot.endpoint,
            honeypot.container_id
        )
        
        # Broadcast to WebSocket clients
        await manager.broadcast({
            "type": "honeypot_created",
            "data": {
                "id": db_honeypot.id,
                "type": db_honeypot.type,
                "endpoint": db_honeypot.endpoint,
                "status": db_honeypot.status
            }
        })
        
        return db_honeypot
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/honeypots", response_model=List[HoneypotResponse])
async def get_honeypots(db: Session = Depends(get_db)):
    """Get all active honeypots"""
    return get_active_honeypots(db)

@app.get("/api/honeypots/{honeypot_id}", response_model=HoneypotResponse)
async def get_honeypot(honeypot_id: int, db: Session = Depends(get_db)):
    """Get a specific honeypot by ID"""
    honeypot = db.query(Honeypot).filter(Honeypot.id == honeypot_id).first()
    if not honeypot:
        raise HTTPException(status_code=404, detail="Honeypot not found")
    return honeypot

@app.delete("/api/honeypots/{honeypot_id}")
async def delete_honeypot(honeypot_id: int, db: Session = Depends(get_db)):
    """Delete a honeypot"""
    honeypot = db.query(Honeypot).filter(Honeypot.id == honeypot_id).first()
    if not honeypot:
        raise HTTPException(status_code=404, detail="Honeypot not found")
    
    honeypot.status = "inactive"
    db.commit()
    
    await manager.broadcast({
        "type": "honeypot_deleted",
        "data": {"id": honeypot_id}
    })
    
    return {"message": "Honeypot deleted successfully"}

# eBPF Event endpoints
@app.post("/api/events", response_model=EbpfEventResponse)
async def create_event(event: EbpfEventCreate, db: Session = Depends(get_db)):
    """Create a new eBPF event"""
    try:
        db_event = create_ebpf_event(
            db,
            event.pid,
            event.uid,
            event.comm,
            event.syscall,
            event.target,
            event.syscall_type,
            event.honeypot_id
        )
        
        # Broadcast to WebSocket clients
        await manager.broadcast({
            "type": "ebpf_event",
            "data": {
                "id": db_event.id,
                "timestamp": db_event.timestamp.isoformat(),
                "pid": db_event.pid,
                "syscall": db_event.syscall,
                "target": db_event.target
            }
        })
        
        return db_event
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/events", response_model=List[EbpfEventResponse])
async def get_events(limit: int = 100, db: Session = Depends(get_db)):
    """Get recent eBPF events"""
    return get_recent_events(db, limit)

@app.get("/api/events/{event_id}", response_model=EbpfEventResponse)
async def get_event(event_id: int, db: Session = Depends(get_db)):
    """Get a specific event by ID"""
    event = db.query(EbpfEvent).filter(EbpfEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

# Artifact endpoints
@app.post("/api/artifacts", response_model=ArtifactResponse)
async def create_artifact_endpoint(artifact: ArtifactCreate, db: Session = Depends(get_db)):
    """Create a new artifact"""
    try:
        db_artifact = create_artifact(
            db,
            artifact.event_id,
            artifact.artifact_type,
            artifact.value,
            artifact.confidence
        )
        
        # Broadcast to WebSocket clients
        await manager.broadcast({
            "type": "artifact_extracted",
            "data": {
                "id": db_artifact.id,
                "type": db_artifact.artifact_type,
                "confidence": db_artifact.confidence
            }
        })
        
        return db_artifact
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/artifacts", response_model=List[ArtifactResponse])
async def get_artifacts(artifact_type: Optional[str] = None, db: Session = Depends(get_db)):
    """Get artifacts, optionally filtered by type"""
    return get_artifacts_by_type(db, artifact_type)

@app.get("/api/artifacts/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(artifact_id: int, db: Session = Depends(get_db)):
    """Get a specific artifact by ID"""
    artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact

# Statistics endpoint
@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get system statistics"""
    active_honeypots = db.query(Honeypot).filter(Honeypot.status == "active").count()
    total_events = db.query(EbpfEvent).count()
    total_artifacts = db.query(Artifact).count()
    
    return {
        "active_honeypots": active_honeypots,
        "total_events": total_events,
        "total_artifacts": total_artifacts,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time event streaming"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            # Echo back or handle client messages
            await websocket.send_json({"status": "connected"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
