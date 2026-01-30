# Prison Roll Call - System Architecture Diagram

This diagram shows the technical architecture of the Prison Roll Call system.

## High-Level Architecture

```mermaid
graph TB
    %% Clients
    subgraph "Client Layer"
        WEB[Web UI<br/>SvelteKit]
        MOB[Mobile App<br/>React Native<br/>FUTURE]
    end

    %% API Gateway
    subgraph "API Layer"
        API[FastAPI Server<br/>Port 8000]
        CORS[CORS Middleware]
        CTX[Request Context<br/>Middleware]

        API --> CORS
        CORS --> CTX
    end

    %% Routes
    subgraph "API Routes"
        R_HEALTH[/health]
        R_INMATES[/inmates]
        R_LOCATIONS[/locations]
        R_ENROLL[/enrollment]
        R_VERIFY[/verify]
        R_ROLLCALL[/rollcalls]
        R_SCHEDULE[/schedules]
        R_SYNC[/sync]
        R_VERIF[/verifications]
    end

    %% Services Layer
    subgraph "Business Logic Layer"
        S_FACE[Face Recognition<br/>Service]
        S_ROLLCALL[Roll Call<br/>Service]
        S_SCHEDULE[Schedule<br/>Service]
        S_SYNC[Sync<br/>Service]
        S_AUDIT[Audit<br/>Service]
        S_PATH[Pathfinding<br/>Service]
        S_GEN[Roll Call Generator<br/>Service]
    end

    %% ML Layer
    subgraph "Machine Learning Pipeline"
        ML_DETECT[Face Detector<br/>RetinaFace]
        ML_EMBED[Face Embedder<br/>Facenet512/ArcFace]
        ML_MATCH[Face Matcher<br/>Cosine Similarity]
        ML_DEEP[DeepFace Library<br/>GPU Accelerated]

        ML_DETECT --> ML_DEEP
        ML_EMBED --> ML_DEEP
        ML_MATCH --> ML_EMBED
    end

    %% Repository Layer
    subgraph "Data Access Layer"
        REPO_INM[Inmate<br/>Repository]
        REPO_LOC[Location<br/>Repository]
        REPO_EMB[Embedding<br/>Repository]
        REPO_ROLL[Roll Call<br/>Repository]
        REPO_VER[Verification<br/>Repository]
        REPO_SCHED[Schedule<br/>Repository]
        REPO_AUD[Audit<br/>Repository]
        REPO_CONN[Connection<br/>Repository]
    end

    %% Database
    subgraph "Data Storage"
        DB[(SQLite Database<br/>AES-256 Encrypted)]

        subgraph "Tables"
            T_INMATES[inmates]
            T_EMBEDDINGS[embeddings<br/>512-dim BLOB]
            T_LOCATIONS[locations]
            T_ROLLCALLS[roll_calls<br/>route JSON]
            T_VERIFS[verifications]
            T_SCHEDULES[schedule_entries]
            T_AUDIT[audit_log]
            T_CONNS[location_connections<br/>graph JSON]
            T_POLICY[policy]
        end
    end

    %% Network
    subgraph "Network Layer"
        WIFI[WiFi Hotspot<br/>192.168.x.1<br/>No Internet]
    end

    %% Connections - Client to API
    WEB -->|HTTP/REST| WIFI
    MOB -.->|HTTP/REST| WIFI
    WIFI --> API

    %% Connections - API to Routes
    CTX --> R_HEALTH
    CTX --> R_INMATES
    CTX --> R_LOCATIONS
    CTX --> R_ENROLL
    CTX --> R_VERIFY
    CTX --> R_ROLLCALL
    CTX --> R_SCHEDULE
    CTX --> R_SYNC
    CTX --> R_VERIF

    %% Connections - Routes to Services
    R_HEALTH --> S_FACE
    R_INMATES --> REPO_INM
    R_LOCATIONS --> REPO_LOC
    R_ENROLL --> S_FACE
    R_VERIFY --> S_FACE
    R_ROLLCALL --> S_ROLLCALL
    R_ROLLCALL --> S_GEN
    R_SCHEDULE --> S_SCHEDULE
    R_SYNC --> S_SYNC
    R_VERIF --> REPO_VER

    %% Connections - Services to ML/Repos
    S_FACE --> ML_DETECT
    S_FACE --> ML_EMBED
    S_FACE --> ML_MATCH
    S_FACE --> REPO_EMB
    S_ROLLCALL --> REPO_ROLL
    S_ROLLCALL --> REPO_VER
    S_SCHEDULE --> REPO_SCHED
    S_SYNC --> S_FACE
    S_SYNC --> REPO_VER
    S_GEN --> S_SCHEDULE
    S_GEN --> S_PATH
    S_PATH --> REPO_CONN

    %% Connections - All actions go through audit
    R_INMATES --> S_AUDIT
    R_ENROLL --> S_AUDIT
    R_ROLLCALL --> S_AUDIT
    S_AUDIT --> REPO_AUD

    %% Connections - Repos to DB
    REPO_INM --> T_INMATES
    REPO_LOC --> T_LOCATIONS
    REPO_EMB --> T_EMBEDDINGS
    REPO_ROLL --> T_ROLLCALLS
    REPO_VER --> T_VERIFS
    REPO_SCHED --> T_SCHEDULES
    REPO_AUD --> T_AUDIT
    REPO_CONN --> T_CONNS

    %% Styling
    classDef client fill:#e3f2fd,stroke:#1976d2,stroke-width:3px
    classDef api fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef service fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
    classDef ml fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef repo fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    classDef db fill:#e0f2f1,stroke:#00796b,stroke-width:3px
    classDef network fill:#fff9c4,stroke:#f9a825,stroke-width:2px

    class WEB,MOB client
    class API,CORS,CTX,R_HEALTH,R_INMATES,R_LOCATIONS,R_ENROLL,R_VERIFY,R_ROLLCALL,R_SCHEDULE,R_SYNC,R_VERIF api
    class S_FACE,S_ROLLCALL,S_SCHEDULE,S_SYNC,S_AUDIT,S_PATH,S_GEN service
    class ML_DETECT,ML_EMBED,ML_MATCH,ML_DEEP ml
    class REPO_INM,REPO_LOC,REPO_EMB,REPO_ROLL,REPO_VER,REPO_SCHED,REPO_AUD,REPO_CONN repo
    class DB,T_INMATES,T_EMBEDDINGS,T_LOCATIONS,T_ROLLCALLS,T_VERIFS,T_SCHEDULES,T_AUDIT,T_CONNS,T_POLICY db
    class WIFI network
```

## Detailed Component Architecture

```mermaid
graph LR
    %% Component Detail
    subgraph "Web UI Components"
        direction TB
        WEB_PAGES[Pages<br/>11 Routes]
        WEB_COMP[Components<br/>7 Reusable]
        WEB_SVC[Services<br/>API + Camera]
        WEB_STORE[Stores<br/>Svelte State]

        WEB_PAGES --> WEB_COMP
        WEB_PAGES --> WEB_SVC
        WEB_SVC --> WEB_STORE
    end

    subgraph "Server Application Structure"
        direction TB

        subgraph "app/api/"
            API_ROUTES[9 Route Modules]
            API_MW[2 Middleware]
        end

        subgraph "app/services/"
            SVC_FACE[face_recognition.py]
            SVC_ROLL[rollcall_service.py]
            SVC_SCHED[schedule_service.py]
            SVC_SYNC[sync_service.py]
            SVC_AUD[audit_service.py]
            SVC_PATH[pathfinding_service.py]
            SVC_GEN[rollcall_generator_service.py]
        end

        subgraph "app/ml/"
            ML_DET[face_detector.py]
            ML_EMB[face_embedder.py]
            ML_MAT[face_matcher.py]
        end

        subgraph "app/db/"
            DB_REPOS[8 Repositories]
            DB_MIG[6 Migrations]
        end

        subgraph "app/models/"
            MOD_PYD[9 Pydantic Models]
        end

        API_ROUTES --> SVC_FACE
        API_ROUTES --> SVC_ROLL
        API_ROUTES --> SVC_SCHED
        SVC_FACE --> ML_DET
        SVC_FACE --> ML_EMB
        SVC_FACE --> ML_MAT
        SVC_ROLL --> DB_REPOS
        SVC_SCHED --> DB_REPOS
        API_MW --> SVC_AUD
    end

    %% Connections
    WEB_SVC -->|REST API| API_ROUTES

    classDef webui fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef server fill:#e8f5e9,stroke:#388e3c,stroke-width:2px

    class WEB_PAGES,WEB_COMP,WEB_SVC,WEB_STORE webui
    class API_ROUTES,API_MW,SVC_FACE,SVC_ROLL,SVC_SCHED,SVC_SYNC,SVC_AUD,SVC_PATH,SVC_GEN,ML_DET,ML_EMB,ML_MAT,DB_REPOS,DB_MIG,MOD_PYD server
```

## Data Flow Architecture

```mermaid
sequenceDiagram
    participant Officer as Officer<br/>(Web UI)
    participant API as FastAPI<br/>Server
    participant Service as Business<br/>Service
    participant ML as ML<br/>Pipeline
    participant Repo as Repository
    participant DB as SQLite<br/>Database
    participant Audit as Audit<br/>Service

    Note over Officer,DB: Face Enrollment Flow

    Officer->>API: POST /enrollment/{id}<br/>+ face photo
    API->>Service: enrollFace(id, photo)
    Service->>ML: detectFace(photo)
    ML-->>Service: BoundingBox + Quality

    alt Quality >= Threshold
        Service->>ML: extractEmbedding(photo)
        ML-->>Service: 512-dim vector
        Service->>Repo: saveEmbedding(id, vector)
        Repo->>DB: INSERT embeddings
        DB-->>Repo: Success
        Repo-->>Service: Success
        Service->>Audit: log(FACE_ENROLLED)
        Audit->>DB: INSERT audit_log
        Service-->>API: {success: true, quality: 0.89}
        API-->>Officer: 200 OK
    else Quality < Threshold
        Service-->>API: {success: false, quality: 0.45}
        API-->>Officer: 400 Bad Request
    end

    Note over Officer,DB: Face Verification Flow

    Officer->>API: POST /verify/quick<br/>+ face photo + location
    API->>Service: verifyFace(photo, location)
    Service->>ML: detectFace(photo)
    ML-->>Service: Face detected
    Service->>ML: extractEmbedding(photo)
    ML-->>Service: Query vector
    Service->>Repo: getAllEmbeddings()
    Repo->>DB: SELECT * FROM embeddings
    DB-->>Repo: All embeddings
    Repo-->>Service: Embedding dictionary
    Service->>ML: findMatch(query, embeddings)
    ML-->>Service: {matched: true, id: "abc", conf: 0.89}
    Service->>Repo: getInmate(id)
    Repo->>DB: SELECT FROM inmates
    DB-->>Repo: Inmate record
    Repo-->>Service: Inmate
    Service-->>API: MatchResult
    API-->>Officer: 200 OK + match details

    Note over Officer,DB: Roll Call Generation Flow

    Officer->>API: POST /rollcalls/generate<br/>+ location_ids + time
    API->>Service: generateRollCall(params)
    Service->>Repo: getLocations(ids)
    Repo->>DB: SELECT locations
    DB-->>Repo: Location hierarchy
    Repo-->>Service: Locations
    Service->>Service: collectChildCells()
    Service->>Repo: getSchedules(time)
    Repo->>DB: SELECT schedules<br/>WHERE time overlaps
    DB-->>Repo: Expected activities
    Repo-->>Service: Schedule entries
    Service->>Service: calculateRoute()
    Service->>Repo: getConnections()
    Repo->>DB: SELECT location_connections
    DB-->>Repo: Location graph
    Repo-->>Service: Graph
    Service->>Service: optimizeRoute()
    Service-->>API: GeneratedRoute
    API-->>Officer: 200 OK + route details
```

## Technology Stack

```mermaid
graph TB
    subgraph "Frontend"
        FE1[SvelteKit 2.x]
        FE2[Tailwind CSS]
        FE3[TypeScript]
        FE4[Vitest + Testing Library]
        FE5[Vite 7.x]
    end

    subgraph "Backend"
        BE1[Python 3.11+]
        BE2[FastAPI + Uvicorn]
        BE3[Pydantic v2]
        BE4[SQLAlchemy Core]
        BE5[Pytest]
    end

    subgraph "Machine Learning"
        ML1[DeepFace 0.0.93+]
        ML2[TensorFlow/Keras]
        ML3[RetinaFace Detector]
        ML4[Facenet512 Model]
        ML5[NumPy + OpenCV]
    end

    subgraph "Database"
        DB1[SQLite 3.x]
        DB2[AES-256 Encryption]
        DB3[6 Migrations]
    end

    subgraph "Infrastructure"
        INF1[Linux Server]
        INF2[WiFi Hotspot<br/>No Internet]
        INF3[GPU Optional<br/>RTX 3060+]
    end

    FE1 --> BE2
    BE2 --> ML1
    ML1 --> ML2
    BE4 --> DB1
    ML2 -.->|Optional| INF3
    BE2 --> INF1
    FE5 --> INF1
    INF2 --> INF1

    classDef frontend fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef backend fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
    classDef ml fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef database fill:#e0f2f1,stroke:#00796b,stroke-width:2px
    classDef infra fill:#fce4ec,stroke:#c2185b,stroke-width:2px

    class FE1,FE2,FE3,FE4,FE5 frontend
    class BE1,BE2,BE3,BE4,BE5 backend
    class ML1,ML2,ML3,ML4,ML5 ml
    class DB1,DB2,DB3 database
    class INF1,INF2,INF3 infra
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Prison Facility - Closed Network"

        subgraph "Laptop Server (Brain)"
            SRV[FastAPI Application<br/>Port 8000]
            DB[(SQLite Database<br/>Encrypted)]
            ML[ML Models<br/>GPU Accelerated]
            WIFI[WiFi Hotspot<br/>192.168.4.1]

            SRV --> DB
            SRV --> ML
            SRV --> WIFI
        end

        subgraph "Officer Devices"
            WEB1[Web Browser<br/>Chrome/Edge]
            WEB2[Web Browser<br/>Chrome/Edge]
            MOB1[Mobile Device<br/>FUTURE]

            WEB1 -.->|WiFi| WIFI
            WEB2 -.->|WiFi| WIFI
            MOB1 -.->|WiFi| WIFI
        end
    end

    subgraph "Security Boundary"
        FENCE[No Internet Connection<br/>Air-Gapped Network<br/>AES-256 Encryption]
    end

    WIFI ---|X| FENCE

    classDef server fill:#e8f5e9,stroke:#388e3c,stroke-width:3px
    classDef client fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef security fill:#ffebee,stroke:#c62828,stroke-width:3px

    class SRV,DB,ML,WIFI server
    class WEB1,WEB2,MOB1 client
    class FENCE security
```

## Architecture Characteristics

### Performance Targets

| Component | Target | Hardware |
|-----------|--------|----------|
| Face Detection | <30ms | GPU |
| Embedding Extraction | <50ms | GPU |
| 1:N Matching (1000) | <20ms | CPU |
| Full Pipeline | <100ms | GPU |
| API Response | <50ms | CPU |

### Scalability

- **Prisoners:** Supports 1,000-5,000 inmates per facility
- **Concurrent Users:** 5-10 officers simultaneously
- **Roll Call Size:** Up to 500 locations per route
- **Embeddings:** Efficient cosine similarity for 1:N matching

### Reliability

- **Offline Mode:** Queue up to 50 photos, 500MB, 4-hour expiry
- **Failover:** Manual override for all verification scenarios
- **Audit Trail:** Tamper-proof logging of all actions
- **Data Integrity:** Foreign key constraints, transactions

### Security

- **Network:** Closed WiFi hotspot, no internet
- **Encryption:** AES-256 at rest (planned)
- **Authentication:** API key per shift (planned)
- **Audit:** Comprehensive logging with context
- **Data Privacy:** Embeddings are one-way transformation
