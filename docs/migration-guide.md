# Migration Guide: Requirements Versioning System

## Overview

This guide helps you migrate from the existing requirements system to the new versioned requirements system with PDF upload capabilities. The migration process is designed to be safe, reversible, and preserve all existing data.

## Table of Contents

1. [Pre-Migration Checklist](#pre-migration-checklist)
2. [Migration Process](#migration-process)
3. [Post-Migration Verification](#post-migration-verification)
4. [API Changes](#api-changes)
5. [Rollback Procedures](#rollback-procedures)
6. [Troubleshooting](#troubleshooting)

## Pre-Migration Checklist

### System Requirements
- [ ] Python 3.8+ installed
- [ ] SQLite 3.x available
- [ ] Sufficient disk space (2x current database size)
- [ ] Backup storage available
- [ ] Ollama service installed (for PDF features)

### Backup Preparation
- [ ] Create full database backup
- [ ] Export existing requirements data
- [ ] Document current API usage
- [ ] Test backup restoration procedure

### Dependency Check
```bash
# Install new dependencies
pip install PyMuPDF psutil

# Verify Ollama installation (optional for PDF features)
ollama --version
```

## Migration Process

### Step 1: Create System Backup

```bash
# Create timestamped backup
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
sqlite3 app.db ".backup backups/app_pre_migration_${BACKUP_DATE}.db"

# Verify backup
sqlite3 "backups/app_pre_migration_${BACKUP_DATE}.db" ".tables"
```

### Step 2: Export Existing Data (Optional)

```bash
# Export existing requirements to CSV
sqlite3 app.db -header -csv "SELECT * FROM requirements;" > existing_requirements.csv

# Count existing records
sqlite3 app.db "SELECT COUNT(*) as total_requirements FROM requirements;"
```

### Step 3: Run Migration Script

```bash
# Run the migration
python migrate_database.py
```

**Expected Output:**
```
🗄️  Requirements Versioning Database Migration
============================================================
Database: app.db
Migrations directory: migrations/

📊 Current Migration Status
----------------------------------------
Total migrations: 3
Applied migrations: 0
Pending migrations: 3

Pending migrations:
  • 000: create_migration_tables.sql
  • 001: create_requirement_documents_table.sql
  • 002: migrate_existing_requirements.sql

⚠️  This will apply 3 migrations to the database.
Continue? (y/N): y

🚀 Running Migrations
----------------------------------------
✅ Migration 000 completed successfully
✅ Migration 001 completed successfully  
✅ Migration 002 completed successfully

🎉 Migration completed successfully!
```

### Step 4: Verify Migration Results

```bash
# Check migration status
python -c "
import sqlite3
conn = sqlite3.connect('app.db')
cursor = conn.execute('SELECT version, description, applied_at FROM schema_migrations ORDER BY version')
for row in cursor:
    print(f'✅ Migration {row[0]}: {row[1]} ({row[2]})')
conn.close()
"
```

## Post-Migration Verification

### Database Schema Verification

```bash
# Verify new table exists
sqlite3 app.db ".schema requirement_documents"

# Check indexes
sqlite3 app.db ".indices requirement_documents"

# Verify data migration
sqlite3 app.db "
SELECT 
    COUNT(*) as migrated_count,
    COUNT(DISTINCT project_id) as projects_affected,
    MIN(created_at) as earliest,
    MAX(created_at) as latest
FROM requirement_documents 
WHERE version = 1;
"
```

### API Functionality Test

```bash
# Test health endpoint
curl http://localhost:8000/api/v1/monitoring/health

# Test requirements endpoint
curl "http://localhost:8000/api/v1/projects/test-project/requirements/latest"

# Test new versioning features
curl -X POST "http://localhost:8000/api/v1/projects/test-project/requirements" \
  -d "content=# Test Requirements\n\n1. Test requirement" \
  -d "status=draft"
```

### Performance Verification

```bash
# Check system performance
curl http://localhost:8000/api/v1/monitoring/metrics

# Verify cache functionality
curl http://localhost:8000/api/v1/monitoring/cache
```

## API Changes

### New Endpoints

The migration introduces several new endpoints:

#### Requirements Management
```http
# Upsert requirements (replaces old create/update)
POST /api/v1/projects/{project_id}/requirements

# Get latest version (new)
GET /api/v1/projects/{project_id}/requirements/latest

# Get specific version (new)
GET /api/v1/projects/{project_id}/requirements/{version}

# List all versions with pagination (enhanced)
GET /api/v1/projects/{project_id}/requirements

# PDF upload (new)
POST /api/v1/projects/{project_id}/requirements/upload-pdf

# Status management (new)
PATCH /api/v1/projects/{project_id}/requirements/{document_id}/status

# Version deletion (new)
DELETE /api/v1/projects/{project_id}/requirements/{version}

# Summary statistics (new)
GET /api/v1/projects/{project_id}/requirements/summary
```

#### Monitoring Endpoints (New)
```http
GET /api/v1/monitoring/health
GET /api/v1/monitoring/metrics
GET /api/v1/monitoring/dashboard
GET /api/v1/monitoring/system
GET /api/v1/monitoring/cache
GET /api/v1/monitoring/alerts
```

### Response Format Changes

#### Before Migration
```json
{
  "id": 1,
  "project_id": "my-project",
  "description": "User authentication requirement",
  "category": "Functional",
  "status": "approved",
  "created_at": "2023-01-01T00:00:00Z"
}
```

#### After Migration
```json
{
  "id": 1,
  "project_id": "my-project",
  "content": "# Requirements Document\n\n1. User authentication requirement",
  "version": 1,
  "status": "published",
  "source_type": "manual",
  "original_filename": null,
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```

### Client Code Updates

#### Old API Usage
```python
# Old way - separate create/update endpoints
response = requests.post(f"/api/v1/requirements", json={
    "project_id": "my-project",
    "description": "User authentication",
    "category": "Functional"
})

# Old way - simple list
response = requests.get(f"/api/v1/requirements?project_id=my-project")
```

#### New API Usage
```python
# New way - upsert endpoint
response = requests.post(
    f"/api/v1/projects/my-project/requirements",
    params={
        "content": "# Requirements\n\n1. User authentication",
        "status": "draft"
    }
)

# New way - versioned access
response = requests.get(f"/api/v1/projects/my-project/requirements/latest")

# New way - paginated list with filtering
response = requests.get(
    f"/api/v1/projects/my-project/requirements",
    params={"page": 1, "per_page": 20, "status_filter": "published"}
)
```

## Rollback Procedures

### Automatic Rollback

If migration fails, the system automatically rolls back:

```bash
# Check rollback logs
tail -f migration.log

# Verify rollback status
sqlite3 app.db "SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 1;"
```

### Manual Rollback

If you need to rollback after successful migration:

```bash
# Run rollback script
python rollback_migration.py

# Follow prompts to select target version
# Example: rollback to version 000 (pre-migration state)
```

**Rollback Process:**
1. Creates automatic backup before rollback
2. Removes migration records in reverse order
3. Drops new tables and indexes
4. Restores original schema (if backup exists)

### Emergency Restore

If rollback fails, restore from backup:

```bash
# Stop application
pkill -f "uvicorn app.main:app"

# Restore from backup
cp "backups/app_pre_migration_${BACKUP_DATE}.db" app.db

# Restart application
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Troubleshooting

### Common Migration Issues

#### Issue: Migration Fails with "Table Already Exists"
**Cause**: Previous incomplete migration attempt
**Solution**:
```bash
# Check existing tables
sqlite3 app.db ".tables"

# If requirement_documents exists, drop it
sqlite3 app.db "DROP TABLE IF EXISTS requirement_documents;"

# Re-run migration
python migrate_database.py
```

#### Issue: "No Module Named 'psutil'"
**Cause**: Missing optional dependency
**Solution**:
```bash
# Install missing dependency
pip install psutil

# Or run without system monitoring
export DISABLE_SYSTEM_MONITORING=true
python migrate_database.py
```

#### Issue: Data Migration Shows 0 Records
**Cause**: No existing requirements table or empty table
**Solution**:
```bash
# Check if old requirements table exists
sqlite3 app.db ".schema requirements"

# If table exists, check data
sqlite3 app.db "SELECT COUNT(*) FROM requirements;"

# This is normal if starting fresh
```

#### Issue: PDF Upload Not Working
**Cause**: Ollama service not running
**Solution**:
```bash
# Start Ollama service
ollama serve

# Test Ollama connection
curl http://localhost:11434/api/version

# PDF upload will work without Ollama but won't convert to markdown
```

### Performance Issues After Migration

#### Slow Query Performance
```bash
# Analyze query performance
sqlite3 app.db "EXPLAIN QUERY PLAN SELECT * FROM requirement_documents WHERE project_id = 'test';"

# Rebuild indexes if needed
sqlite3 app.db "REINDEX;"

# Update table statistics
sqlite3 app.db "ANALYZE;"
```

#### High Memory Usage
```bash
# Check cache usage
curl http://localhost:8000/api/v1/monitoring/cache

# Clear cache if needed
curl -X POST http://localhost:8000/api/v1/monitoring/cache/clear

# Trigger cleanup
curl -X POST http://localhost:8000/api/v1/monitoring/cleanup
```

### Validation Scripts

#### Data Integrity Check
```python
# data_integrity_check.py
import sqlite3

def check_data_integrity():
    conn = sqlite3.connect('app.db')
    
    # Check version uniqueness
    cursor = conn.execute("""
        SELECT project_id, version, COUNT(*) 
        FROM requirement_documents 
        GROUP BY project_id, version 
        HAVING COUNT(*) > 1
    """)
    
    duplicates = cursor.fetchall()
    if duplicates:
        print(f"❌ Found {len(duplicates)} duplicate versions")
        return False
    
    # Check version sequences
    cursor = conn.execute("""
        SELECT project_id, 
               COUNT(*) as total_versions,
               MAX(version) as max_version
        FROM requirement_documents 
        GROUP BY project_id
    """)
    
    for row in cursor:
        if row[1] != row[2]:  # total_versions != max_version
            print(f"❌ Version gap in project {row[0]}: {row[1]} versions, max version {row[2]}")
            return False
    
    print("✅ Data integrity check passed")
    return True

if __name__ == "__main__":
    check_data_integrity()
```

#### Performance Benchmark
```python
# performance_benchmark.py
import time
import requests

def benchmark_api():
    base_url = "http://localhost:8000/api/v1"
    project_id = "benchmark-test"
    
    # Test creation performance
    start_time = time.time()
    for i in range(10):
        response = requests.post(
            f"{base_url}/projects/{project_id}/requirements",
            params={"content": f"# Benchmark Test {i}", "status": "draft"}
        )
        assert response.status_code == 201
    
    creation_time = time.time() - start_time
    print(f"✅ Created 10 versions in {creation_time:.2f}s ({10/creation_time:.1f} ops/sec)")
    
    # Test retrieval performance
    start_time = time.time()
    for i in range(1, 11):
        response = requests.get(f"{base_url}/projects/{project_id}/requirements/{i}")
        assert response.status_code == 200
    
    retrieval_time = time.time() - start_time
    print(f"✅ Retrieved 10 versions in {retrieval_time:.2f}s ({10/retrieval_time:.1f} ops/sec)")

if __name__ == "__main__":
    benchmark_api()
```

## Support and Next Steps

### Post-Migration Tasks

1. **Update Client Applications**
   - Update API endpoints
   - Handle new response formats
   - Implement version management
   - Add error handling for new error codes

2. **Configure Monitoring**
   - Set up health check monitoring
   - Configure performance alerts
   - Set up log aggregation
   - Create monitoring dashboards

3. **Performance Optimization**
   - Monitor cache hit rates
   - Optimize query patterns
   - Adjust resource limits
   - Configure concurrent processing

4. **User Training**
   - Document new features
   - Train users on version management
   - Explain PDF upload workflow
   - Provide troubleshooting guides

### Getting Help

If you encounter issues during migration:

1. **Check Logs**: Review migration.log for detailed error information
2. **Run Diagnostics**: Use monitoring endpoints to check system health
3. **Verify Backups**: Ensure backups are available for rollback
4. **Test Rollback**: Practice rollback procedure in development environment

### Migration Checklist

- [ ] Pre-migration backup completed
- [ ] Migration script executed successfully
- [ ] Database schema verified
- [ ] Data integrity confirmed
- [ ] API functionality tested
- [ ] Performance benchmarks acceptable
- [ ] Client applications updated
- [ ] Monitoring configured
- [ ] User documentation updated
- [ ] Rollback procedure tested

The migration to the versioned requirements system provides significant improvements in functionality, performance, and maintainability. Follow this guide carefully to ensure a smooth transition.