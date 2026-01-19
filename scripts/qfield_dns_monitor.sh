#!/bin/bash
# QFieldCloud DNS Propagation Monitor
# Deploy to: ~/qfieldcloud/scripts/dns_monitor.sh

echo "==================================="
echo "QFieldCloud DNS Monitor"
echo "Checking: qfield.fibreflow.app"
echo "==================================="
echo ""

# DNS Lookup
echo "=== DNS Resolution ==="
DNS_RESULT=$(dig +short qfield.fibreflow.app @8.8.8.8 2>/dev/null)

if [ -z "$DNS_RESULT" ]; then
    echo "⚠️  DNS not yet propagated (no results)"
    echo "   Expected: CNAME vf-downloads.cfargotunnel.com"
    echo "   Status: Waiting for Cloudflare propagation (5-60 min)"
else
    echo "✅ DNS resolved:"
    echo "$DNS_RESULT" | while read line; do echo "   $line"; done

    # Check if it's the tunnel CNAME
    if echo "$DNS_RESULT" | grep -q "cfargotunnel.com"; then
        echo ""
        echo "✅ Correct CNAME (Cloudflare Tunnel)"
    fi
fi

echo ""
echo "=== HTTP Test ==="
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -m 10 https://qfield.fibreflow.app 2>&1)

if [ "$HTTP_STATUS" = "302" ] || [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ Public URL working (HTTP $HTTP_STATUS)"
    echo "   https://qfield.fibreflow.app"
    echo ""
    echo "🎉 MIGRATION COMPLETE - DNS LIVE!"
elif [ "$HTTP_STATUS" = "000" ] || echo "$HTTP_STATUS" | grep -q "Could not resolve"; then
    echo "⏳ DNS not propagated yet"
    echo "   Estimated time: 5-60 minutes"
elif [ "$HTTP_STATUS" = "502" ]; then
    echo "⚠️  DNS propagated but tunnel/app not responding"
    echo "   Check: ~/qfieldcloud/scripts/health_check.sh"
else
    echo "⚠️  Unexpected status: $HTTP_STATUS"
fi

echo ""
echo "=== Next Steps ==="
if [ "$HTTP_STATUS" = "302" ] || [ "$HTTP_STATUS" = "200" ]; then
    echo "1. Test with QField mobile app"
    echo "2. Validate projects and data"
    echo "3. Monitor for 24-48 hours"
    echo "4. Decommission Hostinger VPS"
else
    echo "1. Wait for DNS propagation"
    echo "2. Re-run this script: ~/qfieldcloud/scripts/dns_monitor.sh"
    echo "3. Check health: ~/qfieldcloud/scripts/health_check.sh"
fi

echo "==================================="
