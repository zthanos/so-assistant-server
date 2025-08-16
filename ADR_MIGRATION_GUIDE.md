# ADR Schema Migration Guide

## Current Status

The ADR API is currently running in **backward compatibility mode** with the original simple schema. This ensures the API continues to work while the database migration is pending.

## Current Schema (Backward Compatible)

### Database Fields
- `id` - Primary key
- `project_id` - Foreign key to projects
- `title` - ADR title (required)
- `content` - ADR content (required)
- `created_at` - Creation timestamp
- `updated_at` - Update timestamp

### API Schema
```json
{
  "title": "ADR Title",
  "content": "ADR content and details",
  "adr_id": 123  // Optional for updates
}
```

## Future Enhanced Schema (After Migration)

### Additional Database Fields
- `status` - ADR status (proposed, accepted, rejected, deprecated)
- `context` - Background and context information
- `decision` - The architectural decision made
- `consequences` - Positive and negative consequences
- `alternatives` - Alternative approaches considered
- `author` - Decision author or team
- `tags` - JSON array of tags for categorization

### Enhanced API Schema
```json
{
  "title": "ADR Title",
  "status": "proposed",
  "context": "Background information...",
  "decision": "The decision made...",
  "consequences": "Expected outcomes...",
  "alternatives": "Other options considered...",
  "author": "Architecture Team",
  "tags": ["architecture", "microservices"],
  "content": "Legacy content field",
  "adr_id": 123  // Optional for updates
}
```

## Migration Steps

### Step 1: Apply Database Migration

Run the SQL migration script to add the new columns:

```bash
mysql -u username -p database_name < add_adr_fields_migration.sql
```

### Step 2: Update ADR Model

Uncomment the new fields in `app/domain/models/adrs.py`:

```python
# Uncomment these lines after migration:
status = Column(String(50), nullable=True, default="proposed")
context = Column(Text, nullable=True)
decision = Column(Text, nullable=True)
consequences = Column(Text, nullable=True)
alternatives = Column(Text, nullable=True)
author = Column(String(255), nullable=True)
tags = Column(JSON, nullable=True, default=list)
```

### Step 3: Update ADR Schemas

Replace the current schemas in `app/api/schemas/adrs.py` with the extended versions:

```python
# Use ADRExtendedBase and ADRExtendedResponse as the main schemas
# Update imports and service methods accordingly
```

### Step 4: Update Service Methods

Update the ADR service methods to handle all the new fields:

```python
# Update create_adr, update_adr, and upsert_adr methods
# Add support for all new fields in filtering and search
```

### Step 5: Test Migration

Run comprehensive tests to ensure all functionality works with the new schema:

```bash
python test_adr_full_schema.py  # Create this test after migration
```

## Backward Compatibility

The current implementation ensures:

- ✅ **Existing API calls continue to work** - No breaking changes
- ✅ **Database queries are compatible** - Only queries existing columns
- ✅ **Gradual migration path** - Can migrate when ready
- ✅ **No data loss** - All existing ADRs remain intact

## Testing Current Implementation

Test the current backward compatible implementation:

```bash
python test_adr_backward_compatibility.py
```

## Migration Benefits

After migration, you'll gain:

- 📊 **Structured ADR Format** - Proper ADR sections (context, decision, etc.)
- 🏷️ **Tagging System** - Organize ADRs with tags
- 📈 **Status Tracking** - Track ADR lifecycle
- 🔍 **Enhanced Search** - Search across all ADR sections
- 👤 **Author Attribution** - Track who made decisions
- 📝 **Rich Metadata** - Better organization and filtering

## Rollback Plan

If issues occur after migration:

1. **Revert Model Changes** - Comment out new fields in the model
2. **Revert Schema Changes** - Use original schemas
3. **Revert Service Changes** - Use backward compatible service methods
4. **Database Rollback** - Drop new columns if needed (optional)

## Current API Endpoints

All endpoints work with the current backward compatible schema:

- `POST /api/v1/projects/{project_id}/adrs` - Create/update ADR
- `GET /api/v1/adrs/{adr_id}` - Get ADR by ID
- `GET /api/v1/projects/{project_id}/adrs` - List ADRs with pagination
- `GET /api/v1/projects/{project_id}/adrs/search` - Search ADRs
- `DELETE /api/v1/adrs/{adr_id}` - Delete ADR

## Next Steps

1. **Schedule Migration** - Plan database migration during maintenance window
2. **Backup Database** - Ensure you have a backup before migration
3. **Apply Migration** - Run the SQL migration script
4. **Update Code** - Uncomment new fields and update schemas
5. **Test Thoroughly** - Verify all functionality works
6. **Update Documentation** - Update API docs with new schema