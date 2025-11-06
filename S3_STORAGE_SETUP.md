# AWS S3 Storage Configuration Guide

This guide explains how to configure CerebraUI to store files (including AI-generated images) in AWS S3 instead of local Docker volumes.

## Overview

CerebraUI already supports AWS S3 storage out of the box. You just need to configure the appropriate environment variables.

## Prerequisites

1. **AWS Account** with S3 access
2. **S3 Bucket** created in your desired region
3. **IAM Credentials** (Access Key ID and Secret Access Key) OR IAM Role (for EC2/EKS)

## Configuration

### Required Environment Variables

Add these to your `.env` file or docker-compose environment:

```bash
# Storage Provider Selection
STORAGE_PROVIDER=s3

# S3 Configuration
S3_BUCKET_NAME=your-bucket-name
S3_REGION_NAME=us-east-1

# Authentication Method 1: Using Access Keys (Recommended for development)
S3_ACCESS_KEY_ID=your-access-key-id
S3_SECRET_ACCESS_KEY=your-secret-access-key

# Authentication Method 2: Using IAM Roles (Recommended for production)
# If running on EC2/EKS with IAM roles, you can omit the access keys above
# The SDK will automatically use the instance/pod credentials
```

### Optional Environment Variables

```bash
# Custom S3 Endpoint (for S3-compatible services like MinIO, DigitalOcean Spaces)
S3_ENDPOINT_URL=https://s3.amazonaws.com

# Key Prefix (subfolder in bucket)
S3_KEY_PREFIX=cerebraui/uploads

# S3 Transfer Acceleration
S3_USE_ACCELERATE_ENDPOINT=false

# S3 Addressing Style (path or virtual)
S3_ADDRESSING_STYLE=auto
```

## Docker Compose Example

### Basic Configuration (Using Access Keys)

```yaml
version: '3.8'

services:
  backend:
    image: your-backend-image
    environment:
      # Storage Configuration
      STORAGE_PROVIDER: s3
      S3_BUCKET_NAME: my-cerebraui-bucket
      S3_REGION_NAME: us-east-1
      S3_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}
      S3_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY}

      # Optional: Use subfolder in bucket
      S3_KEY_PREFIX: uploads

      # Database configuration (still uses Postgres)
      DATABASE_URL: postgresql://user:pass@db:5432/cerebraui

    # No need for volumes anymore for file storage!
    # volumes:
    #   - ./data/uploads:/app/backend/data/uploads  # Not needed with S3
```

### Advanced Configuration (Using IAM Roles on EC2/EKS)

```yaml
version: '3.8'

services:
  backend:
    image: your-backend-image
    environment:
      # Storage Configuration
      STORAGE_PROVIDER: s3
      S3_BUCKET_NAME: my-cerebraui-bucket
      S3_REGION_NAME: us-east-1

      # No access keys needed - IAM role will be used automatically

      # Database configuration
      DATABASE_URL: postgresql://user:pass@db:5432/cerebraui
```

## AWS IAM Policy

Your IAM user/role needs these S3 permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::your-bucket-name/*",
        "arn:aws:s3:::your-bucket-name"
      ]
    }
  ]
}
```

## How It Works

### File Upload Flow

1. User uploads file or AI generates image
2. File is temporarily saved to local storage (`/app/backend/data/uploads`)
3. File is uploaded to S3: `s3://bucket-name/prefix/filename`
4. Database stores S3 path: `s3://bucket-name/prefix/filename`
5. Local temporary file can be deleted (but kept as cache)

### File Retrieval Flow

1. User requests file by ID: `/api/v1/files/{id}/content`
2. System checks local cache first
3. If not in cache, downloads from S3 to local cache
4. Serves file from local cache
5. Local cache acts as performance optimization

### File Deletion Flow

1. User deletes file
2. File is deleted from S3
3. File is deleted from local cache
4. Database record is removed

## Migration from Local Storage to S3

If you already have files in local storage:

### Step 1: Configure S3

Add S3 environment variables as shown above.

### Step 2: Restart Services

```bash
docker-compose down
docker-compose up -d
```

### Step 3: Migrate Existing Files (Optional)

**Note**: Existing local files will still work. New files will be stored in S3.

To migrate existing files to S3, you can:

#### Option A: Let them migrate naturally
- Keep local files
- New uploads go to S3
- Old files remain local
- System handles both transparently

#### Option B: Manual migration script

```python
# migrate_to_s3.py
import os
from cerebraui.storage.provider import Storage, LocalStorageProvider, S3StorageProvider
from cerebraui.models.files import Files

# Switch to S3
s3_storage = S3StorageProvider()
local_storage = LocalStorageProvider()

# Get all files from database
files = Files.get_files()

for file in files:
    if file.path.startswith("/app/backend/data/uploads/"):
        # This is a local file
        local_path = file.path
        filename = os.path.basename(local_path)

        try:
            # Read file from local storage
            with open(local_path, "rb") as f:
                # Upload to S3
                contents, s3_path = s3_storage.upload_file(f, filename)

                # Update database
                file.path = s3_path
                Files.update_file_by_id(file.id, {"path": s3_path})

                print(f"Migrated: {filename} -> {s3_path}")
        except Exception as e:
            print(f"Error migrating {filename}: {e}")
```

## Supported Storage Providers

CerebraUI supports multiple storage backends:

| Provider | Value | Description |
|----------|-------|-------------|
| Local | `local` | Local filesystem (default) |
| AWS S3 | `s3` | Amazon S3 or S3-compatible |
| Google Cloud | `gcs` | Google Cloud Storage |
| Azure | `azure` | Azure Blob Storage |

## S3-Compatible Services

The S3 provider works with any S3-compatible service:

### MinIO

```bash
STORAGE_PROVIDER=s3
S3_ENDPOINT_URL=http://minio:9000
S3_BUCKET_NAME=cerebraui
S3_ACCESS_KEY_ID=minioadmin
S3_SECRET_ACCESS_KEY=minioadmin
S3_REGION_NAME=us-east-1
```

### DigitalOcean Spaces

```bash
STORAGE_PROVIDER=s3
S3_ENDPOINT_URL=https://nyc3.digitaloceanspaces.com
S3_BUCKET_NAME=your-space-name
S3_ACCESS_KEY_ID=your-spaces-key
S3_SECRET_ACCESS_KEY=your-spaces-secret
S3_REGION_NAME=nyc3
```

### Cloudflare R2

```bash
STORAGE_PROVIDER=s3
S3_ENDPOINT_URL=https://your-account-id.r2.cloudflarestorage.com
S3_BUCKET_NAME=your-bucket
S3_ACCESS_KEY_ID=your-r2-access-key
S3_SECRET_ACCESS_KEY=your-r2-secret-key
S3_REGION_NAME=auto
```

## Troubleshooting

### Error: "Error uploading file to S3"

**Cause**: Incorrect credentials or permissions

**Solution**:
1. Verify `S3_ACCESS_KEY_ID` and `S3_SECRET_ACCESS_KEY`
2. Check IAM policy has required permissions
3. Verify bucket name and region are correct

### Error: "Error downloading file from S3"

**Cause**: File not found or permission issue

**Solution**:
1. Check if file exists in S3 bucket
2. Verify read permissions in IAM policy
3. Check if `S3_KEY_PREFIX` matches

### Files not appearing

**Cause**: Database still has local paths

**Solution**:
1. Check `file.path` in database
2. If path starts with `/app/backend/`, it's still using local storage
3. Restart services to use new configuration for new uploads

### Slow file access

**Cause**: No local cache or frequent downloads

**Solution**:
1. Local cache is enabled by default
2. First access downloads from S3 (slower)
3. Subsequent accesses use local cache (faster)
4. Consider using S3 Transfer Acceleration for faster uploads

## Cost Optimization

### S3 Storage Costs

- **Standard Storage**: $0.023 per GB/month (first 50 TB)
- **PUT/POST Requests**: $0.005 per 1,000 requests
- **GET Requests**: $0.0004 per 1,000 requests
- **Data Transfer Out**: $0.09 per GB (first 10 TB)

### Cost Reduction Tips

1. **Use S3 Lifecycle Policies**:
   ```json
   {
     "Rules": [
       {
         "Id": "DeleteOldFiles",
         "Status": "Enabled",
         "Expiration": {
           "Days": 90
         }
       }
     ]
   }
   ```

2. **Use Intelligent-Tiering**:
   - Automatically moves objects between access tiers
   - Reduces costs for infrequently accessed files

3. **Enable Compression**:
   - Compress files before uploading
   - Reduces storage and transfer costs

4. **Use CloudFront CDN**:
   - Cache frequently accessed files
   - Reduces S3 GET requests and data transfer

## Performance Optimization

### Local Cache

The system maintains a local cache in `/app/backend/data/uploads/`:
- First access: Downloads from S3 (slower)
- Subsequent access: Serves from cache (faster)
- Cache persists across restarts if volume is mounted

### S3 Transfer Acceleration

Enable for faster uploads from distant locations:

```bash
S3_USE_ACCELERATE_ENDPOINT=true
```

**Note**: Additional cost applies ($0.04-$0.08 per GB transferred)

### Regional Considerations

- Choose S3 region closest to your users
- Use CloudFront for global distribution
- Consider multi-region replication for high availability

## Security Best Practices

### 1. Use IAM Roles (Production)

Instead of access keys, use IAM roles:
- EC2 Instance Profiles
- EKS Service Accounts (IRSA)
- Avoids storing credentials in environment variables

### 2. Encrypt Data at Rest

Enable S3 bucket encryption:
- SSE-S3 (Server-Side Encryption with S3 managed keys)
- SSE-KMS (Server-Side Encryption with AWS KMS)
- SSE-C (Server-Side Encryption with Customer provided keys)

### 3. Enable Bucket Versioning

Protect against accidental deletion:

```bash
aws s3api put-bucket-versioning \
  --bucket your-bucket-name \
  --versioning-configuration Status=Enabled
```

### 4. Restrict Bucket Access

- Enable "Block all public access"
- Use bucket policies to restrict access
- Enable MFA Delete for critical buckets

### 5. Monitor Access

- Enable S3 Access Logging
- Use CloudTrail for API auditing
- Set up CloudWatch Alarms for unusual activity

## Database Considerations

**Important**: Only file storage moves to S3. The database (chat history) remains in Postgres.

Your setup:
- ✅ **Chat History**: Neon Postgres (as before)
- ✅ **Files/Images**: AWS S3 (new)
- ✅ **Temporary Cache**: Docker volume (optional)

Database schema doesn't change:
- `file` table stores S3 paths: `s3://bucket/path/to/file`
- Existing queries work without modification
- No database migration needed

## Testing

### Test S3 Configuration

```bash
# Upload a test file
curl -X POST http://localhost:8080/api/v1/files \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test.png"

# Response will show S3 path
{
  "id": "uuid",
  "path": "s3://your-bucket/uploads/uuid_test.png",
  ...
}

# Retrieve file
curl http://localhost:8080/api/v1/files/{id}/content \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o downloaded.png
```

### Verify S3 Upload

```bash
# List files in S3 bucket
aws s3 ls s3://your-bucket-name/uploads/

# Check file exists
aws s3 ls s3://your-bucket-name/uploads/uuid_test.png
```

## FAQ

### Q: Will existing local files stop working?

**A**: No. The system handles both S3 and local paths transparently. Old files remain accessible.

### Q: Do I need to keep Docker volumes?

**A**: Not for file storage. But keeping a small cache volume improves performance.

### Q: Can I switch back to local storage?

**A**: Yes. Change `STORAGE_PROVIDER=local` and restart. Files in S3 will remain there but new uploads go local.

### Q: What happens if S3 is unavailable?

**A**: File uploads and downloads will fail. Local cache may serve previously downloaded files. Consider implementing retry logic or fallback storage.

### Q: How do I backup S3 data?

**A**: Use S3 versioning, Cross-Region Replication (CRR), or AWS Backup.

### Q: Can I use multiple buckets?

**A**: Not directly. You'd need to modify the code to support multiple buckets. Current implementation uses a single bucket with optional prefix.

## Related Documentation

- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [Boto3 S3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html)
- [IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)

## Support

For issues or questions:
1. Check backend logs: `docker-compose logs backend`
2. Verify S3 bucket permissions
3. Test AWS credentials: `aws s3 ls s3://your-bucket-name`
4. Review IAM policy configuration
