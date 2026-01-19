#!/bin/bash

# WhatsApp Express Microservice Deployment Script
# Port 8092 (avoiding conflict with drop-number-api on 8090)

echo "🚀 Deploying WhatsApp Express Microservice on Port 8092"

# Configuration
MICROSERVICE_PORT=8092
WHATSAPP_SENDER_URL="http://localhost:8081"
APP_DIR="/opt/whatsapp-express"  # Adjust path as needed

# 1. Check if port is available
if lsof -i :$MICROSERVICE_PORT > /dev/null 2>&1; then
    echo "❌ Port $MICROSERVICE_PORT is already in use!"
    echo "Current process using port:"
    lsof -i :$MICROSERVICE_PORT
    exit 1
fi

echo "✅ Port $MICROSERVICE_PORT is available"

# 2. Create Express microservice (if not exists)
if [ ! -d "$APP_DIR" ]; then
    echo "📁 Creating WhatsApp Express microservice..."
    mkdir -p $APP_DIR
    cd $APP_DIR

    # Initialize package.json
    cat > package.json << 'EOF'
{
  "name": "whatsapp-express-microservice",
  "version": "1.0.0",
  "description": "Express middleware for WhatsApp feedback integration",
  "main": "server.js",
  "scripts": {
    "start": "node server.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "cors": "^2.8.5",
    "axios": "^1.6.0",
    "dotenv": "^16.0.3"
  }
}
EOF

    # Create server.js
    cat > server.js << 'EOF'
const express = require('express');
const cors = require('cors');
const axios = require('axios');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 8092;
const WHATSAPP_SENDER_URL = process.env.WHATSAPP_SENDER_URL || 'http://localhost:8081';

app.use(cors());
app.use(express.json());

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ status: 'healthy', port: PORT, sender: WHATSAPP_SENDER_URL });
});

// Send WhatsApp message endpoint
app.post('/send-feedback', async (req, res) => {
    try {
        const { phone, message, jobId } = req.body;

        if (!phone || !message) {
            return res.status(400).json({ error: 'Phone and message are required' });
        }

        // Forward to WhatsApp Sender
        const response = await axios.post(`${WHATSAPP_SENDER_URL}/send`, {
            phone: phone.replace(/\D/g, ''), // Remove non-digits
            message: message
        });

        res.json({
            success: true,
            messageId: response.data.messageId,
            jobId: jobId
        });
    } catch (error) {
        console.error('Error sending WhatsApp message:', error.message);
        res.status(500).json({
            error: 'Failed to send WhatsApp message',
            details: error.message
        });
    }
});

// List messages endpoint (for debugging)
app.get('/messages', async (req, res) => {
    try {
        const response = await axios.get(`${WHATSAPP_SENDER_URL}/messages`);
        res.json(response.data);
    } catch (error) {
        res.status(500).json({ error: 'Failed to fetch messages' });
    }
});

app.listen(PORT, () => {
    console.log(`✅ WhatsApp Express Microservice running on port ${PORT}`);
    console.log(`   Sender URL: ${WHATSAPP_SENDER_URL}`);
});
EOF

    # Create .env file
    cat > .env << EOF
PORT=$MICROSERVICE_PORT
WHATSAPP_SENDER_URL=$WHATSAPP_SENDER_URL
EOF

    # Install dependencies
    echo "📦 Installing dependencies..."
    npm install
fi

# 3. Start the microservice
cd $APP_DIR
echo "🚀 Starting WhatsApp Express Microservice..."
nohup npm start > whatsapp-express.log 2>&1 &
MICROSERVICE_PID=$!

# 4. Wait and verify
sleep 3
if lsof -i :$MICROSERVICE_PORT > /dev/null 2>&1; then
    echo "✅ WhatsApp Express Microservice is running on port $MICROSERVICE_PORT"
    echo "   PID: $MICROSERVICE_PID"
    echo "   Logs: $APP_DIR/whatsapp-express.log"

    # Test health endpoint
    echo "🔍 Testing health endpoint..."
    curl -s http://localhost:$MICROSERVICE_PORT/health | jq .

    echo ""
    echo "📝 Next Steps:"
    echo "1. Update your app's .env file:"
    echo "   WHATSAPP_MICROSERVICE_URL=http://localhost:$MICROSERVICE_PORT"
    echo ""
    echo "2. Restart your staging app:"
    echo "   cd /path/to/staging/app && npm run build && npm start"
    echo ""
    echo "3. Test the integration:"
    echo "   curl -X POST http://localhost:$MICROSERVICE_PORT/send-feedback \\"
    echo "     -H 'Content-Type: application/json' \\"
    echo "     -d '{\"phone\": \"+27711558396\", \"message\": \"Test feedback\"}'"
else
    echo "❌ Failed to start WhatsApp Express Microservice"
    echo "Check logs at: $APP_DIR/whatsapp-express.log"
    exit 1
fi