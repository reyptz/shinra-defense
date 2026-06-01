# Shinra Defense Engine (Python)

Control Plane & Intelligence for the Shinra Defense platform.

## Architecture

- **FastAPI**: REST API for honeypot and artifact management
- **SQLite**: Database for honeypots, events, and artifacts
- **ChromaDB**: Vector database for RAG correlation
- **Docker/Podman**: Container management for honeypot provisioning
- **WebSocket**: Real-time event streaming

## Requirements

- Python 3.9+
- Docker or Podman (for container management)

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Start the FastAPI server
python main.py

# Or with uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## API Endpoints

### Health
- `GET /health` - Health check

### Honeypots
- `POST /api/honeypots` - Create honeypot
- `GET /api/honeypots` - List active honeypots
- `GET /api/honeypots/{id}` - Get specific honeypot
- `DELETE /api/honeypots/{id}` - Delete honeypot

### Events
- `POST /api/events` - Create eBPF event
- `GET /api/events` - List recent events
- `GET /api/events/{id}` - Get specific event

### Artifacts
- `POST /api/artifacts` - Create artifact
- `GET /api/artifacts` - List artifacts
- `GET /api/artifacts/{id}` - Get specific artifact

### Statistics
- `GET /api/stats` - System statistics

### WebSocket
- `WS /ws` - Real-time event streaming

## Components

### database.py
SQLAlchemy models and database session management:
- Honeypot model
- EbpfEvent model
- Artifact model
- VectorRAG model

### main.py
FastAPI application with:
- REST API endpoints
- WebSocket connection manager
- Event broadcasting

### container_manager.py
Docker/Podman container management:
- SMB honeypot creation
- SSH honeypot creation
- HTTP honeypot creation
- Container lifecycle management

### rag_engine.py
RAG correlation engine:
- ChromaDB integration
- Sentence transformer embeddings
- Artifact similarity search
- Pattern analysis

## Database Schema

### honeypots
- id, type, status, endpoint, container_id, created_at, updated_at

### events_ebpf
- id, timestamp, pid, uid, comm, syscall, target, syscall_type, honeypot_id

### artifacts
- id, event_id, artifact_type, value, confidence, extracted_at

### vectors_rag
- id, embedding, context, artifact_type, similarity_threshold, created_at

## Configuration

Environment variables can be set in `.env`:
- `DATABASE_URL`: SQLite database path (default: ./shinra_defense.db)
- `CHROMA_PERSIST_DIR`: ChromaDB persistence directory (default: ./chroma_db)