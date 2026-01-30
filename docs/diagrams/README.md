# Prison Roll Call - System Diagrams

This directory contains comprehensive Mermaid diagrams documenting the Prison Roll Call system.

## Diagrams Available

### 1. [Logical Features Diagram](./logical-features.md)

**Purpose:** Shows all the logical features and workflows of the system and how they interact.

**Contents:**
- Prisoner Management (enrollment workflow)
- Schedule Management (timetables and activities)
- Roll Call Generation (route planning)
- Active Roll Call Execution (verification workflow)
- Offline Queue Mode (network resilience)
- Audit & Reporting (compliance tracking)
- Location Management (hierarchy and pathfinding)

**Best For:**
- Understanding user workflows
- Training officers on system features
- Product demonstrations
- Business stakeholder presentations

---

### 2. [System Architecture Diagram](./system-architecture.md)

**Purpose:** Shows the technical architecture, components, and technology stack.

**Contents:**
- High-Level Architecture (client, API, services, ML, data)
- Detailed Component Architecture (file structure)
- Data Flow Architecture (sequence diagrams)
- Technology Stack (frontend, backend, ML, database)
- Deployment Architecture (network topology)

**Best For:**
- Developer onboarding
- Technical reviews
- System integration planning
- Security audits
- Infrastructure setup

---

## How to View These Diagrams

### Option 1: GitHub/GitLab (Recommended)
GitHub and GitLab both render Mermaid diagrams natively. Just view the `.md` files in your browser.

### Option 2: VS Code
Install the "Markdown Preview Mermaid Support" extension:
```bash
code --install-extension bierner.markdown-mermaid
```
Then open the `.md` files and use the preview pane.

### Option 3: Mermaid Live Editor
Copy the Mermaid code and paste into: https://mermaid.live/

### Option 4: Export to PNG/SVG
Using the Mermaid CLI:
```bash
npm install -g @mermaid-js/mermaid-cli
mmdc -i logical-features.md -o logical-features.png
mmdc -i system-architecture.md -o system-architecture.png
```

---

## Diagram Key

### Color Coding

**Logical Features Diagram:**
- 🔵 Blue (Enrollment): Prisoner registration and face enrollment
- 🟢 Green (Verification): Face verification and matching
- 🟠 Orange (Schedule): Schedule and timetable management
- 🟣 Purple (Roll Call): Roll call generation and management
- 🔴 Pink (Audit): Audit logging and reporting
- 🟢 Teal (Location): Location hierarchy and pathfinding
- 🟡 Yellow (Queue): Offline queue mode

**Architecture Diagram:**
- 🔵 Light Blue: Client layer (Web UI, Mobile)
- 🟣 Purple: API layer (FastAPI, routes)
- 🟢 Green: Service layer (business logic)
- 🟠 Orange: ML layer (DeepFace pipeline)
- 🔴 Pink: Data access layer (repositories)
- 🟢 Teal: Database layer (SQLite)
- 🟡 Yellow: Network layer (WiFi hotspot)

---

## Quick Reference

### System Components Count

**Web UI:**
- 11 pages
- 7 reusable components
- 2 services (API + Camera)
- 141 tests

**Server:**
- 28 API endpoints
- 9 route modules
- 7 service classes
- 8 repositories
- 3 ML pipeline components
- 6 database migrations
- 488 tests

**Database:**
- 9 tables
- 8 indexes
- AES-256 encryption (planned)

---

## Related Documentation

- [Design Document v3](../../prison-rollcall-design-document-v3.md) - Complete technical specification
- [Validation Report](../../VALIDATION_REPORT.md) - Implementation compliance audit
- [Test Fixes Summary](../../TEST_FIXES_SUMMARY.md) - Test suite fixes
- [Project TODO](../../PROJECT_TODO.md) - Development roadmap

---

## Contributing

When updating these diagrams:

1. **Maintain Consistency:** Use the same color scheme and styling
2. **Keep It Current:** Update diagrams when architecture changes
3. **Test Rendering:** Verify diagrams render correctly in GitHub
4. **Document Changes:** Update this README if adding new diagrams

---

**Last Updated:** January 30, 2026
**Diagram Format:** Mermaid v10+
**Status:** ✅ Current with implementation
