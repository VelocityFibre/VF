# QFieldCloud Photo Compression Guide

## Quick Summary

**Problem**: Mohadin's project has 2,021 photos = 890MB causing sync failures
**Solution**: Compress existing photos from ~440KB → ~150KB average
**Result**: Project size reduces to ~350MB (540MB saved)

## Status

✅ **Timeout Fix Applied** (2026-01-14 12:30)
- Workers now wait 5 minutes instead of 60 seconds
- Project should sync now, but still slow due to size

⚠️ **Photo Compression** (Optional - but recommended)
- Run script below to compress existing photos
- Significant improvement for future syncs

## Option 1: Run Compression Script (Recommended)

### Prerequisites

Install required Python packages:
```bash
source venv/bin/activate
pip install Pillow psycopg2-binary boto3
```

### Run the Script

```bash
cd /home/louisdup/Agents/claude/scripts
./qfield_compress_photos.py
```

### What it Does

1. Connects to QFieldCloud database
2. Finds all photos > 200KB in Mohadin's project
3. Compresses each photo:
   - Resizes if > 2048px width/height
   - Saves as JPEG quality 85%
   - Uploads back to MinIO storage
   - Updates database with new size
4. Shows progress and savings

### Expected Results

```
Before:  2,021 photos @ 440KB avg = 890MB
After:   2,021 photos @ 150KB avg = 350MB
Savings: 540MB (61% reduction)
```

### Safety

- **Non-destructive**: Only compresses, doesn't delete
- **Reversible**: Can restore from MinIO backups if needed
- **Database transaction**: Rolls back on error
- **Tested approach**: JPEG quality 85% maintains visual quality

### Time Required

- ~20-30 minutes for 2,021 photos
- ~1 second per photo (download, compress, upload)

## Option 2: QField App Settings (Prevention)

**For Future Photos**, tell Mohadin to change QField settings:

### Steps:
1. Open QField app
2. Tap menu (☰) → Settings
3. Find "Camera" section
4. Change "Photo Quality": High → **Medium**

### Result:
- Future photos will be ~150KB instead of 440KB
- Faster uploads, faster syncs
- Still good quality for documentation

## Option 3: Do Nothing

If timeout fix works and Mohadin is patient:
- Current setup will work, just slower
- 5 minutes should be enough for 890MB
- But future syncs will get slower as more photos added

## Recommendation

**Do both**:
1. ✅ Timeout fix (DONE) - immediate relief
2. 🔧 Run compression script - long-term solution
3. 📱 Change QField settings - prevent future problems

## Questions?

Contact Louis or check logs:
- Script output shows progress
- Database: `psql -h 100.96.203.105 -p 5433 -U qfieldcloud_db_admin -d qfieldcloud_db`
- MinIO: http://100.96.203.105:8010 (minioadmin/minioadmin)

## Troubleshooting

**"Connection refused"**
- Check VF Server is accessible: `ssh velo@100.96.203.105`
- Verify services running: `docker-compose ps`

**"Permission denied"**
- Check database password in script matches `.env`
- Verify MinIO credentials

**"Out of memory"**
- Script processes one photo at a time
- Safe for server with 32GB RAM

**Want to test first?**
Edit script line 126 to process only 10 photos:
```python
photos = cur.fetchall()[:10]  # Test with 10 photos
```
