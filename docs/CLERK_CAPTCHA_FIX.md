# Clerk CAPTCHA Error Fix

## Quick Fix: Disable CAPTCHA for Testing

1. Go to Clerk Dashboard: https://dashboard.clerk.com
2. Navigate to: **User & Authentication** → **Attack Protection**
3. Find **Bot Protection**
4. Toggle OFF: **Enable bot protection**
5. Save changes

## Alternative Solutions

### If You Need CAPTCHA Enabled:

1. **Try Different Browser**:
   - Chrome (without extensions)
   - Firefox Private Window
   - Safari
   - Edge

2. **Disable Browser Extensions**:
   - Ad blockers (uBlock, AdBlock)
   - Privacy extensions (Privacy Badger, Ghostery)
   - Script blockers (NoScript)
   - VPN extensions

3. **Browser Settings**:
   - Allow third-party cookies
   - Disable "Enhanced Tracking Protection"
   - Allow JavaScript from all sources

4. **Whitelist Domains**:
   Add to your ad blocker whitelist:
   - *.clerk.accounts.dev
   - *.clerk.com
   - *.hcaptcha.com
   - creative-coral-82.clerk.accounts.dev

## For Production

Configure custom domain in Clerk:
1. Dashboard → Settings → Domains
2. Add your domain: vf.fibreflow.app
3. Follow DNS verification steps