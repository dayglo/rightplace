# Audit Logging Demo - Quick Start

## 🚀 30-Second Demo

```bash
cd server

# Terminal 1: Start server
source .venv/bin/activate
uvicorn app.main:app --reload

# Terminal 2: Run automated demo
source .venv/bin/activate
./scripts/demo_audit_api.sh
```

That's it! The script will demonstrate all audit logging features automatically.

---

## 📋 5-Minute Manual Demo

```bash
# 1. Create inmate
curl -X POST http://localhost:8000/api/v1/inmates \
  -H "Content-Type: application/json" \
  -H "X-Officer-ID: officer-demo" \
  -d '{"inmate_number":"A12345","first_name":"John","last_name":"Doe","date_of_birth":"1990-01-01","cell_block":"A","cell_number":"101"}'

# 2. View audit log
python scripts/export_audit.py --days 1
```

---

## 🎯 What Gets Logged?

| Action | Endpoint | Audit Event |
|--------|----------|-------------|
| Create inmate | `POST /inmates` | `INMATE_CREATED` |
| Update inmate | `PUT /inmates/{id}` | `INMATE_UPDATED` |
| Delete inmate | `DELETE /inmates/{id}` | `INMATE_DELETED` |
| Enroll face | `POST /enrollment/{id}` | `FACE_ENROLLED` |
| Start roll call | `POST /rollcalls/{id}/start` | `ROLLCALL_STARTED` |
| Complete roll call | `POST /rollcalls/{id}/complete` | `ROLLCALL_COMPLETED` |
| Cancel roll call | `POST /rollcalls/{id}/cancel` | `ROLLCALL_CANCELLED` |
| Verify inmate | `POST /rollcalls/{id}/verification` | `VERIFICATION_RECORDED` |
| Manual override | `POST /rollcalls/{id}/verification` (manual) | `MANUAL_OVERRIDE_USED` ⚠️ |

---

## 🔍 View Audit Logs

### Option 1: Export to CSV
```bash
python scripts/export_audit.py --days 1 --output audit.csv
cat audit.csv
```

### Option 2: Direct query
```bash
sqlite3 prison_rollcall.db "SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT 10"
```

### Option 3: Filter by officer
```bash
sqlite3 prison_rollcall.db "SELECT action, entity_type FROM audit_log WHERE user_id='officer-demo'"
```

---

## 💡 Demo Tips

**Show these features:**
1. ✅ Every action has a `user_id` (from `X-Officer-ID` header)
2. ✅ Timestamps are automatic
3. ✅ IP addresses are captured
4. ✅ Details include what changed (e.g., which fields were updated)
5. ✅ Manual overrides are flagged separately

**Common demo scenario:**
"Officer Alice creates an inmate, enrolls their face, updates their cell assignment, runs a roll call with a manual override, then deletes a test record. Every action is logged with full details."

---

## 🎬 Full Demo Script

See: `AUDIT_DEMO_GUIDE.md` for a complete step-by-step guide.

Run: `./scripts/demo_audit_api.sh` for an automated demo.

---

## 🆘 Troubleshooting

**Server won't start?**
```bash
cd server
source .venv/bin/activate
uvicorn app.main:app --reload
```

**No audit table?**
```bash
# Run migrations
sqlite3 prison_rollcall.db < app/db/migrations/006_audit_enhancements.sql
```

**No entries in audit log?**
- Make sure you're including the `X-Officer-ID` header in requests
- Check that middleware is loaded: verify `RequestContextMiddleware` is in `app/main.py`

---

## 📊 Sample Output

```csv
timestamp,user_id,action,entity_type,entity_id,ip_address,details
2026-01-29T14:32:01,officer-demo,INMATE_CREATED,inmate,abc123...,192.168.1.100,"{""inmate_number"":""A12345""}"
2026-01-29T14:32:15,officer-demo,INMATE_UPDATED,inmate,abc123...,192.168.1.100,"{""updated_fields"":{""cell_block"":""B""}}"
2026-01-29T14:33:42,officer-demo,MANUAL_OVERRIDE_USED,verification,def456...,192.168.1.100,"{""reason"":""facial_injury""}"
```
