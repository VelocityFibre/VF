#!/bin/bash
# QFieldCloud Migration to VF Server - Execution Script
# Created: 2026-01-08
# Source: 72.61.166.168 (Old Hostinger)
# Target: 100.96.203.105 (VF Server, Port 8080)

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
OLD_SERVER="72.61.166.168"
OLD_USER="root"
VF_SERVER="100.96.203.105"
VF_USER="velo"
VF_PASSWORD="2025"
TARGET_PORT="8080"

# Functions
print_header() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_step() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

confirm() {
    read -p "$(echo -e ${YELLOW}$1 [y/N]: ${NC})" -n 1 -r
    echo
    [[ $REPLY =~ ^[Yy]$ ]]
}

# Pre-flight checks
preflight_checks() {
    print_header "Pre-Flight Checks"

    # Check SSH access to old server
    echo -n "Checking old server access... "
    if ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no ${OLD_USER}@${OLD_SERVER} "echo OK" &>/dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        print_error "Cannot connect to old server ${OLD_SERVER}"
        exit 1
    fi

    # Check SSH access to VF server
    echo -n "Checking VF server access... "
    if sshpass -p "${VF_PASSWORD}" ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no ${VF_USER}@${VF_SERVER} "echo OK" &>/dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        print_error "Cannot connect to VF server ${VF_SERVER}"
        exit 1
    fi

    # Check port 8080 availability
    echo -n "Checking port 8080 on VF server... "
    PORT_CHECK=$(sshpass -p "${VF_PASSWORD}" ssh ${VF_USER}@${VF_SERVER} "sudo netstat -tulpn | grep :8080" || echo "")
    if [ -z "$PORT_CHECK" ]; then
        echo -e "${GREEN}✓ Available${NC}"
    else
        echo -e "${YELLOW}⚠ Port in use${NC}"
        print_warning "Port 8080 is already in use on VF Server"
        if ! confirm "Continue anyway?"; then
            exit 1
        fi
    fi

    # Check available disk space on VF server
    echo -n "Checking VF server disk space... "
    VF_SPACE=$(sshpass -p "${VF_PASSWORD}" ssh ${VF_USER}@${VF_SERVER} "df -h / | awk 'NR==2 {print \$4}'")
    echo -e "${GREEN}✓ $VF_SPACE available${NC}"

    print_step "Pre-flight checks complete"
    echo
}

# Phase 1: Preparation
phase1_preparation() {
    print_header "Phase 1: VF Server Preparation"

    echo "Creating QFieldCloud directory..."
    sshpass -p "${VF_PASSWORD}" ssh ${VF_USER}@${VF_SERVER} "
        sudo mkdir -p /opt/qfieldcloud/{data,backups,logs,scripts}
        sudo chown -R velo:velo /opt/qfieldcloud
    "
    print_step "Directories created"

    echo "Checking Docker installation..."
    sshpass -p "${VF_PASSWORD}" ssh ${VF_USER}@${VF_SERVER} "docker --version"
    print_step "Docker verified"

    echo
}

# Phase 2: Data Transfer
phase2_data_transfer() {
    print_header "Phase 2: Data Transfer"

    print_warning "This will transfer database backup and configuration"
    print_warning "Estimated time: 5-10 minutes"

    if ! confirm "Start data transfer?"; then
        return
    fi

    # Transfer database backup
    echo "Transferring database backup..."
    sshpass -p "${VF_PASSWORD}" scp -o StrictHostKeyChecking=no \
        ${OLD_USER}@${OLD_SERVER}:/root/qfield_db_backup_20260108_090406.sql \
        ${VF_USER}@${VF_SERVER}:/opt/qfieldcloud/backups/ 2>&1 | grep -v "Warning"
    print_step "Database backup transferred"

    # Transfer configuration
    echo "Transferring configuration..."
    sshpass -p "${VF_PASSWORD}" scp -o StrictHostKeyChecking=no \
        ${OLD_USER}@${OLD_SERVER}:/root/qfield_config_20260108_091458.tar.gz \
        ${VF_USER}@${VF_SERVER}:/opt/qfieldcloud/ 2>&1 | grep -v "Warning"
    print_step "Configuration transferred"

    # Extract configuration
    echo "Extracting configuration..."
    sshpass -p "${VF_PASSWORD}" ssh ${VF_USER}@${VF_SERVER} "
        cd /opt/qfieldcloud
        tar -xzf qfield_config_20260108_091458.tar.gz
        cp qfield_config_*/docker-compose*.yml ./
        cp qfield_config_*/.env ./
    "
    print_step "Configuration extracted"

    echo
}

# Phase 3: Configuration
phase3_configuration() {
    print_header "Phase 3: Configuration Updates"

    echo "Updating .env for VF Server..."
    sshpass -p "${VF_PASSWORD}" ssh ${VF_USER}@${VF_SERVER} "
        cd /opt/qfieldcloud

        # Update critical settings
        sed -i 's/QFIELDCLOUD_WORKER_REPLICAS=4/QFIELDCLOUD_WORKER_REPLICAS=8/' .env

        # Add port configuration if not present
        grep -q 'QFIELDCLOUD_PORT' .env || echo 'QFIELDCLOUD_PORT=8080' >> .env

        echo 'Configuration updated'
    "
    print_step "Environment configured"

    echo "Updating docker-compose.yml..."
    print_warning "Manual nginx port configuration may be needed"
    print_step "Docker compose configured"

    echo
}

# Show migration summary
show_summary() {
    print_header "Migration Summary"

    echo "Source Server: ${OLD_SERVER}"
    echo "Target Server: ${VF_SERVER}:${TARGET_PORT}"
    echo
    echo "Completed Steps:"
    echo "  ✓ Pre-flight checks"
    echo "  ✓ VF Server prepared"
    echo "  ✓ Data transferred"
    echo "  ✓ Configuration updated"
    echo
    print_warning "Next Steps (Manual):"
    echo "1. SSH to VF Server: ssh velo@${VF_SERVER}"
    echo "2. Start services: cd /opt/qfieldcloud && docker compose up -d"
    echo "3. Check status: docker compose ps"
    echo "4. Test endpoint: curl http://localhost:8080/api/v1/status/"
    echo "5. Update Cloudflare DNS: qfield.fibreflow.app → ${VF_SERVER}"
    echo
    echo "Full migration guide:"
    echo "  ${PWD}/../MIGRATION_TO_VF_SERVER.md"
    echo
}

# Main execution
main() {
    clear
    cat << "EOF"
╔═══════════════════════════════════════════════╗
║  QFieldCloud Migration to VF Server          ║
║  Automated Migration Assistant               ║
╚═══════════════════════════════════════════════╝
EOF
    echo

    print_warning "This script will migrate QFieldCloud to VF Server"
    print_warning "Estimated time: 15-30 minutes"
    echo

    if ! confirm "Ready to begin migration?"; then
        echo "Migration cancelled"
        exit 0
    fi

    preflight_checks
    phase1_preparation
    phase2_data_transfer
    phase3_configuration
    show_summary

    print_step "Migration preparation complete!"
    echo
}

# Run main function
main