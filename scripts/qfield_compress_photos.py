#!/usr/bin/env python3
"""
QFieldCloud Photo Compression Script
Compresses existing photos in Mohadin's project to reduce size.

Target: Reduce 890MB (2,021 photos @ 440KB avg) → 350MB (@ 150KB avg)
Savings: 540MB (61% reduction)
"""

import os
import sys
from pathlib import Path
from PIL import Image
import psycopg2
from io import BytesIO
import boto3
from botocore.client import Config

# Force unbuffered output for real-time logging
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Configuration
DB_CONFIG = {
    'host': '100.96.203.105',
    'port': 5433,
    'database': 'qfieldcloud_db',
    'user': 'qfieldcloud_db_admin',
    'password': 'c6ce1f02f798c5776fee9e6857f628ff775c75e5eb3b7753'
}

MINIO_CONFIG = {
    'endpoint_url': 'http://100.96.203.105:8009',
    'aws_access_key_id': 'minioadmin',
    'aws_secret_access_key': 'minioadmin',
    'bucket': 'qfieldcloud-prod'
}

PROJECT_ID = '137eb5ec-4c0b-4eab-8a5c-de046eb06349'

# Compression settings - AGGRESSIVE MODE
TARGET_MAX_SIZE = 150 * 1024  # 150KB target (more aggressive)
JPEG_QUALITY = 65  # Lower quality but still good for field documentation
MAX_DIMENSION = 1600  # Smaller max dimension (was 2048)

def compress_image(image_data: bytes, original_size: int) -> tuple[bytes, int]:
    """
    Compress image to target size while maintaining quality.

    Returns: (compressed_bytes, new_size)
    """
    try:
        img = Image.open(BytesIO(image_data))

        # Convert RGBA to RGB if needed
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background

        # Resize if image is very large
        if max(img.size) > MAX_DIMENSION:
            ratio = MAX_DIMENSION / max(img.size)
            new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            print(f"  Resized from {original_size} to {new_size}")

        # Compress
        output = BytesIO()
        img.save(output, format='JPEG', quality=JPEG_QUALITY, optimize=True)
        compressed_data = output.getvalue()

        return compressed_data, len(compressed_data)

    except Exception as e:
        print(f"  ERROR compressing image: {e}")
        return image_data, original_size

def main():
    """Main compression routine"""

    print("=" * 70)
    print("QFieldCloud Photo Compression Script")
    print("=" * 70)
    print(f"Project: {PROJECT_ID} (Mohadin - MOA Pole Audit)")
    print(f"Target: Compress photos from ~440KB avg → ~150KB avg")
    print()

    # Connect to database
    print("Connecting to database...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Connect to MinIO
    print("Connecting to MinIO storage...")
    s3_client = boto3.client(
        's3',
        endpoint_url=MINIO_CONFIG['endpoint_url'],
        aws_access_key_id=MINIO_CONFIG['aws_access_key_id'],
        aws_secret_access_key=MINIO_CONFIG['aws_secret_access_key'],
        config=Config(signature_version='s3v4')
    )

    # Get all photo files
    print(f"\nFetching photo list for project {PROJECT_ID}...")
    cur.execute("""
        SELECT
            f.id,
            f.name,
            fv.id as version_id,
            fv.content as s3_key,
            fv.size,
            fv.etag
        FROM filestorage_file f
        JOIN filestorage_fileversion fv ON f.latest_version_id = fv.id
        WHERE f.project_id = %s
        AND (f.name LIKE '%%.jpg' OR f.name LIKE '%%.jpeg' OR f.name LIKE '%%.JPG')
        AND fv.size > %s
        ORDER BY fv.size DESC
    """, (PROJECT_ID, TARGET_MAX_SIZE))

    photos = cur.fetchall()
    total_photos = len(photos)

    if total_photos == 0:
        print("✅ No photos larger than 200KB found. All photos are already optimized!")
        return

    print(f"\nFound {total_photos} photos to compress (larger than 200KB)")

    # Calculate statistics
    total_original_size = sum(int(p[4]) for p in photos)  # p[4] is size (after s3_key)
    print(f"Total size: {total_original_size / 1024 / 1024:.1f} MB")
    print()

    # Confirm (auto-confirm if running non-interactively)
    print(f"Auto-confirming compression of {total_photos} photos...")
    # Uncomment the line below if you want manual confirmation:
    # response = input(f"Compress {total_photos} photos? (yes/no): ").strip().lower()
    # if response != 'yes':
    #     print("Aborted.")
    #     return

    print("\nStarting compression...")
    print("-" * 70)

    compressed_count = 0
    total_saved = 0
    errors = 0

    for idx, (file_id, filename, version_id, s3_key, original_size, etag) in enumerate(photos, 1):
        print(f"[{idx}/{total_photos}] {filename}")
        print(f"  Original: {original_size / 1024:.1f} KB")

        try:
            # Download from MinIO
            obj = s3_client.get_object(Bucket=MINIO_CONFIG['bucket'], Key=s3_key)
            image_data = obj['Body'].read()

            # Compress
            compressed_data, new_size = compress_image(image_data, original_size)

            # Check if compression was beneficial
            savings = original_size - new_size
            if savings < 10 * 1024:  # Less than 10KB savings, skip
                print(f"  Skipped (minimal savings: {savings / 1024:.1f} KB)")
                continue

            # Upload compressed version back to MinIO
            s3_client.put_object(
                Bucket=MINIO_CONFIG['bucket'],
                Key=s3_key,
                Body=compressed_data,
                ContentType='image/jpeg'
            )

            # Update database with new size
            cur.execute("""
                UPDATE filestorage_fileversion
                SET size = %s
                WHERE id = %s
            """, (new_size, version_id))
            conn.commit()

            compressed_count += 1
            total_saved += savings

            print(f"  Compressed: {new_size / 1024:.1f} KB")
            print(f"  Saved: {savings / 1024:.1f} KB ({savings / original_size * 100:.1f}%)")
            print()

        except Exception as e:
            print(f"  ERROR: {e}")
            errors += 1
            conn.rollback()
            continue

    # Summary
    print("-" * 70)
    print("\nSUMMARY:")
    print(f"✅ Compressed: {compressed_count} photos")
    print(f"❌ Errors: {errors}")
    print(f"💾 Total saved: {total_saved / 1024 / 1024:.1f} MB")
    print(f"📊 Average savings: {total_saved / compressed_count / 1024:.1f} KB per photo")

    cur.close()
    conn.close()

    print("\n✅ Compression complete!")
    print("\nNOTE: Tell Mohadin to sync his project again to see the changes.")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAborted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        sys.exit(1)
