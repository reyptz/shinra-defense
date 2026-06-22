"""
Database models and session management for Shinra Defense Engine
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Float, ForeignKey
from sqlalchemy.orm import DeclarativeBase, sessionmaker, relationship, Session
from datetime import datetime, timezone

# Database configuration
DATABASE_URL = "sqlite:///./shinra_defense.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass


class Honeypot(Base):
    """Honeypot table - État des leurres actifs"""
    __tablename__ = "honeypots"
    
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False)  # SMB, SSH, HTTP, etc.
    status = Column(String, default="active")  # active, inactive, compromised
    endpoint = Column(String, nullable=False)  # IP:Port
    container_id = Column(String, nullable=True)  # Docker container ID
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    events = relationship("EbpfEvent", back_populates="honeypot")


class EbpfEvent(Base):
    """Events eBPF table - Logs bruts d'interception Kernel"""
    __tablename__ = "events_ebpf"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    pid = Column(Integer, nullable=False)
    uid = Column(Integer, nullable=False)
    comm = Column(String, nullable=False)  # Process name
    syscall = Column(String, nullable=False)  # openat, read, connect
    target = Column(String, nullable=False)  # Target file/path
    syscall_type = Column(Integer, nullable=False)  # 0: openat, 1: read, 2: connect
    
    # Foreign key to honeypot
    honeypot_id = Column(Integer, ForeignKey("honeypots.id"), nullable=True)
    honeypot = relationship("Honeypot", back_populates="events")
    
    # Relationships
    artifacts = relationship("Artifact", back_populates="event")


class Artifact(Base):
    """Artifacts table - Extracted data (keys, shellcodes)"""
    __tablename__ = "artifacts"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events_ebpf.id"), nullable=False)
    artifact_type = Column(String, nullable=False)  # AES-256, RSA, Shellcode, etc.
    value = Column(Text, nullable=False)  # The extracted value
    confidence = Column(Float, default=0.0)  # Confidence score (0-1)
    extracted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    event = relationship("EbpfEvent", back_populates="artifacts")


class VectorRAG(Base):
    """Vector RAG table - Base de connaissances vectorielle locale"""
    __tablename__ = "vectors_rag"
    
    id = Column(Integer, primary_key=True, index=True)
    embedding = Column(Text, nullable=False)  # Serialized embedding vector
    context = Column(Text, nullable=False)  # Context description
    artifact_type = Column(String, nullable=False)  # Type of artifact
    similarity_threshold = Column(Float, default=0.8)  # Threshold for matching
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# Create all tables
def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for FastAPI to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Database utility functions
def create_honeypot(db: Session, honeypot_type: str, endpoint: str, container_id: str = None):
    """Create a new honeypot entry"""
    honeypot = Honeypot(
        type=honeypot_type,
        status="active",
        endpoint=endpoint,
        container_id=container_id
    )
    db.add(honeypot)
    db.commit()
    db.refresh(honeypot)
    return honeypot


def create_ebpf_event(db: Session, pid: int, uid: int, comm: str, syscall: str, 
                     target: str, syscall_type: int, honeypot_id: int = None):
    """Create a new eBPF event entry"""
    event = EbpfEvent(
        pid=pid,
        uid=uid,
        comm=comm,
        syscall=syscall,
        target=target,
        syscall_type=syscall_type,
        honeypot_id=honeypot_id
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def create_artifact(db: Session, event_id: int, artifact_type: str, 
                   value: str, confidence: float):
    """Create a new artifact entry"""
    artifact = Artifact(
        event_id=event_id,
        artifact_type=artifact_type,
        value=value,
        confidence=confidence
    )
    db.add(artifact)
    db.commit()
    db.refresh(artifact)
    return artifact


def get_active_honeypots(db: Session):
    """Get all active honeypots"""
    return db.query(Honeypot).filter(Honeypot.status == "active").all()


def get_recent_events(db: Session, limit: int = 100):
    """Get recent eBPF events"""
    return db.query(EbpfEvent).order_by(EbpfEvent.timestamp.desc()).limit(limit).all()


def get_artifacts_by_type(db: Session, artifact_type: str = None):
    """Get artifacts, optionally filtered by type"""
    query = db.query(Artifact)
    if artifact_type:
        query = query.filter(Artifact.artifact_type == artifact_type)
    return query.order_by(Artifact.extracted_at.desc()).all()
