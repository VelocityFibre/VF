#!/usr/bin/env python3
"""
Simple server to test voice agent with proper token generation
"""
import os
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from livekit import api
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

LIVEKIT_URL = os.getenv('LIVEKIT_URL', 'ws://72.60.17.245:7880')
LIVEKIT_API_KEY = os.getenv('LIVEKIT_API_KEY', 'APIff886cece0')
LIVEKIT_API_SECRET = os.getenv('LIVEKIT_API_SECRET', '27c545b4fe6bfbb5b76032de807360ed676be49fa743ce625d230417faf86698')

@app.route('/')
def index():
    """Serve the test page"""
    return send_from_directory('.', 'test_voice_agent_simple.html')

@app.route('/token')
def get_token():
    """Generate a LiveKit access token"""
    try:
        # Generate random identity
        import secrets
        identity = f"user-{secrets.token_hex(4)}"
        room_name = f"test-room-{secrets.token_hex(4)}"

        # Create access token
        token = api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        token.with_identity(identity)
        token.with_name(identity)
        token.with_grants(api.VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True,
        ))

        jwt = token.to_jwt()

        return jsonify({
            'token': jwt,
            'url': LIVEKIT_URL,
            'room': room_name,
            'identity': identity
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting test server on http://localhost:5001")
    print("📖 Open http://localhost:5001 in your browser to test")
    app.run(host='0.0.0.0', port=5001, debug=False)
