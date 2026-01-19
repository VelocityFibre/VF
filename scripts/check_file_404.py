#!/usr/bin/env python3
"""
Check if specific file exists in QFieldCloud database and MinIO
"""
import psycopg2
import boto3
from botocore.client import Config

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
FILE_NAME = 'DCIM/JPEG_20251015084211125.jpg'

def main():
    print(f"Checking file: {FILE_NAME}")
    print("=" * 70)

    # Connect to database
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Check if file exists in database
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
        AND f.name = %s
    """, (PROJECT_ID, FILE_NAME))

    result = cur.fetchone()

    if not result:
        print("❌ File NOT FOUND in database")
        print("\nSearching for similar files...")
        cur.execute("""
            SELECT name, size
            FROM filestorage_file f
            JOIN filestorage_fileversion fv ON f.latest_version_id = fv.id
            WHERE f.project_id = %s
            AND name LIKE '%JPEG_20251015084211%'
        """, (PROJECT_ID,))
        similar = cur.fetchall()
        if similar:
            print("Found similar files:")
            for name, size in similar:
                print(f"  - {name} ({size} bytes)")
        else:
            print("No similar files found")
        return

    file_id, name, version_id, s3_key, size, etag = result

    print(f"✅ File FOUND in database:")
    print(f"   File ID: {file_id}")
    print(f"   Name: {name}")
    print(f"   Version ID: {version_id}")
    print(f"   S3 Key: {s3_key}")
    print(f"   Size: {size} bytes ({size/1024:.1f} KB)")
    print(f"   ETag: {etag}")
    print()

    # Check MinIO
    print("Checking MinIO storage...")
    s3_client = boto3.client(
        's3',
        endpoint_url=MINIO_CONFIG['endpoint_url'],
        aws_access_key_id=MINIO_CONFIG['aws_access_key_id'],
        aws_secret_access_key=MINIO_CONFIG['aws_secret_access_key'],
        config=Config(signature_version='s3v4')
    )

    try:
        obj = s3_client.head_object(Bucket=MINIO_CONFIG['bucket'], Key=s3_key)
        print(f"✅ File EXISTS in MinIO:")
        print(f"   Size: {obj['ContentLength']} bytes")
        print(f"   Last Modified: {obj['LastModified']}")
        print(f"   Content-Type: {obj.get('ContentType', 'N/A')}")
    except Exception as e:
        print(f"❌ File NOT FOUND in MinIO: {e}")

    cur.close()
    conn.close()

if __name__ == '__main__':
    main()
