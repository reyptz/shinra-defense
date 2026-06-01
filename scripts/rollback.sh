#!/bin/bash
# Shinra Defense - Automated Rollback Script
# Automates the rollback of Shinra Defense components

set -e

# Configuration
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

# Stop services
stop_services() {
    log_info "Stopping Shinra Defense services..."
    
    # Stop Python engine
    if [ -f "${LOG_DIR}/engine.pid" ]; then
        ENGINE_PID=$(cat "${LOG_DIR}/engine.pid")
        if ps -p $ENGINE_PID > /dev/null; then
            kill $ENGINE_PID
            rm "${LOG_DIR}/engine.pid"
            log_info "Python engine stopped (PID: ${ENGINE_PID})"
        else
            log_warn "Python engine was not running"
        fi
    fi
    
    # Stop Rust agent
    if [ -f "${LOG_DIR}/agent.pid" ]; then
        AGENT_PID=$(cat "${LOG_DIR}/agent.pid")
        if ps -p $AGENT_PID > /dev/null; then
            kill $AGENT_PID
            rm "${LOG_DIR}/agent.pid"
            log_info "Rust agent stopped (PID: ${AGENT_PID})"
        else
            log_warn "Rust agent was not running"
        fi
    fi
}

# Remove honeypots
remove_honeypots() {
    log_info "Removing honeypots..."
    cd "${PROJECT_ROOT}/src-engine"
    
    source venv/bin/activate
    python -c "
from container_manager import HoneypotContainerManager
manager = HoneypotContainerManager()
honeypots = manager.list_active_honeypots()
for hp in honeypots:
    manager.stop_container(hp['id'])
    manager.remove_container(hp['id'])
"
    
    if [ $? -eq 0 ]; then
        log_info "Honeypots removed successfully"
    else
        log_warn "Failed to remove some honeypots"
    fi
}

# Cleanup temporary files
cleanup_temp_files() {
    log_info "Cleaning up temporary files..."
    
    rm -rf /tmp/shinra/dumps/*
    rm -rf /tmp/shinra/logs/*
    rm -rf /tmp/shinra/reports/*
    rm -rf /tmp/honeypot-data/*
    
    log_info "Temporary files cleaned up"
}

# Restore from backup
restore_backup() {
    local backup_path=$1
    
    if [ -z "$backup_path" ]; then
        # Find latest backup
        backup_path=$(ls -t "${BACKUP_DIR}"/shinra_backup_* 2>/dev/null | head -1)
    fi
    
    if [ -z "$backup_path" ] || [ ! -d "$backup_path" ]; then
        log_warn "No backup found. Skipping restore."
        return
    fi
    
    log_info "Restoring from backup: ${backup_path}"
    
    # Restore database
    if [ -f "${backup_path}/shinra_defense.db" ]; then
        cp "${backup_path}/shinra_defense.db" "${PROJECT_ROOT}/src-engine/"
        log_info "Database restored"
    fi
    
    # Restore ChromaDB
    if [ -d "${backup_path}/chroma_db" ]; then
        rm -rf "${PROJECT_ROOT}/src-engine/chroma_db"
        cp -r "${backup_path}/chroma_db" "${PROJECT_ROOT}/src-engine/"
        log_info "ChromaDB restored"
    fi
    
    log_info "Backup restored successfully"
}

# Cleanup old backups
cleanup_old_backups() {
    log_info "Cleaning up old backups (older than 7 days)..."
    
    find "${BACKUP_DIR}" -name "shinra_backup_*" -type d -mtime +7 -exec rm -rf {} \;
    
    log_info "Old backups cleaned up"
}

# Reset database
reset_database() {
    log_info "Resetting database..."
    
    cd "${PROJECT_ROOT}/src-engine"
    
    # Remove database file
    if [ -f "shinra_defense.db" ]; then
        rm shinra_defense.db
        log_info "Database removed"
    fi
    
    # Remove ChromaDB
    if [ -d "chroma_db" ]; then
        rm -rf chroma_db
        log_info "ChromaDB removed"
    fi
    
    # Reinitialize
    source venv/bin/activate
    python -c "from database import init_db; init_db()"
    
    log_info "Database reset and reinitialized"
}

# Main rollback function
main() {
    local restore_flag=false
    local reset_db_flag=false
    local backup_path=""
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --restore)
                restore_flag=true
                backup_path="$2"
                shift 2
                ;;
            --reset-db)
                reset_db_flag=true
                shift
                ;;
            --backup)
                backup_path="$2"
                shift 2
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    log_info "Starting Shinra Defense rollback..."
    log_info "Timestamp: ${TIMESTAMP}"
    
    stop_services
    remove_honeypots
    cleanup_temp_files
    
    if [ "$reset_db_flag" = true ]; then
        reset_database
    fi
    
    if [ "$restore_flag" = true ]; then
        restore_backup "$backup_path"
    fi
    
    cleanup_old_backups
    
    log_info "Rollback completed successfully!"
}

# Run main function
main "$@"
