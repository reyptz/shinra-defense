#!/bin/bash
# Shinra Defense - Health Check Script
# Performs health checks on all Shinra Defense components

set -e

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
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

# Check Python engine
check_engine() {
    log_info "Checking Python engine..."
    
    if [ -f "${LOG_DIR}/engine.pid" ]; then
        ENGINE_PID=$(cat "${LOG_DIR}/engine.pid")
        if ps -p $ENGINE_PID > /dev/null; then
            log_info "Python engine is running (PID: ${ENGINE_PID})"
            
            # Check API endpoint
            if curl -s http://localhost:8000/health > /dev/null; then
                log_info "API endpoint is accessible"
                return 0
            else
                log_error "API endpoint is not accessible"
                return 1
            fi
        else
            log_error "Python engine is not running"
            return 1
        fi
    else
        log_error "Python engine PID file not found"
        return 1
    fi
}

# Check Rust agent
check_agent() {
    log_info "Checking Rust agent..."
    
    if [ -f "${LOG_DIR}/agent.pid" ]; then
        AGENT_PID=$(cat "${LOG_DIR}/agent.pid")
        if ps -p $AGENT_PID > /dev/null; then
            log_info "Rust agent is running (PID: ${AGENT_PID})"
            return 0
        else
            log_error "Rust agent is not running"
            return 1
        fi
    else
        log_warn "Rust agent PID file not found (may not be running)"
        return 1
    fi
}

# Check honeypots
check_honeypots() {
    log_info "Checking honeypots..."
    
    cd "${PROJECT_ROOT}/src-engine"
    source venv/bin/activate
    
    python -c "
from container_manager import HoneypotContainerManager
manager = HoneypotContainerManager()
honeypots = manager.list_active_honeypots()
print(f'Active honeypots: {len(honeypots)}')
for hp in honeypots:
    print(f'  - {hp[\"name\"]} ({hp[\"status\"]})')
" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        log_info "Honeypots check completed"
        return 0
    else
        log_error "Failed to check honeypots"
        return 1
    fi
}

# Check database
check_database() {
    log_info "Checking database..."
    
    DB_PATH="${PROJECT_ROOT}/src-engine/shinra_defense.db"
    
    if [ -f "$DB_PATH" ]; then
        log_info "Database file exists"
        
        # Check if database is accessible
        cd "${PROJECT_ROOT}/src-engine"
        source venv/bin/activate
        
        python -c "
from database import get_db
db = next(get_db())
print('Database is accessible')
db.close()
" 2>/dev/null
        
        if [ $? -eq 0 ]; then
            log_info "Database is accessible"
            return 0
        else
            log_error "Database is not accessible"
            return 1
        fi
    else
        log_error "Database file not found"
        return 1
    fi
}

# Check ChromaDB
check_chromadb() {
    log_info "Checking ChromaDB..."
    
    CHROMA_PATH="${PROJECT_ROOT}/src-engine/chroma_db"
    
    if [ -d "$CHROMA_PATH" ]; then
        log_info "ChromaDB directory exists"
        return 0
    else
        log_warn "ChromaDB directory not found"
        return 1
    fi
}

# Check disk space
check_disk_space() {
    log_info "Checking disk space..."
    
    local usage=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [ $usage -lt 80 ]; then
        log_info "Disk space usage: ${usage}% (OK)"
        return 0
    elif [ $usage -lt 90 ]; then
        log_warn "Disk space usage: ${usage}% (WARNING)"
        return 1
    else
        log_error "Disk space usage: ${usage}% (CRITICAL)"
        return 1
    fi
}

# Check memory usage
check_memory() {
    log_info "Checking memory usage..."
    
    local usage=$(free | awk 'NR==2 {printf "%.0f", $3/$2 * 100}')
    
    if [ $usage -lt 80 ]; then
        log_info "Memory usage: ${usage}% (OK)"
        return 0
    elif [ $usage -lt 90 ]; then
        log_warn "Memory usage: ${usage}% (WARNING)"
        return 1
    else
        log_error "Memory usage: ${usage}% (CRITICAL)"
        return 1
    fi
}

# Generate health report
generate_report() {
    local engine_status=$1
    local agent_status=$2
    local honeypots_status=$3
    local database_status=$4
    local chromadb_status=$5
    local disk_status=$6
    local memory_status=$7
    
    local report_file="${LOG_DIR}/health_report_${TIMESTAMP}.txt"
    
    cat > "$report_file" << EOF
Shinra Defense Health Report
============================
Timestamp: ${TIMESTAMP}

Component Status:
- Python Engine: $([ $engine_status -eq 0 ] && echo "OK" || echo "FAIL")
- Rust Agent: $([ $agent_status -eq 0 ] && echo "OK" || echo "FAIL")
- Honeypots: $([ $honeypots_status -eq 0 ] && echo "OK" || echo "FAIL")
- Database: $([ $database_status -eq 0 ] && echo "OK" || echo "FAIL")
- ChromaDB: $([ $chromadb_status -eq 0 ] && echo "OK" || echo "FAIL")

System Resources:
- Disk Space: $([ $disk_status -eq 0 ] && echo "OK" || echo "WARNING")
- Memory: $([ $memory_status -eq 0 ] && echo "OK" || echo "WARNING")

Overall Status: $([ $engine_status -eq 0 ] && [ $database_status -eq 0 ] && echo "HEALTHY" || echo "UNHEALTHY")
EOF
    
    log_info "Health report generated: ${report_file}"
}

# Main health check function
main() {
    log_info "Starting Shinra Defense health check..."
    log_info "Timestamp: ${TIMESTAMP}"
    
    local engine_status=0
    local agent_status=0
    local honeypots_status=0
    local database_status=0
    local chromadb_status=0
    local disk_status=0
    local memory_status=0
    
    check_engine || engine_status=1
    check_agent || agent_status=1
    check_honeypots || honeypots_status=1
    check_database || database_status=1
    check_chromadb || chromadb_status=1
    check_disk_space || disk_status=1
    check_memory || memory_status=1
    
    generate_report \
        $engine_status \
        $agent_status \
        $honeypots_status \
        $database_status \
        $chromadb_status \
        $disk_status \
        $memory_status
    
    if [ $engine_status -eq 0 ] && [ $database_status -eq 0 ]; then
        log_info "Overall system status: HEALTHY"
        exit 0
    else
        log_error "Overall system status: UNHEALTHY"
        exit 1
    fi
}

# Run main function
main "$@"
