#!/bin/bash
# Professional deployment workflow for FibreFlow

set -e  # Exit on error

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

function show_help() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🚀 FIBREFLOW DEPLOYMENT WORKFLOW"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "USAGE: ./deploy-workflow.sh [COMMAND]"
    echo ""
    echo "COMMANDS:"
    echo "  staging    - Deploy to VF Server (test environment)"
    echo "  production - Deploy to Hostinger (public app)"
    echo "  docs       - Sync documentation to both servers"
    echo "  status     - Check both servers' status"
    echo "  help       - Show this help"
    echo ""
    echo "WORKFLOW:"
    echo "  1. Develop locally"
    echo "  2. ./deploy-workflow.sh staging  (test on VF)"
    echo "  3. Test at http://100.96.203.105:3005"
    echo "  4. ./deploy-workflow.sh production (go live)"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

function deploy_staging() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}📦 DEPLOYING TO VF SERVER (STAGING)${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # Sync all files to VF Server
    echo -e "${YELLOW}📤 Syncing files to VF Server...${NC}"
    rsync -avz \
        --exclude node_modules \
        --exclude .next \
        --exclude .git \
        --exclude .env \
        -e "ssh -o StrictHostKeyChecking=no" \
        ./ louis@100.96.203.105:/srv/data/apps/fibreflow/

    # Build and restart on VF Server
    echo -e "${YELLOW}🔨 Building and restarting...${NC}"
    ssh louis@100.96.203.105 "cd /srv/data/apps/fibreflow && npm install && npm run build && sudo systemctl restart fibreflow"

    # Check status
    sleep 3
    ssh louis@100.96.203.105 "systemctl is-active fibreflow"

    echo -e "${GREEN}✅ Staging deployment complete!${NC}"
    echo -e "${GREEN}🌐 Test at: http://100.96.203.105:3005${NC}"
    echo ""
    echo -e "${YELLOW}After testing, deploy to production with:${NC}"
    echo "   ./deploy-workflow.sh production"
}

function deploy_production() {
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}🚀 DEPLOYING TO HOSTINGER (PRODUCTION)${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # Confirm deployment
    echo -e "${YELLOW}⚠️  This will deploy to PRODUCTION (app.fibreflow.app)${NC}"
    read -p "Have you tested on staging? (y/N): " confirm
    if [[ $confirm != [yY] ]]; then
        echo -e "${RED}❌ Deployment cancelled${NC}"
        exit 1
    fi

    # Check staging status first
    echo -e "${YELLOW}🔍 Checking staging server status...${NC}"
    staging_status=$(ssh louis@100.96.203.105 "systemctl is-active fibreflow" 2>/dev/null || echo "inactive")
    if [[ $staging_status != "active" ]]; then
        echo -e "${RED}⚠️  Warning: Staging server is not active!${NC}"
        read -p "Continue anyway? (y/N): " force
        if [[ $force != [yY] ]]; then
            echo -e "${RED}❌ Deployment cancelled${NC}"
            exit 1
        fi
    fi

    # Deploy to Hostinger
    echo -e "${YELLOW}📤 Deploying to Hostinger...${NC}"
    ./sync-to-hostinger --code --restart

    # Verify deployment
    sleep 5
    echo -e "${YELLOW}🔍 Verifying production...${NC}"
    response=$(curl -s -o /dev/null -w "%{http_code}" https://app.fibreflow.app)

    if [[ $response == "200" ]]; then
        echo -e "${GREEN}✅ Production deployment successful!${NC}"
        echo -e "${GREEN}🌐 Live at: https://app.fibreflow.app${NC}"
    else
        echo -e "${RED}⚠️  Warning: Site returned HTTP $response${NC}"
        echo "Check manually: https://app.fibreflow.app"
    fi
}

function sync_docs() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}📚 SYNCING DOCUMENTATION ONLY${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    echo -e "${YELLOW}📤 Syncing to VF Server...${NC}"
    scp -q CLAUDE.md docs/*.md louis@100.96.203.105:/srv/data/apps/fibreflow/docs/ 2>/dev/null

    echo -e "${YELLOW}📤 Syncing to Hostinger...${NC}"
    ./sync-to-hostinger

    echo -e "${GREEN}✅ Documentation synced to both servers!${NC}"
}

function check_status() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}📊 SERVER STATUS CHECK${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    echo -e "\n${YELLOW}VF SERVER (Staging):${NC}"
    vf_status=$(ssh louis@100.96.203.105 "systemctl is-active fibreflow" 2>/dev/null || echo "error")
    vf_response=$(curl -s -o /dev/null -w "%{http_code}" http://100.96.203.105:3005 2>/dev/null || echo "000")

    if [[ $vf_status == "active" ]]; then
        echo -e "  Service: ${GREEN}● Active${NC}"
    else
        echo -e "  Service: ${RED}● $vf_status${NC}"
    fi
    echo -e "  HTTP: $vf_response"
    echo -e "  URL: http://100.96.203.105:3005"

    echo -e "\n${YELLOW}HOSTINGER (Production):${NC}"
    host_response=$(curl -s -o /dev/null -w "%{http_code}" https://app.fibreflow.app 2>/dev/null || echo "000")

    if [[ $host_response == "200" ]]; then
        echo -e "  HTTP: ${GREEN}$host_response ✓${NC}"
    else
        echo -e "  HTTP: ${RED}$host_response ✗${NC}"
    fi
    echo -e "  URL: https://app.fibreflow.app"

    # Quick PM2 check
    pm2_status=$(HOSTINGER_PASSWORD="VeloF@2025@@" .claude/skills/hostinger-vps/scripts/execute.py "pm2 list | grep fibreflow-prod | awk '{print \$10}'" 2>/dev/null | grep -o "online\|stopped" || echo "unknown")
    echo -e "  PM2: $pm2_status"

    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Main logic
case "$1" in
    staging)
        deploy_staging
        ;;
    production|prod)
        deploy_production
        ;;
    docs)
        sync_docs
        ;;
    status)
        check_status
        ;;
    help|--help|-h|"")
        show_help
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        show_help
        exit 1
        ;;
esac