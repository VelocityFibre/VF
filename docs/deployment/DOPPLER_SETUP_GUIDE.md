# 🚀 Doppler Setup Guide for FibreFlow

**Status**: ✅ **SETUP COMPLETE** (2026-01-07)
- ✅ Doppler CLI v3.75.1 installed
- ✅ Authenticated and logged in
- ✅ Project "fibreflow" created
- ✅ 11 secrets uploaded successfully
- ✅ Tested and working

**Dashboard**: https://dashboard.doppler.com
**Project**: fibreflow (dev config)

---

## Quick Setup (5 Minutes)

### 1️⃣ Install Doppler CLI

**On macOS:**
```bash
brew install dopplerhq/cli/doppler
```

**On Linux/WSL:**
```bash
# Debian/Ubuntu
sudo apt-get update && sudo apt-get install -y apt-transport-https ca-certificates curl gnupg
curl -sLf --retry 3 --tlsv1.2 --proto "=https" 'https://packages.doppler.com/public/cli/gpg.DE2A7741A397C129.key' | sudo apt-key add -
echo "deb https://packages.doppler.com/public/cli/deb/debian any-version main" | sudo tee /etc/apt/sources.list.d/doppler-cli.list
sudo apt-get update && sudo apt-get install doppler
```

**Or use their installer:**
```bash
curl -Ls --tlsv1.2 --proto "=https" --retry 3 https://cli.doppler.com/install.sh | sh
```

### 2️⃣ Create Doppler Account

1. Go to: https://www.doppler.com
2. Click "Start for Free"
3. Sign up with email or GitHub
4. Verify your email

### 3️⃣ Login to Doppler

```bash
doppler login
```
This opens your browser to authenticate.

### 4️⃣ Setup FibreFlow Project

```bash
# Navigate to your project
cd ~/fibreflow-louis  # or wherever your project is

# Initialize Doppler
doppler setup

# When prompted:
# - Create new project: "fibreflow"
# - Select config: "dev" for development
```

### 5️⃣ Upload Your Existing Secrets

```bash
# Option A: Upload your .env.local file
doppler secrets upload .env.local

# Option B: Add manually in dashboard
# Go to: https://dashboard.doppler.com
# Click your project → Add secrets
```

### 6️⃣ Test It Works

```bash
# Run your app with Doppler
doppler run -- npm run dev

# Your app should start with all secrets injected!
```

## For Team Collaboration

### Invite Hein:

1. Go to: https://dashboard.doppler.com
2. Click "Team" in sidebar
3. Click "Invite teammate"
4. Enter Hein's email
5. Select role: "Developer"

### Hein's Setup (2 minutes):

```bash
# 1. Install Doppler
brew install dopplerhq/cli/doppler  # or Linux command

# 2. Login
doppler login

# 3. Setup project
cd ~/fibreflow-louis
doppler setup
# Select existing project: "fibreflow"

# 4. Run
doppler run -- npm run dev
# All secrets automatically available!
```

## Your Secrets to Add

```env
# These are your Clerk keys to add to Doppler:
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_Y3JlYXRpdmUtY29yYWwtODIuY2xlcmsuYWNjb3VudHMuZGV2JA
CLERK_SECRET_KEY=sk_test_VVLQUws0JUO6maeBv9KycImwmHmxhtP9F3KiLCSljS
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/ticketing
NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/ticketing

# Any other secrets from your .env.local
DATABASE_URL=your_database_url
# etc...
```

## Benefits You Get Immediately

✅ **No More Git Blocks**: Commit your code without secrets
✅ **Team Sync**: Hein gets updates instantly
✅ **Multiple Environments**: dev, staging, production configs
✅ **Version History**: See who changed what and when
✅ **Secure**: Encrypted, audited, SOC 2 compliant

## Common Commands

```bash
# View all secrets
doppler secrets

# Download as .env file
doppler secrets download --no-file --format env

# Add a new secret
doppler secrets set API_KEY "new_value"

# Run any command with secrets
doppler run -- [your command]
doppler run -- npm run dev
doppler run -- npm run build
doppler run -- npm test
```

## Integrations

### GitHub Actions
```yaml
- name: Install Doppler CLI
  uses: dopplerhq/cli-action@v3

- name: Run with secrets
  run: doppler run -- npm run build
  env:
    DOPPLER_TOKEN: ${{ secrets.DOPPLER_TOKEN }}
```

### Vercel Deployment
1. Install Vercel integration in Doppler
2. Select your project
3. Secrets auto-sync to Vercel

## Troubleshooting

**"doppler: command not found"**
- Restart terminal after installation
- Or add to PATH: `export PATH="$HOME/.doppler/bin:$PATH"`

**"Not authorized"**
- Run `doppler login` again
- Check you're in the right project: `doppler setup`

**"Config not found"**
- Run `doppler setup` in your project directory
- Select the right environment (dev/staging/prod)

## Next Steps

1. ✅ Install Doppler (you) - **COMPLETE** (v3.75.1)
2. ✅ Upload your secrets - **COMPLETE** (11 secrets uploaded)
3. ✅ Test it works - **COMPLETE** (tested with `doppler run -- printenv`)
4. ⬜ Invite Hein - See instructions above
5. ⬜ Remove .env.local from staging server (optional)
6. ✅ Use Doppler for all projects - **READY** (run `doppler run -- npm run dev`)

---

**Support**: https://docs.doppler.com
**Dashboard**: https://dashboard.doppler.com
**Free for up to 5 users!**