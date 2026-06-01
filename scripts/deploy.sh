#!/bin/bash
# Shinra Defense - Automated Deployment Script
# Automates the deployment of all Shinra Defense components

set -e

# Configuration
DEPLOY_ENV="${DEPLOY_ENV:-dev}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-/tmp/shinra/backups}"
LOG_DIR="/var/log/shinra"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Create necessary directories
setup_directories() {
    log_info "Creating necessary directories..."
    mkdir -p "${BACKUP_DIR}"
    mkdir -p "${LOG_DIR}"
    mkdir -p /tmp/shinra/dumps
    mkdir -p /tmp/shinra/logs
    mkdir -p /tmp/shinra/reports
    mkdir -p /tmp/honeypot-data
    log_info "Directories created successfully"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Nix
    if ! command -v nix &> /dev/null; then
        log_error "Nix is not installed. Please install Nix first."
        exit 1
    fi
    
    # Check Docker/Podman
    if ! command -v docker &> /dev/null && ! command -v podman &> /dev/null; then
        log_error "Docker or Podman is not installed. Please install one of them."
        exit 1
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed. Please install Python 3.9+."
        exit 1
    fi
    
    # Check Rust
    if ! command -v rustc &> /dev/null; then
        log_error "Rust is not installed. Please install Rust 1.70+."
        exit 1
    fi
    
    log_info "All prerequisites satisfied"
}

# Backup existing deployment
backup_existing() {
    log_info "Backing up existing deployment..."
    
    BACKUP_PATH="${BACKUP_DIR}/shinra_backup_${TIMESTAMP}"
    mkdir -p "${BACKUP_PATH}"
    
    # Backup database if exists
    if [ -f "${PROJECT_ROOT}/src-engine/shinra_defense.db" ]; then
        cp "${PROJECT_ROOT}/src-engine/shinra_defense.db" "${BACKUP_PATH}/"
        log_info "Database backed up"
    fi
    
    # Backup ChromaDB if exists
    if [ -d "${PROJECT_ROOT}/src-engine/chroma_db" ]; then
        cp -r "${PROJECT_ROOT}/src-engine/chroma_db" "${BACKUP_PATH}/"
        log_info "ChromaDB backed up"
    fi
    
    log_info "Backup completed: ${BACKUP_PATH}"
}

# Build Rust agent
build_agent() {
    log_info "Building Rust eBPF agent..."
    cd "${PROJECT_ROOT}/src-agent"
    
    cargo build --release
    if [ $? -eq 0 ]; then
        log_info "Rust agent built successfully"
    else
        log_error "Failed to build Rust agent"
        exit 1
    fi
}

# Install Python dependencies
install_python_deps() {
    log_info "Installing Python dependencies..."
    cd "${PROJECT_ROOT}/src-engine"
    
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    if [ $? -eq 0 ]; then
        log_info "Python dependencies installed successfully"
    else
        log_error "Failed to install Python dependencies"
        exit 1
    fi
}

# Initialize database
init_database() {
    log_info "Initializing database..."
    cd "${PROJECT_ROOT}/src-engine"
    
    source venv/bin/activate
    python -c "from database import init_db; init_db()"
    
    if [ $? -eq 0 ]; then
        log_info "Database initialized successfully"
    else
        log_error "Failed to initialize database"
        exit 1
    fi
}

# Start services
start_services() {
    log_info "Starting Shinra Defense services..."
    
    # Start Python engine
    cd "${PROJECT_ROOT}/src-engine"
    source venv/bin/activate
    nohup python main.py > "${LOG_DIR}/engine_${TIMESTAMP}.log" 2>&1 &
    ENGINE_PID=$!
    echo $ENGINE_PID > "${LOG_DIR}/engine.pid"
    log_info "Python engine started (PID: ${ENGINE_PID})"
    
    # Start Rust agent (requires root)
    if [ "$EUID" -eq 0 ]; then
        cd "${PROJECT_ROOT}/src-agent"
        nohup ./target/release/shinra-agent > "${LOG_DIR}/agent_${TIMESTAMP}.log" 2>&1 &
        AGENT_PID=$!
        echo $AGENT_PID > "${LOG_DIR}/agent.pid"
        log_info "Rust agent started (PID: ${AGENT_PID})"
    else
        log_warn "Rust agent requires root privileges. Skipping..."
    fi
}

# Deploy honeypots
deploy_honeypots() {
    log_info "Deploying honeypots..."
    cd "${PROJECT_ROOT}/src-engine"
    
    source venv/bin/activate
    python -c "
from container_manager import HoneypotContainerManager
manager = HoneypotContainerManager()
manager.create_smb_honeypot('honeypot-smb', 445)
manager.create_ssh_honeypot('honeypot-ssh', 2222)
manager.create_http_honeypot('honeypot-http', 80)
"
    
    if [ $? -eq 0 ]; then
        log_info "Honeypots deployed successfully"
    else
        log_warn "Failed to deploy honeypots"
    fi
}

# Health check
health_check() {
    log_info "Performing health check..."
    
    # Check Python engine
    if [ -f "${LOG_DIR}/engine.pid" ]; then
        ENGINE_PID=$(cat "${LOG_DIR}/engine.pid")
        if ps -p $ENGINE_PID > /dev/null; then
            log_info "Python engine is running (PID: ${ENGINE_PID})"
        else
            log_error "Python engine is not running"
        fi
    fi
    
    # Check Rust agent
    if [ -f "${LOG_DIR}/agent.pid" ]; then
        AGENT_PID=$(cat "${LOG_DIR}/agent.pid")
        if ps -p $AGENT_PID > /dev/null; then
            log_info "Rust agent is running (PID: ${AGENT_PID})"
        else
            log_warn "Rust agent is not running"
        fi
    fi
    
    # Check API endpoint
    if curl -s http://localhost:8000/health > /dev/null; then
        log_info "API endpoint is accessible"
    else
        log_warn "API endpoint is not accessible"
    fi
}

# Main deployment function
main() {
    log_info "Starting Shinra Defense deployment..."
    log_info "Environment: ${DEPLOY_ENV}"
    log_info "Timestamp: ${TIMESTAMP}"
    
    setup_directories
    check_prerequisites
    backup_existing
    build_agent
    install_python_deps
    init_database
    start_services
    deploy_honeypots
    health_check
    
    log_info "Deployment completed successfully!"
    log_info "Logs are available in: ${LOG_DIR}"
    log_info "Backup location: ${BACKUP_DIR}/shinra_backup_${TIMESTAMP}"
}

# Run main function
main "$@"
