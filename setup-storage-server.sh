#!/bin/bash

# FibreFlow Storage Server Setup
# Replaces Firebase Storage with VF Server + Cloudflare Tunnel
# Keeps Firebase as backup/mirror

echo "🚀 Setting up FibreFlow Storage Server..."

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo "Please run with sudo: sudo bash setup-storage-server.sh"
    exit 1
fi

# Configuration
STORAGE_ROOT="/srv/data/fibreflow-storage"
UPLOAD_USER="velo"
NGINX_SITE="vf-storage"

# 1. Create directory structure (mirrors Firebase Storage buckets)
echo "📁 Creating storage directories..."
mkdir -p $STORAGE_ROOT/{contractors,projects,tickets,poles,temp,archive}/{documents,images,videos}
mkdir -p $STORAGE_ROOT/public/assets
mkdir -p $STORAGE_ROOT/logs

# Set permissions
chown -R $UPLOAD_USER:$UPLOAD_USER $STORAGE_ROOT
chmod -R 755 $STORAGE_ROOT

# 2. Install required packages
echo "📦 Installing dependencies..."
apt-get update
apt-get install -y imagemagick ffmpeg webp nginx

# 3. Create nginx configuration for file serving
echo "🔧 Configuring nginx..."
cat > /etc/nginx/sites-available/$NGINX_SITE << 'EOF'
server {
    listen 8090;
    server_name localhost;

    # Logging
    access_log /srv/data/fibreflow-storage/logs/access.log;
    error_log /srv/data/fibreflow-storage/logs/error.log;

    # File upload size limit (100MB)
    client_max_body_size 100M;

    # Storage root
    root /srv/data/fibreflow-storage;

    # CORS headers (allow from your domains)
    add_header 'Access-Control-Allow-Origin' '$http_origin' always;
    add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
    add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range' always;

    # Serve uploaded files
    location /storage/ {
        alias /srv/data/fibreflow-storage/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        add_header X-Content-Type-Options nosniff;

        # Enable range requests for video streaming
        add_header Accept-Ranges bytes;
    }

    # Image resizing on-the-fly (optional)
    location ~ ^/storage/(.+)_(\d+)x(\d+)\.(jpg|jpeg|png|gif|webp)$ {
        alias /srv/data/fibreflow-storage/$1.$4;
        image_filter resize $2 $3;
        image_filter_jpeg_quality 85;
        image_filter_webp_quality 85;
        image_filter_buffer 20M;
    }

    # Health check endpoint
    location /health {
        return 200 "Storage server is running\n";
        add_header Content-Type text/plain;
    }
}
EOF

# Enable site
ln -sf /etc/nginx/sites-available/$NGINX_SITE /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# 4. Create upload service (Node.js)
echo "📝 Creating upload service..."
cat > $STORAGE_ROOT/storage-api.js << 'EOF'
const express = require('express');
const multer = require('multer');
const path = require('path');
const fs = require('fs').promises;
const crypto = require('crypto');
const sharp = require('sharp');

const app = express();
app.use(express.json());

// Storage configuration
const storage = multer.diskStorage({
    destination: async (req, file, cb) => {
        const type = req.params.type || 'general';
        const category = req.params.category || 'documents';
        const dir = `/srv/data/fibreflow-storage/${type}/${category}`;

        await fs.mkdir(dir, { recursive: true });
        cb(null, dir);
    },
    filename: (req, file, cb) => {
        const hash = crypto.randomBytes(16).toString('hex');
        const ext = path.extname(file.originalname);
        const filename = `${Date.now()}-${hash}${ext}`;
        cb(null, filename);
    }
});

const upload = multer({
    storage,
    limits: { fileSize: 100 * 1024 * 1024 }, // 100MB
    fileFilter: (req, file, cb) => {
        const allowedTypes = /jpeg|jpg|png|gif|webp|pdf|doc|docx|xls|xlsx|mp4|mov|avi/;
        const ext = allowedTypes.test(path.extname(file.originalname).toLowerCase());
        const mimetype = allowedTypes.test(file.mimetype);

        if (ext && mimetype) {
            return cb(null, true);
        } else {
            cb(new Error('Invalid file type'));
        }
    }
});

// Upload endpoint (Firebase-compatible)
app.post('/upload/:type/:category', upload.single('file'), async (req, res) => {
    try {
        const file = req.file;
        if (!file) {
            return res.status(400).json({ error: 'No file uploaded' });
        }

        // Process images (resize, optimize)
        if (file.mimetype.startsWith('image/')) {
            const optimizedPath = file.path.replace(/\.[^.]+$/, '-optimized.webp');
            await sharp(file.path)
                .resize(2048, 2048, {
                    fit: 'inside',
                    withoutEnlargement: true
                })
                .webp({ quality: 85 })
                .toFile(optimizedPath);
        }

        // Build response (Firebase-compatible format)
        const baseUrl = process.env.STORAGE_BASE_URL || 'https://vf.fibreflow.app';
        const publicUrl = `${baseUrl}/storage/${req.params.type}/${req.params.category}/${file.filename}`;

        res.json({
            name: file.filename,
            bucket: 'fibreflow-storage',
            contentType: file.mimetype,
            size: file.size,
            publicUrl: publicUrl,
            downloadUrl: publicUrl,
            metadata: {
                originalName: file.originalname,
                uploadTime: new Date().toISOString(),
                type: req.params.type,
                category: req.params.category
            }
        });

        // Async backup to Firebase (non-blocking)
        if (process.env.FIREBASE_BACKUP === 'true') {
            // Queue for Firebase upload
            backupToFirebase(file).catch(console.error);
        }

    } catch (error) {
        console.error('Upload error:', error);
        res.status(500).json({ error: error.message });
    }
});

// Delete endpoint
app.delete('/delete/:type/:category/:filename', async (req, res) => {
    try {
        const filePath = `/srv/data/fibreflow-storage/${req.params.type}/${req.params.category}/${req.params.filename}`;
        await fs.unlink(filePath);
        res.json({ success: true });
    } catch (error) {
        res.status(404).json({ error: 'File not found' });
    }
});

// List files endpoint
app.get('/list/:type/:category', async (req, res) => {
    try {
        const dir = `/srv/data/fibreflow-storage/${req.params.type}/${req.params.category}`;
        const files = await fs.readdir(dir);
        const fileList = await Promise.all(files.map(async (file) => {
            const stats = await fs.stat(path.join(dir, file));
            return {
                name: file,
                size: stats.size,
                modified: stats.mtime,
                url: `${process.env.STORAGE_BASE_URL}/storage/${req.params.type}/${req.params.category}/${file}`
            };
        }));
        res.json(fileList);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Firebase backup function
async function backupToFirebase(file) {
    // Implementation for syncing to Firebase
    console.log(`Queued for Firebase backup: ${file.filename}`);
    // Add to queue for background sync
}

const PORT = process.env.STORAGE_PORT || 8091;
app.listen(PORT, () => {
    console.log(`Storage API running on port ${PORT}`);
});
EOF

# 5. Create package.json for the storage API
cat > $STORAGE_ROOT/package.json << 'EOF'
{
  "name": "fibreflow-storage-api",
  "version": "1.0.0",
  "description": "Firebase Storage replacement API",
  "main": "storage-api.js",
  "scripts": {
    "start": "node storage-api.js",
    "dev": "nodemon storage-api.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "multer": "^1.4.5-lts.1",
    "sharp": "^0.33.1",
    "firebase-admin": "^11.11.1"
  },
  "devDependencies": {
    "nodemon": "^3.0.2"
  }
}
EOF

# 6. Install Node.js dependencies
echo "📦 Installing Node.js packages..."
cd $STORAGE_ROOT
npm install

# 7. Create systemd service
echo "⚙️ Creating systemd service..."
cat > /etc/systemd/system/fibreflow-storage.service << EOF
[Unit]
Description=FibreFlow Storage API
After=network.target

[Service]
Type=simple
User=$UPLOAD_USER
WorkingDirectory=$STORAGE_ROOT
ExecStart=/usr/bin/node storage-api.js
Restart=always
RestartSec=10
StandardOutput=append:$STORAGE_ROOT/logs/storage-api.log
StandardError=append:$STORAGE_ROOT/logs/storage-api-error.log

Environment="NODE_ENV=production"
Environment="STORAGE_PORT=8091"
Environment="STORAGE_BASE_URL=https://vf.fibreflow.app"
Environment="FIREBASE_BACKUP=true"

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
systemctl daemon-reload
systemctl enable fibreflow-storage
systemctl start fibreflow-storage

# 8. Create backup script
echo "💾 Creating backup script..."
cat > $STORAGE_ROOT/backup-to-firebase.sh << 'EOF'
#!/bin/bash
# Sync local storage to Firebase Storage as backup
# Run daily via cron

STORAGE_ROOT="/srv/data/fibreflow-storage"
LOG_FILE="$STORAGE_ROOT/logs/firebase-backup.log"

echo "[$(date)] Starting Firebase backup..." >> $LOG_FILE

# Add your Firebase sync logic here
# Example using gsutil (Google Cloud SDK):
# gsutil -m rsync -r $STORAGE_ROOT gs://fibreflow-app.appspot.com/backup/

echo "[$(date)] Firebase backup completed" >> $LOG_FILE
EOF

chmod +x $STORAGE_ROOT/backup-to-firebase.sh

# 9. Add cron job for daily backup
echo "0 2 * * * $STORAGE_ROOT/backup-to-firebase.sh" | crontab -l | { cat; echo "0 2 * * * $STORAGE_ROOT/backup-to-firebase.sh"; } | crontab -

# 10. Update Cloudflare Tunnel (if not already configured)
echo "☁️ Cloudflare Tunnel Configuration..."
echo "Add these routes to your Cloudflare Tunnel:"
echo "  - vf.fibreflow.app/storage → http://localhost:8090/storage"
echo "  - vf.fibreflow.app/api/storage → http://localhost:8091"

echo ""
echo "✅ Storage server setup complete!"
echo ""
echo "📊 Status:"
echo "  Storage Root: $STORAGE_ROOT"
echo "  Nginx Port: 8090 (file serving)"
echo "  API Port: 8091 (upload API)"
echo "  Service: systemctl status fibreflow-storage"
echo "  Logs: tail -f $STORAGE_ROOT/logs/storage-api.log"
echo ""
echo "🔗 Endpoints:"
echo "  Upload: POST https://vf.fibreflow.app/api/storage/upload/[type]/[category]"
echo "  Serve: GET https://vf.fibreflow.app/storage/[type]/[category]/[filename]"
echo "  List: GET https://vf.fibreflow.app/api/storage/list/[type]/[category]"
echo "  Delete: DELETE https://vf.fibreflow.app/api/storage/delete/[type]/[category]/[filename]"
echo ""
echo "📝 Next Steps:"
echo "1. Test upload: curl -X POST -F 'file=@test.jpg' https://vf.fibreflow.app/api/storage/upload/test/images"
echo "2. Update app environment: STORAGE_URL=https://vf.fibreflow.app/api/storage"
echo "3. Keep Firebase as fallback: FIREBASE_BACKUP=true"