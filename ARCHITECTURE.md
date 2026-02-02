# FRAS Backend Architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                          │
│  (Frontend, Mobile App, API Consumers)                       │
└──────────────────┬──────────────────────────────────────────┘
                   │ HTTP/HTTPS
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                    API Gateway (FastAPI)                     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  CORS Middleware                                        │ │
│  │  Authentication Middleware (JWT)                        │ │
│  │  Logging Middleware                                     │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────┬──────────────────────────────────────────┘
                   │
    ┌──────────────┴──────────────┬──────────────────┐
    │                             │                  │
┌───▼────────┐         ┌──────────▼──────┐    ┌────▼─────────┐
│   Auth     │         │     Fleet       │    │    File      │
│  Routes    │         │    Routes       │    │   Routes     │
│            │         │                 │    │              │
│ - Login    │         │ - Create        │    │ - Upload     │
│ - Token    │         │ - Read          │    │ - Process    │
│            │         │ - Delete        │    │ - Export     │
└───┬────────┘         └──────────┬──────┘    └────┬─────────┘
    │                             │                 │
    │         ┌───────────────────┴─────────────────┘
    │         │
┌───▼─────────▼────────────────────────────────────────────────┐
│                   Business Logic Layer                        │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐   │
│  │   Auth      │  │    CRUD      │  │    Utils          │   │
│  │  Module     │  │  Operations  │  │  - File parser    │   │
│  │             │  │              │  │  - Excel export   │   │
│  │ - Hash pwd  │  │ - Create     │  │  - Validation     │   │
│  │ - Verify    │  │ - Read       │  │                   │   │
│  │ - JWT ops   │  │ - Update     │  │                   │   │
│  │ - Auth user │  │ - Delete     │  │                   │   │
│  └─────────────┘  └──────────────┘  └───────────────────┘   │
└───────────────────────────┬──────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────┐
│                   Data Access Layer                           │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │            Database Session Management                   │ │
│  │         (Connection Pooling, Transaction Mgmt)           │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌──────────────┐                    ┌──────────────────┐   │
│  │    Models    │                    │    Schemas       │   │
│  │              │                    │                  │   │
│  │ - User       │◄──────────────────►│ - UserCreate    │   │
│  │ - FleetRec   │   ORM ◄─► Pydantic│ - FleetRecordOut │   │
│  └──────────────┘                    └──────────────────┘   │
└───────────────────────────┬──────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────┐
│                    Database Layer                             │
│                    PostgreSQL                                 │
│  ┌─────────────────┐        ┌──────────────────────┐         │
│  │  users table    │        │  fleet_records table │         │
│  │  - id           │        │  - id                │         │
│  │  - username     │        │  - date              │         │
│  │  - hashed_pwd   │        │  - fleet             │         │
│  │  - role         │        │  - amount            │         │
│  └─────────────────┘        └──────────────────────┘         │
└───────────────────────────────────────────────────────────────┘


## Request Flow Example

### Authentication Flow
```
1. Client sends credentials (POST /auth/token)
   ↓
2. Auth Routes receives request
   ↓
3. Auth Module validates credentials
   ↓
4. Database queries User table
   ↓
5. Password verification (bcrypt)
   ↓
6. JWT token generation
   ↓
7. Token returned to client
```

### Protected Endpoint Flow
```
1. Client sends request with JWT token
   ↓
2. FastAPI extracts token from header
   ↓
3. Auth dependency validates token
   ↓
4. JWT decoded and verified
   ↓
5. User fetched from database
   ↓
6. Authorization check (role-based)
   ↓
7. Route handler executed
   ↓
8. Response returned to client
```

### File Upload Flow
```
1. Client uploads CSV/Excel (POST /files/upload-summary)
   ↓
2. Admin authentication check
   ↓
3. File validation (type, size)
   ↓
4. Parse file content (Pandas)
   ↓
5. Data validation and cleaning
   ↓
6. Create FleetRecord instances
   ↓
7. Batch insert to database
   ↓
8. Generate Excel summary
   ↓
9. Return summary file to client
```

## Component Dependencies

```
main.py
├── app/config.py (Settings)
├── app/database.py (DB Connection)
└── app/routers/
    ├── auth_routes.py
    │   ├── app/auth.py
    │   ├── app/database.py
    │   └── app/schemas.py
    ├── fleet_routes.py
    │   ├── app/auth.py (get_current_user)
    │   ├── app/dependencies.py (admin_required)
    │   ├── app/crud.py
    │   └── app/schemas.py
    └── file_routes.py
        ├── app/dependencies.py (admin_required)
        ├── app/models.py
        ├── app/utils.py
        └── app/database.py
```

## Configuration Management

```
Environment (.env)
       ↓
   config.py (Pydantic Settings)
       ↓
   ┌──────┴──────┬──────────┬──────────┐
   ↓             ↓          ↓          ↓
database.py   auth.py   main.py   [other modules]
```

## Security Layers

```
┌─────────────────────────────────────────────┐
│ Layer 1: CORS Protection                    │
│  - Origin validation                        │
│  - Methods/Headers control                  │
└─────────────┬───────────────────────────────┘
              ↓
┌─────────────┴───────────────────────────────┐
│ Layer 2: Authentication (JWT)               │
│  - Token validation                         │
│  - Expiration check                         │
│  - User identification                      │
└─────────────┬───────────────────────────────┘
              ↓
┌─────────────┴───────────────────────────────┐
│ Layer 3: Authorization                      │
│  - Role-based access (admin/user)           │
│  - Endpoint-level permissions               │
└─────────────┬───────────────────────────────┘
              ↓
┌─────────────┴───────────────────────────────┐
│ Layer 4: Input Validation                   │
│  - Pydantic schema validation               │
│  - Type checking                            │
│  - Field constraints                        │
└─────────────┬───────────────────────────────┘
              ↓
┌─────────────┴───────────────────────────────┐
│ Layer 5: Business Logic                     │
│  - Custom validation rules                  │
│  - Data sanitization                        │
│  - Error handling                           │
└─────────────────────────────────────────────┘
```

## Key Design Patterns

### 1. Dependency Injection
- Database sessions via `Depends(get_db)`
- User authentication via `Depends(get_current_user)`
- Admin authorization via `Depends(admin_required)`

### 2. Repository Pattern
- CRUD operations centralized in `crud.py`
- Separation of data access from business logic

### 3. Settings Pattern
- Centralized configuration in `config.py`
- Environment-based settings
- Cached settings with `@lru_cache()`

### 4. Middleware Pattern
- CORS middleware
- Authentication middleware
- Logging middleware

### 5. Schema Validation
- Pydantic models for request/response validation
- Type safety throughout the application

## Technology Stack

```
┌─────────────────────────────────────────────┐
│            Application Layer                │
│              FastAPI 0.100+                 │
└─────────────┬───────────────────────────────┘
              │
┌─────────────▼───────────────────────────────┐
│           ORM & Validation                  │
│  SQLAlchemy 2.0    │    Pydantic 2.0        │
└─────────────┬───────────────────────────────┘
              │
┌─────────────▼───────────────────────────────┐
│            Database Driver                  │
│           psycopg2-binary                   │
└─────────────┬───────────────────────────────┘
              │
┌─────────────▼───────────────────────────────┐
│            Database                         │
│           PostgreSQL 12+                    │
└─────────────────────────────────────────────┘

Additional Libraries:
- python-jose: JWT handling
- passlib[bcrypt]: Password hashing
- pandas: Data processing
- openpyxl: Excel generation
```

## Scalability Considerations

### Horizontal Scaling
- Stateless application design
- JWT tokens (no server-side sessions)
- Database connection pooling
- Can deploy multiple instances behind load balancer

### Performance Optimization
- Connection pooling (5 connections, 10 max overflow)
- Lazy loading of settings
- Efficient database queries
- Batch operations for file uploads

### Future Enhancements
- Redis for caching frequently accessed data
- Message queue for async file processing
- CDN for static assets
- Database read replicas
- Microservices architecture (if needed)
