#!/bin/bash
# Setup Limited Sudo for velo user
# Run this ON THE VF SERVER as root

cat << 'EOF'
=== Limited Sudo Setup Script ===

This script will configure limited sudo access for the velo user.
The velo user will be able to:
  ✅ Check service status
  ✅ View logs
  ✅ Monitor processes
  ❌ But NOT restart/stop services or run destructive commands

Run this script ON THE VF SERVER as root:

ssh -i ~/.ssh/vf_server_key louis@100.96.203.105
sudo su -

Then paste this:

cat > /etc/sudoers.d/velo-readonly << 'SUDOERS'
# Limited sudo access for velo user (Claude Code read-only)
# Created: 2026-01-14
# Purpose: Allow monitoring without destructive capabilities

# Monitoring commands - NO PASSWORD REQUIRED
velo ALL=(ALL) NOPASSWD: /usr/bin/systemctl status *
velo ALL=(ALL) NOPASSWD: /usr/bin/systemctl list-units
velo ALL=(ALL) NOPASSWD: /usr/bin/journalctl *
velo ALL=(ALL) NOPASSWD: /usr/bin/docker ps
velo ALL=(ALL) NOPASSWD: /usr/bin/docker logs *
velo ALL=(ALL) NOPASSWD: /usr/bin/docker inspect *
velo ALL=(ALL) NOPASSWD: /usr/bin/ps *
velo ALL=(ALL) NOPASSWD: /usr/bin/top
velo ALL=(ALL) NOPASSWD: /usr/bin/htop
velo ALL=(ALL) NOPASSWD: /usr/bin/netstat *
velo ALL=(ALL) NOPASSWD: /usr/bin/ss *
velo ALL=(ALL) NOPASSWD: /usr/bin/lsof *
velo ALL=(ALL) NOPASSWD: /usr/bin/df *
velo ALL=(ALL) NOPASSWD: /usr/bin/free *
velo ALL=(ALL) NOPASSWD: /usr/bin/tail -f /var/log/*
velo ALL=(ALL) NOPASSWD: /usr/bin/cat /var/log/*
velo ALL=(ALL) NOPASSWD: /usr/bin/grep * /var/log/*
velo ALL=(ALL) NOPASSWD: /usr/bin/zgrep * /var/log/*

# Explicitly DENY dangerous commands (defense in depth)
velo ALL=(ALL) !ALL: /usr/bin/systemctl restart *
velo ALL=(ALL) !ALL: /usr/bin/systemctl stop *
velo ALL=(ALL) !ALL: /usr/bin/systemctl start *
velo ALL=(ALL) !ALL: /usr/bin/kill *
velo ALL=(ALL) !ALL: /usr/bin/killall *
velo ALL=(ALL) !ALL: /usr/bin/pkill *
velo ALL=(ALL) !ALL: /bin/rm *
velo ALL=(ALL) !ALL: /usr/bin/passwd *
velo ALL=(ALL) !ALL: /usr/bin/apt *
velo ALL=(ALL) !ALL: /usr/bin/apt-get *
velo ALL=(ALL) !ALL: /usr/sbin/reboot
velo ALL=(ALL) !ALL: /usr/sbin/shutdown
SUDOERS

# Set correct permissions
chmod 0440 /etc/sudoers.d/velo-readonly

# Validate sudoers file
visudo -c -f /etc/sudoers.d/velo-readonly

echo "✅ Limited sudo configured for velo user"
echo ""
echo "Test with:"
echo "  su - velo"
echo "  sudo systemctl status nginx  # Should work"
echo "  sudo systemctl restart nginx # Should be denied"
EOF