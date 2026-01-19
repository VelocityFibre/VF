# Voice Agent Setup Guide

This guide will help you set up voice interaction with FibreFlow using Grok's realtime API via LiveKit.

## Quick Start for FibreFlow

**FibreFlow has LiveKit already running on the Hostinger VPS!** 🎉

You only need to get the xAI API key. LiveKit credentials are already in `.env`:

```bash
# 1. Get xAI API key from: https://x.ai/api
# 2. Add to .env:
XAI_API_KEY=xai-your-key-here

# 3. Run voice agent (LiveKit already configured!)
./venv/bin/python3 voice_agent_grok.py
```

**Self-Hosted LiveKit Details:**
- Server: `72.60.17.245:7880` (Hostinger VPS)
- WebSocket: `ws://72.60.17.245:7880` (API access)
- Client URL: `wss://app.fibreflow.app/livekit-ws/` (browser access)
- Config: `/opt/livekit/config.yaml` on VPS
- Redis: `localhost:6379` (for state)
- Egress: Enabled (for recordings)

**Benefit**: No usage fees, full control, already integrated with FibreFlow!

---

## Full Setup Guide (For Other Projects)

**Total setup time**: ~10 minutes

```bash
# 1. Already installed dependencies (livekit-agents with xAI)
# 2. Get API keys (see below)
# 3. Add keys to .env
# 4. Run the voice agent
./venv/bin/python3 voice_agent_grok.py
```

## Step 1: Get xAI API Key

1. Go to **https://x.ai/api**
2. Sign in with your X (Twitter) account
3. Click "Get API Key" or navigate to API settings
4. Copy your API key (starts with `xai-...`)
5. Add to `.env`:
   ```bash
   XAI_API_KEY=xai-your-key-here
   ```

**Pricing**: Check https://x.ai/api for current pricing

## Step 2: Get LiveKit Credentials

LiveKit provides the WebRTC infrastructure for voice communication.

### Option A: LiveKit Cloud (Recommended - Free Tier)

1. Go to **https://cloud.livekit.io**
2. Sign up for free account
3. Create a new project
4. Navigate to **Settings** → **Keys**
5. Copy your credentials:
   - WebSocket URL (e.g., `wss://your-project.livekit.cloud`)
   - API Key
   - API Secret

6. Add to `.env`:
   ```bash
   LIVEKIT_URL=wss://your-project.livekit.cloud
   LIVEKIT_API_KEY=your-api-key
   LIVEKIT_API_SECRET=your-api-secret
   ```

**Free Tier**: 50GB bandwidth/month, unlimited development usage

### Option B: Self-Hosted LiveKit (Advanced)

If you want full control, you can deploy LiveKit on your VPS:

```bash
# Install LiveKit server (requires Docker)
docker pull livekit/livekit-server
docker run -p 7880:7880 -p 7881:7881 -p 7882:7882/udp \
  -v $PWD/livekit.yaml:/livekit.yaml \
  livekit/livekit-server --config /livekit.yaml
```

See https://docs.livekit.io/home/self-hosting/deployment/ for details.

## Step 3: Update Your .env File

Your `.env` should now have:

```bash
# xAI Grok Configuration
XAI_API_KEY=xai-your-actual-key-here

# LiveKit Configuration
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your-actual-api-key
LIVEKIT_API_SECRET=your-actual-api-secret
```

## Step 4: Run the Voice Agent

```bash
# Activate virtual environment
source venv/bin/activate

# Run voice agent
python voice_agent_grok.py
```

You should see:
```
🚀 Starting Grok Voice Agent...
   Room URL: wss://your-project.livekit.cloud
✅ Connected to room: your-room-name
🎙️  Voice agent ready - speak to interact!
```

## Testing the Voice Agent

### Option A: LiveKit Playground (Easiest)

1. Go to your LiveKit Cloud dashboard
2. Click **Rooms** → **Create Room**
3. Join the room from your browser
4. Start speaking - Grok will respond!

### Option B: Build a Web UI

Create a simple HTML page to connect to your LiveKit room:

```html
<!DOCTYPE html>
<html>
<head>
    <title>FibreFlow Voice Agent</title>
    <script src="https://unpkg.com/livekit-client@latest"></script>
</head>
<body>
    <h1>FibreFlow Voice Assistant</h1>
    <button id="connect">Start Talking</button>
    <div id="status"></div>

    <script>
        // Connection code here (see LiveKit docs)
    </script>
</body>
</html>
```

### Option C: Use LiveKit CLI

```bash
# Install LiveKit CLI
npm install -g livekit-cli

# Join room and test
lk room join --url wss://your-project.livekit.cloud \
  --api-key your-api-key \
  --api-secret your-api-secret
```

## Architecture

```
User (Browser/Phone)
    ↓ WebRTC Audio
LiveKit Server
    ↓ Audio Stream
Voice Agent (voice_agent_grok.py)
    ↓ Speech-to-Speech
Grok Realtime API (xAI)
    ↓ Response
Voice Agent
    ↓ WebRTC Audio
User
```

**Key Points**:
- **Single API**: Grok handles speech-to-text, reasoning, and text-to-speech internally
- **Low Latency**: ~200ms typical response time
- **No Pipeline**: Unlike Claude (which needs STT→LLM→TTS), Grok is all-in-one

## Adding FibreFlow Agent Tools

You can make the voice agent call your existing FibreFlow agents as tools:

```python
from agents.neon_database.neon_agent import NeonAgent

async def query_database(query: str) -> str:
    """Query FibreFlow database via voice"""
    neon_agent = NeonAgent(os.getenv("ANTHROPIC_API_KEY"))
    result = await neon_agent.execute_tool("execute_query", {"query": query})
    return result

# Add to agent definition
agent = Agent(
    instructions="...",
    tools=[query_database],  # Now voice agent can access database!
)
```

## Troubleshooting

### "Missing required environment variables"

Make sure your `.env` file has all four variables:
```bash
XAI_API_KEY=xai-...
LIVEKIT_URL=wss://...
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...
```

Run `cat .env | grep -E "XAI|LIVEKIT"` to verify.

### "Connection refused" or "WebSocket error"

Check your LiveKit URL format:
- ✅ Correct: `wss://your-project.livekit.cloud`
- ❌ Wrong: `https://your-project.livekit.cloud` (should be wss://)
- ❌ Wrong: `your-project.livekit.cloud` (missing wss://)

### "xAI API authentication failed"

1. Verify your API key is correct: https://x.ai/api
2. Check key starts with `xai-`
3. Ensure no extra spaces in `.env` file

### Voice not working in browser

Modern browsers require HTTPS for microphone access:
- Use LiveKit Cloud (has HTTPS built-in)
- Or set up SSL certificate for self-hosted

## Cost Estimation

**For 1000 voice interactions (~5 min each = 5000 minutes total)**:

| Component | Provider | Est. Cost |
|-----------|----------|-----------|
| Grok Realtime | xAI | ~$50-100* |
| LiveKit | Cloud Free Tier | $0 |
| **Total** | | **$50-100/month** |

*Pricing TBD - check https://x.ai/api for current rates

**Compare to Claude Pipeline**:
- Claude pipeline: ~$45-55/month (STT + LLM + TTS)
- Grok realtime: ~$50-100/month (all-in-one)

## Switching to Claude Pipeline

If you need Claude's better reasoning, see `voice_agent_claude.py` (not yet created).

Claude pipeline is more complex but gives you:
- Better reasoning for technical questions
- Same context/memory as your existing agents
- Ability to fine-tune each component (STT, LLM, TTS)

## Next Steps

1. **Add tools** - Connect FibreFlow database, VPS monitoring, etc.
2. **Build web UI** - Create user-friendly interface
3. **Deploy to production** - Run on VPS, integrate with FibreFlow app
4. **Monitor usage** - Track costs, performance, user satisfaction

## Support

- **LiveKit Docs**: https://docs.livekit.io
- **xAI Docs**: https://x.ai/api/docs
- **LiveKit Discord**: https://livekit.io/discord
- **FibreFlow Issues**: Create issue in repo
