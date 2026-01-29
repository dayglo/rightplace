# Audit Service Documentation

## Overview

The Audit Service provides comprehensive logging and tracking of all security-sensitive actions in the Prison Roll Call system. It implements an immutable audit trail for compliance, security review, and operational analysis.

## Architecture

### Components

1. **AuditEntry Model** (`app/models/audit.py`)
   - Pydantic model defining audit log structure
   - AuditAction enum for standardized action types
   - Support for JSON details field

2. **AuditRepository** (`app/db/repositories/audit_repo.py`)
   - Database access layer for audit logs
   - Immutable entries (no update/delete operations)
   - Efficient querying by entity, user, action, and time range

3. **AuditService** (`app/services/audit_service.py`)
   - Business logic for audit logging
   - CSV export functionality
   - Convenience methods for common queries

4. **Database Migration** (`app/db/migrations/006_audit_enhancements.sql`)
   - Adds `ip_address` and `user_agent` columns
   - Creates indexes for efficient queries

## Database Schema

```sql
CREATE TABLE audit_log (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    officer_id TEXT NOT NULL,      -- User who performed the action
    action TEXT NOT NULL,           -- Action type (e.g., "rollcall_started")
    entity_type TEXT NOT NULL,      -- Entity affected (e.g., "rollcall")
    entity_id TEXT NOT NULL,        -- ID of entity
    details TEXT,                   -- JSON blob with additional context
    ip_address TEXT,                -- Client IP address
    user_agent TEXT                 -- Client user agent string
);

-- Indexes for efficient queries
CREATE INDEX idx_audit_timestamp ON audit_log(timestamp);
CREATE INDEX idx_audit_action ON audit_log(action);
CREATE INDEX idx_audit_user ON audit_log(officer_id);
CREATE INDEX idx_audit_entity ON audit_log(entity_type, entity_id);
```

## Audit Actions

The following actions are logged:

### Inmate Management
- `INMATE_CREATED` - New inmate record created
- `INMATE_UPDATED` - Inmate details modified
- `INMATE_DELETED` - Inmate record deleted
- `FACE_ENROLLED` - Face embedding created
- `FACE_UNENROLLED` - Face embedding removed

### Roll Call Operations
- `ROLLCALL_STARTED` - Roll call session started
- `ROLLCALL_COMPLETED` - Roll call session completed
- `ROLLCALL_CANCELLED` - Roll call session cancelled
- `STOP_SKIPPED` - Location skipped during roll call

### Verification
- `VERIFICATION_RECORDED` - Face verification attempt logged
- `MANUAL_OVERRIDE_USED` - Officer manually verified inmate

### System Operations
- `POLICY_UPDATED` - Recognition policy thresholds changed
- `QUEUE_SYNCED` - Offline queue synchronized
- `CONNECTION_ESTABLISHED` - Device connected to server
- `CONNECTION_LOST` - Device connection lost

## Usage Examples

### Basic Logging

```python
from app.db.repositories.audit_repo import AuditRepository
from app.services.audit_service import AuditService
from app.models.audit import AuditAction

# Create service
audit_repo = AuditRepository(conn)
audit_service = AuditService(audit_repo)

# Log an action
audit_service.log_action(
    user_id="officer-001",
    action=AuditAction.ROLLCALL_STARTED,
    entity_type="rollcall",
    entity_id="rc-morning-001",
    details={"location": "A Wing", "expected_inmates": 42},
    ip_address="192.168.1.100",
    user_agent="PrisonRollCallApp/1.0",
)
```

### Query Audit History

```python
# Get complete audit trail for an entity
history = audit_service.get_entity_history("rollcall", "rc-morning-001")

for entry in history:
    print(f"{entry.timestamp}: {entry.action} by {entry.user_id}")
    if entry.details:
        print(f"  Details: {entry.details}")
```

### Query User Actions

```python
from datetime import datetime, timedelta

# Get all actions by a user in the last 24 hours
start = datetime.now() - timedelta(days=1)
end = datetime.now()

actions = audit_service.get_user_actions("officer-001", start, end)
print(f"Officer-001 performed {len(actions)} actions in the last 24 hours")
```

### Export Audit Logs

```python
# Export as CSV
csv_content = audit_service.export_logs(start, end, format="csv")

# Save to file
with open("audit_export.csv", "w") as f:
    f.write(csv_content)
```

## Command-Line Tools

### Export Script

```bash
# Export last 7 days (default)
python scripts/export_audit.py

# Export specific date range
python scripts/export_audit.py --start 2025-01-01 --end 2025-01-31

# Export last 30 days
python scripts/export_audit.py --days 30

# Custom output file
python scripts/export_audit.py --output audit_january.csv

# Specify database path
python scripts/export_audit.py --db /path/to/prison_rollcall.db
```

### Demo Script

```bash
# Run interactive demo
python scripts/demo_audit_logging.py
```

## Security Considerations

### Immutability

Audit entries are **immutable** by design:
- No update operations supported
- No delete operations supported
- Repository does not expose update/delete methods
- Ensures audit trail integrity

### Data Retention

- Audit logs are retained indefinitely by default
- Implement retention policy via external archival process
- Consider periodic export to external audit system
- Do not delete audit logs from production systems

### Performance

- Indexes optimize common query patterns
- Write performance: O(1) for inserts
- Read performance: O(log n) for indexed queries
- CSV export: O(n) where n = entries in time range

### Privacy

- `details` field may contain sensitive information
- Use encryption at rest for database file
- Control access to audit export functionality
- Redact sensitive fields when exporting for analysis

## Testing

### Unit Tests

```bash
# Run unit tests
pytest tests/unit/test_audit_service.py -v

# With coverage
pytest tests/unit/test_audit_service.py --cov=app/services/audit_service --cov=app/db/repositories/audit_repo
```

### Integration Tests

```bash
# Run integration tests
pytest tests/integration/test_audit_integration.py -v
```

### Test Coverage

Current coverage: **100%** for:
- `app/models/audit.py`
- `app/db/repositories/audit_repo.py`
- `app/services/audit_service.py`

## API Integration (Future)

To integrate audit logging into API endpoints:

```python
from app.models.audit import AuditAction
from app.services.audit_service import AuditService
from fastapi import Request

@router.post("/rollcalls/{id}/start")
def start_roll_call(
    id: str,
    request: Request,
    audit_service: AuditService = Depends(get_audit_service),
):
    # Perform action
    rollcall = rollcall_service.start_roll_call(id)

    # Log action
    audit_service.log_action(
        user_id=request.state.user_id,
        action=AuditAction.ROLLCALL_STARTED,
        entity_type="rollcall",
        entity_id=id,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
    )

    return rollcall
```

## Future Enhancements

1. **Real-time Monitoring**
   - WebSocket endpoint for live audit stream
   - Alert on suspicious activity patterns

2. **Advanced Analytics**
   - Officer activity dashboards
   - Manual override trend analysis
   - System usage reports

3. **External Integration**
   - Export to SIEM systems
   - Webhook notifications for critical events
   - Compliance reporting automation

4. **Audit Search**
   - Full-text search in details field
   - Advanced filtering UI
   - Audit trail visualization

## References

- Design Document: `/prison-rollcall-design-document-v3.md` (Appendix D)
- Database Schema: `/app/db/migrations/001_initial.sql`
- API Specification: Design doc section "Audit Log Actions"
