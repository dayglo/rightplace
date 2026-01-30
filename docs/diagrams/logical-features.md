# Prison Roll Call - Logical Features Diagram

This diagram shows all the logical features of the Prison Roll Call system and how they interact with each other.

```mermaid
graph TD
    %% Main Workflows
    subgraph "Prisoner Management"
        A1[Add Prisoner] --> A2[Prisoner Record Created]
        A2 --> A3{Has Face?}
        A3 -->|No| A4[Face Enrollment Workflow]
        A3 -->|Yes| A5[Prisoner Ready for Roll Call]
        A4 --> A6[Capture Face Photo]
        A6 --> A7[Face Detection]
        A7 --> A8{Quality Check}
        A8 -->|Pass| A9[Extract Embedding]
        A8 -->|Fail| A6
        A9 --> A10[Store Embedding in DB]
        A10 --> A5
    end

    subgraph "Schedule Management"
        S1[Import Prisoner Schedules] --> S2[Schedule Entries Stored]
        S2 --> S3[Daily Activity Timetable]
        S3 --> S4[Expected Locations by Time]
        S5[Create Schedule Entry] --> S2
        S6[Update Schedule] --> S2
    end

    subgraph "Roll Call Generation"
        R1[Select Locations] --> R2[Query Schedules]
        R2 --> R3[Identify Expected Prisoners]
        R3 --> R4[Calculate Optimal Route]
        R4 --> R5[Generate Walking Path]
        R5 --> R6[Estimate Time & Distance]
        R6 --> R7[Roll Call Route Created]
        R7 --> R8[Review & Approve]
        R8 --> R9[Start Roll Call]
    end

    subgraph "Active Roll Call Execution"
        R9 --> V1[Navigate to First Location]
        V1 --> V2[Camera Activates]
        V2 --> V3[Officer Scans Prisoner Face]
        V3 --> V4[Face Detection]
        V4 --> V5{Face Found?}
        V5 -->|No| V6[Retry or Manual Override]
        V5 -->|Yes| V7[Extract Embedding]
        V7 --> V8[Match Against Enrolled]
        V8 --> V9{Match Found?}
        V9 -->|No| V10[No Match - Manual Override]
        V9 -->|Yes| V11[Check Confidence Score]
        V11 --> V12{Score >= Threshold?}
        V12 -->|< 60%| V13[Manual Review Required]
        V12 -->|60-74%| V14[Low Confidence - Officer Confirms]
        V12 -->|75-91%| V15[Suggest Match - Officer Confirms]
        V12 -->|>= 92%| V16[Auto-Accept Match]

        V13 --> V17[Officer Decision]
        V14 --> V17
        V15 --> V17
        V16 --> V18[Record Verification]
        V17 --> V18
        V10 --> V18
        V6 --> V18

        V18 --> V19{Location Expected?}
        V19 -->|Yes| V20[Mark as Verified]
        V19 -->|No| V21[Flag Discrepancy]
        V20 --> V22[Log to Audit Trail]
        V21 --> V22
        V22 --> V23{More Prisoners at Location?}
        V23 -->|Yes| V3
        V23 -->|No| V24{More Locations?}
        V24 -->|Yes| V1
        V24 -->|No| V25[Complete Roll Call]
    end

    subgraph "Offline Queue Mode"
        Q1[Network Unavailable] --> Q2[Enter Queue Mode]
        Q2 --> Q3[Capture Photo Locally]
        Q3 --> Q4[Store in Local Queue]
        Q4 --> Q5[Continue Roll Call]
        Q5 --> Q6{Network Restored?}
        Q6 -->|No| Q3
        Q6 -->|Yes| Q7[Sync Queue to Server]
        Q7 --> Q8[Process Queued Photos]
        Q8 --> V7
    end

    subgraph "Audit & Reporting"
        V22 --> AU1[Audit Log Entry]
        V10 --> AU2[Manual Override Logged]
        V6 --> AU2
        AU1 --> AU3[Audit Database]
        AU2 --> AU3
        AU3 --> AU4[Generate Reports]
        AU4 --> AU5[Export to CSV]
        R9 --> AU6[Log Roll Call Start]
        V25 --> AU7[Log Roll Call Complete]
        AU6 --> AU3
        AU7 --> AU3
    end

    subgraph "Location Management"
        L1[Create Location] --> L2[Location Hierarchy]
        L2 --> L3[Houseblock]
        L3 --> L4[Wing]
        L4 --> L5[Landing]
        L5 --> L6[Cell]
        L7[Define Connections] --> L8[Location Graph]
        L8 --> R4
        L2 --> R1
    end

    subgraph "Pathfinding Service"
        R4 --> P1[Collect All Child Cells]
        P1 --> P2[Build Location Graph]
        P2 --> P3[Calculate Distances]
        P3 --> P4[Optimize Route Order]
        P4 --> P5[Minimize Walking Time]
        P5 --> R5
    end

    %% Interconnections
    A5 --> S3
    S4 --> R3
    V25 --> AU4
    L2 --> S2

    %% Styling
    classDef enrollment fill:#e1f5ff,stroke:#0288d1,stroke-width:2px
    classDef verification fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
    classDef schedule fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef rollcall fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef audit fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    classDef location fill:#e0f2f1,stroke:#00796b,stroke-width:2px
    classDef queue fill:#fff9c4,stroke:#f9a825,stroke-width:2px

    class A1,A2,A3,A4,A5,A6,A7,A8,A9,A10 enrollment
    class V1,V2,V3,V4,V5,V6,V7,V8,V9,V10,V11,V12,V13,V14,V15,V16,V17,V18,V19,V20,V21,V22,V23,V24,V25 verification
    class S1,S2,S3,S4,S5,S6 schedule
    class R1,R2,R3,R4,R5,R6,R7,R8,R9 rollcall
    class AU1,AU2,AU3,AU4,AU5,AU6,AU7 audit
    class L1,L2,L3,L4,L5,L6,L7,L8 location
    class Q1,Q2,Q3,Q4,Q5,Q6,Q7,Q8 queue
    class P1,P2,P3,P4,P5 location
```

## Feature Interactions Summary

### Core Workflows

1. **Prisoner Enrollment**
   - Add prisoner → Capture face → Detect face → Quality check → Extract embedding → Store
   - Prerequisites: Good lighting, single face, no obstructions
   - Output: 512-dimensional face embedding in database

2. **Schedule Management**
   - Import/create schedules → Store activity timetables → Query expected locations
   - Supports: Recurring activities, one-off appointments, multiple activity types
   - Output: Expected prisoner locations by time

3. **Roll Call Generation**
   - Select locations → Query schedules → Calculate route → Generate walking path
   - Features: Multi-location support, optimal routing, time estimation
   - Output: Ordered route with expected prisoners at each stop

4. **Active Roll Call Execution**
   - Navigate route → Scan faces → Verify identity → Record results
   - Confidence thresholds: <60% (manual), 60-74% (review), 75-91% (confirm), ≥92% (auto-accept)
   - Output: Verification records with confidence scores

5. **Offline Queue Mode**
   - Network lost → Queue photos locally → Sync when restored
   - Limits: 50 photos, 500MB storage, 4-hour expiry
   - Output: Queued verifications processed on reconnection

6. **Audit & Reporting**
   - Log all actions → Track manual overrides → Generate reports
   - Captures: Who, what, when, where, why
   - Output: Tamper-proof audit trail, CSV exports

### Key Decision Points

- **Quality Check (A8):** Rejects poor quality images (blur, low light, occlusion)
- **Match Found (V9):** Determines if face matches enrolled prisoner
- **Confidence Threshold (V12):** Decides level of officer involvement
- **Location Expected (V19):** Flags prisoners in wrong locations
- **Network Status (Q6):** Switches between online and offline modes

### Integration Points

- **Schedules → Roll Call Generation:** Expected locations inform route planning
- **Enrollment → Verification:** Stored embeddings enable face matching
- **Location Hierarchy → Pathfinding:** Graph structure enables route optimization
- **Verifications → Audit:** All actions logged for compliance
- **Queue → Verification:** Offline photos processed same as live scans
