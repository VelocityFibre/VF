---
name: port-manager
description: Manage ports and services on VF server
version: 1.0.0
author: Claude
tags:
  - infrastructure
  - debugging
  - server-management
dependencies:
  - bash
  - lsof
  - ss
  - systemctl
---

# Port Manager Skill

Intelligent port management for VF server to prevent conflicts and manage services.

## Available Scripts

### Check Port Status
```bash
.claude/skills/port-manager/scripts/check_port.py [PORT]
```
Shows what's using a specific port with process details.

### Restart FibreFlow
```bash
.claude/skills/port-manager/scripts/restart_fibreflow.py
```
Safely restarts FibreFlow on port 3005, handling multiple instances.

### List All Services
```bash
.claude/skills/port-manager/scripts/list_services.py
```
Lists all services and their ports on the server.

## Common Ports

- **3000**: Development Next.js instances
- **3005**: FibreFlow production
- **8000**: FastAPI services
- **8001**: WhatsApp sender / API services
- **8080**: Alternative web services
- **8081**: WhatsApp sender service
- **8100**: Qwen VLM service

## Features

- Identifies process owner (user)
- Shows PID for targeted kills
- Handles multiple instances gracefully
- Ensures clean restarts
- Validates service status after restart